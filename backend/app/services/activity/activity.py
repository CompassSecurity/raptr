import uuid

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.enums.enums import AclRole, ActivityAssetRole
from app.models.activity import Activity, activity_asset_association
from app.models.activity_evaluation import ActivityEvaluation
from app.models.activity_evaluation_dynamic_questions import (
    ActivityEvaluationDynamicQuestions,
)
from app.models.activity_group import ActivityGroup
from app.models.evaluation_template import EvaluationTemplate
from app.models.user import User
from app.schemas.activity import (
    ActivityBase,
    ActivityFilter,
    ActivityRead,
    ActivityUpdate,
    ActivityUpdateBlue,
)
from app.schemas.activity_evaluation_dynamic_questions import (
    DynamicEvaluationQuestionAssign,
)
from app.schemas.general import PaginatedResponse
from app.services.activity_history.activity_history import save_activity_shadow_copy
from app.services.utils.evaluation import (
    calculate_evaluations,
    create_activity_evaluation,
)
from app.services.utils.position import calculate_new_activity_position
from app.services.utils.query import paginated_query


def get_all_activities_service(
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
    filter_query: ActivityFilter,
) -> PaginatedResponse[ActivityRead]:
    """
    Get all activities. Searchable by activity name and related fields.
    """
    statement = (
        select(Activity)
        .filter(Activity.assessment_id == assessment_id)
        .outerjoin(ActivityGroup, Activity.activity_group_id == ActivityGroup.id)
        .outerjoin(ActivityEvaluation, Activity.id == ActivityEvaluation.activity_id)
    )

    if user.assessment_acl_role != AclRole.RED:
        statement = (
            statement.filter(Activity.visible.is_(True))
            .where(Activity.deleted.is_(False))
            .where(ActivityGroup.visible.is_(True))
            .where(ActivityGroup.deleted.is_(False))
        )

    # M2M Relationship Filters
    exclude_filters = set()

    if filter_query.tags:
        # We need to filter by any of the provided tags
        from app.models.tag import Tag

        statement = statement.where(Activity.tags.any(Tag.id.in_(filter_query.tags)))
        exclude_filters.add("tags")

    # For sorting by tags (which is a many-to-many relationship), we need to handle it properly.
    # Group_concat/string_agg approach for tags sorting
    from app.models.activity import activity_tag_association
    from app.models.tag import Tag

    sort_mapper = {
        "activity_group.name": ActivityGroup.name,
        "activity_coverage_score": ActivityEvaluation.activity_coverage_score,
    }

    if filter_query.sort_by == "tags":
        # Create a scalar subquery that aggregates tag names for each activity
        tags_agg_subquery = (
            select(func.string_agg(Tag.name, ", ").label("tag_names"))
            .join(activity_tag_association, Tag.id == activity_tag_association.c.tag_id)
            .where(activity_tag_association.c.activity_id == Activity.id)
            .correlate(Activity)
            .scalar_subquery()
        )
        # Using a literal column name effectively makes the sort_mapper apply sorting to the aliased aggregate
        sort_mapper["tags"] = tags_agg_subquery

    if filter_query.sort_by == "activity_position":
        sort_mapper["activity_position"] = [
            ActivityGroup.activity_group_position,
            Activity.activity_position,
        ]

    filter_mapper = {
        "activity_group_id": Activity.activity_group_id,
    }

    return paginated_query(
        session,
        Activity,
        filter_query,
        base_statement=statement,
        filter_mapper=filter_mapper,
        sort_mapper=sort_mapper,
        exclude_filters=exclude_filters,
    )


def get_activity_by_id_service(
    activity_id: uuid.UUID, assessment_id: uuid.UUID, user: User, session: Session
) -> Activity:
    """
    Get a activity by ID.
    """
    statement = select(Activity).where(
        Activity.id == activity_id,
        Activity.assessment_id == assessment_id,
    )

    if user.assessment_acl_role != AclRole.RED:
        statement = (
            statement.join(Activity.activity_group)
            .filter(Activity.visible.is_(True))
            .where(Activity.deleted.is_(False))
            .where(ActivityGroup.visible.is_(True))
            .where(ActivityGroup.deleted.is_(False))
        )

    activity = session.execute(statement).scalars().unique().one_or_none()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    return activity


def create_activity_service(
    activity: ActivityBase, assessment_id: uuid.UUID, user: User, session: Session
) -> Activity:
    """
    Create a new activity.
    """
    from app.services.activity_group.activity_group import get_or_create_default_group

    default_group = get_or_create_default_group(
        assessment_id, session, created_by=user.id
    )
    new_position = calculate_new_activity_position(session, default_group.id)

    activity_db = Activity(
        assessment_id=assessment_id,
        name=activity.name,
        mitre_tactic=activity.mitre_tactic,
        mitre_technique=activity.mitre_technique,
        activity_group_id=default_group.id,
        activity_position=new_position,
        created_by=user.id,
    )

    session.add(activity_db)
    session.flush()

    # Create evaluation with default dynamic questions from assessment
    create_activity_evaluation(activity_db.id, assessment_id, session)

    # Save a shadow copy
    save_activity_shadow_copy(activity_db, session)

    session.commit()
    return activity_db


def _apply_blue_team_restrictions(
    activity: ActivityUpdate, user: User
) -> ActivityUpdate | ActivityUpdateBlue:
    """Filter update fields through Blue schema if user is Blue team."""
    if user.assessment_acl_role != AclRole.BLUE:
        return activity
    try:
        return ActivityUpdateBlue(**activity.model_dump())
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e.errors()
        )


def _handle_activity_group_change(
    activity_db: Activity,
    update_data: dict,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """Move activity between groups, closing position gaps in the old group."""
    from app.services.activity_group.activity_group import (
        get_activity_group_by_id_service,
    )

    new_group_id = update_data["activity_group_id"]
    old_group_id = activity_db.activity_group_id
    old_position = activity_db.activity_position

    # Validate group exists
    if new_group_id:
        get_activity_group_by_id_service(new_group_id, assessment_id, user, session)

    # No change — nothing to do
    if old_group_id == new_group_id:
        return

    # A. Remove from old group (close the gap)
    if old_group_id is not None:
        subsequent_activities = (
            session.execute(
                select(Activity).where(
                    Activity.activity_group_id == old_group_id,
                    Activity.activity_position > old_position,
                    Activity.deleted.is_(False),
                )
            )
            .scalars()
            .unique()
            .all()
        )
        for act in subsequent_activities:
            act.activity_position -= 1
            session.add(act)

    # B. Add to new group (append)
    if new_group_id is not None:
        activity_db.activity_position = calculate_new_activity_position(
            session, new_group_id
        )
    else:
        # No target group specified — move to default group
        from app.services.activity_group.activity_group import (
            get_or_create_default_group,
        )

        default_group = get_or_create_default_group(
            assessment_id, session, created_by=user.id
        )
        update_data["activity_group_id"] = default_group.id
        activity_db.activity_position = calculate_new_activity_position(
            session, default_group.id
        )


def _update_evaluation(
    activity_db: Activity, evaluation_data: dict, session: Session
) -> None:
    """Create or update the activity evaluation and its dynamic questions."""
    dynamic_questions_data = evaluation_data.pop("dynamic_questions", None)

    if not activity_db.evaluation:
        clean_eval_data = {k: v for k, v in evaluation_data.items() if v is not None}
        evaluation_obj = ActivityEvaluation(
            activity_id=activity_db.id, **clean_eval_data
        )
        session.add(evaluation_obj)
    else:
        evaluation_obj = activity_db.evaluation
        for field, value in evaluation_data.items():
            if value is not None:
                setattr(evaluation_obj, field, value)

    # Update existing dynamic questions (new questions are NOT created here)
    if dynamic_questions_data is not None:
        existing_questions_map = {
            q.evaluation_template_id: q for q in evaluation_obj.dynamic_questions
        }
        for q_data in dynamic_questions_data:
            template_id = q_data.get("evaluation_template_id")
            if template_id in existing_questions_map:
                existing_q = existing_questions_map[template_id]
                for k, v in q_data.items():
                    if k != "evaluation_template_id" and v is not None:
                        setattr(existing_q, k, v)


def _update_tags(
    activity_db: Activity,
    tag_ids: list[uuid.UUID],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """Replace the activity's tag associations."""
    from app.services.tag.tag import get_tags_by_ids_service

    if tag_ids:
        activity_db.tags = get_tags_by_ids_service(
            tag_ids, assessment_id, user, session
        )
    else:
        activity_db.tags = []


def _update_asset_associations(
    activity_db: Activity,
    update_data: dict,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> None:
    """Extract asset role fields from update_data and replace associations."""
    from app.services.asset.asset import get_assets_by_ids_service

    asset_roles = [
        (ActivityAssetRole.SOURCE, "sources"),
        (ActivityAssetRole.TARGET, "targets"),
        (ActivityAssetRole.TOOL, "tools"),
        (ActivityAssetRole.PREVENTION_SOURCE, "prevention_sources"),
        (ActivityAssetRole.ALERT_SOURCE, "alert_sources"),
        (ActivityAssetRole.LOG_SOURCE, "log_sources"),
        (
            ActivityAssetRole.STAKEHOLDER_NOTIFICATION_SOURCE,
            "stakeholder_notification_sources",
        ),
    ]

    for role, field_name in asset_roles:
        if field_name not in update_data:
            continue
        asset_ids = update_data.pop(field_name)

        # Clear current associations for this role
        session.execute(
            activity_asset_association.delete().where(
                activity_asset_association.c.activity_id == activity_db.id,
                activity_asset_association.c.role == role.value,
            )
        )

        # Insert new associations
        if asset_ids:
            get_assets_by_ids_service(asset_ids, assessment_id, user, session)
            for asset_id in asset_ids:
                session.execute(
                    activity_asset_association.insert().values(
                        activity_id=activity_db.id, asset_id=asset_id, role=role.value
                    )
                )


def update_activity_service(
    activity_id: uuid.UUID,
    activity: ActivityUpdate,
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> Activity:
    """Update activity properties."""
    activity_db = get_activity_by_id_service(activity_id, assessment_id, user, session)

    # Optimistic concurrency check
    if activity.updated_at is not None and activity_db.updated_at is not None:
        if activity.updated_at != activity_db.updated_at:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This activity has been modified by another user. Please reload and try again.",
            )

    activity = _apply_blue_team_restrictions(activity, user)
    update_data = activity.model_dump()

    # Group reordering
    if "activity_group_id" in update_data:
        _handle_activity_group_change(
            activity_db, update_data, assessment_id, user, session
        )

    # Evaluation
    update_data.pop("updated_at", None)
    evaluation_data = update_data.pop("evaluation", None)
    if evaluation_data:
        _update_evaluation(activity_db, evaluation_data, session)

    # Tags
    tags_to_update = update_data.pop("tags", None)
    if tags_to_update is not None:
        _update_tags(activity_db, tags_to_update, assessment_id, user, session)

    # Assets
    _update_asset_associations(activity_db, update_data, assessment_id, user, session)

    # Apply remaining simple field updates
    for field, value in update_data.items():
        setattr(activity_db, field, value)

    # Recalculate evaluation results from expected/actual fields
    calculate_evaluations(activity_db)

    # Always bump updated_at so linked-element-only changes are tracked.
    # SQLAlchemy's onupdate only fires when Activity columns change directly;
    # linked elements (assets, tags, evaluation) live in separate tables.
    activity_db.updated_by = user.id
    activity_db.updated_at = func.now()

    # Save a shadow copy
    save_activity_shadow_copy(activity_db, session)

    session.commit()
    return activity_db


def toggle_delete_activity_service(
    activity_id: uuid.UUID, assessment_id: uuid.UUID, user: User, session: Session
) -> None:
    """
    Toggle delete state of an activity
    """
    activity_db = get_activity_by_id_service(activity_id, assessment_id, user, session)

    if activity_db.deleted:
        activity_db.deleted = False
        activity_db.deleted_by = None
        activity_db.deleted_at = None
    else:
        activity_db.deleted = True
        activity_db.deleted_by = user.id
        activity_db.deleted_at = func.now()
    session.commit()


def toggle_visible_activity_service(
    activity_id: uuid.UUID, assessment_id: uuid.UUID, user: User, session: Session
) -> None:
    """
    Toggle visible state of an activity
    """
    activity_db = get_activity_by_id_service(activity_id, assessment_id, user, session)

    if activity_db.visible:
        activity_db.visible = False
    else:
        activity_db.visible = True
    activity_db.updated_by = user.id
    activity_db.updated_at = func.now()
    session.commit()


def clone_activity_service(
    activity_id: uuid.UUID, assessment_id: uuid.UUID, user: User, session: Session
) -> Activity:
    """
    Clone an activity by ID.
    """
    activity_db = get_activity_by_id_service(activity_id, assessment_id, user, session)

    # Only copy the included items
    include_fields = {
        "assessment_id",
        "mitre_tactic",
        "mitre_technique",
        "priority",
        "activity_rationale",
        "activity_requirements",
        "expected_logging",
        "expected_prevention",
        "expected_alert_creation",
        "expected_stakeholder_notification",
        "expected_severity",
        "linked_knowledge_base_articles",
    }

    new_data = {}
    for column in activity_db.__table__.columns:
        if column.name in include_fields:
            new_data[column.name] = getattr(activity_db, column.name)

    # Update name to indicate copy
    new_data["name"] = f"{activity_db.name} (Copy)"

    # Assign cloned activity to the same group at the end of the position
    new_data["activity_group_id"] = activity_db.activity_group_id
    new_data["activity_position"] = calculate_new_activity_position(
        session, activity_db.activity_group_id
    )

    new_data["created_by"] = user.id

    new_activity = Activity(**new_data)

    # Handle Tags, SQLAlchemy handles the association table insert automatically for writable relationships
    new_activity.tags = list(activity_db.tags)

    session.add(new_activity)
    session.flush()  # Flush to generate the new activity ID

    # Create evaluation with default dynamic questions from assessment
    create_activity_evaluation(new_activity.id, assessment_id, session)
    session.flush()

    # Recalculate evaluations from cloned expected/actual fields
    session.refresh(new_activity)
    calculate_evaluations(new_activity)

    session.commit()
    return new_activity


def assign_dynamic_evaluation_questions_service(
    activity_id: uuid.UUID,
    dynamic_evaluation_questions: list[DynamicEvaluationQuestionAssign],
    assessment_id: uuid.UUID,
    user: User,
    session: Session,
) -> Activity:
    """
    Assign dynamic evaluation questions to an activity.
    Handles Add, Update (position), and Remove (if not in list).
    """

    activity_db = get_activity_by_id_service(activity_id, assessment_id, user, session)

    # 1. Ensure ActivityEvaluation exists
    if not activity_db.evaluation:
        activity_db.evaluation = ActivityEvaluation(activity_id=activity_db.id)
        session.flush()

    # 2. Extract IDs for validation
    requested_template_ids = {
        q.evaluation_template_id for q in dynamic_evaluation_questions
    }
    requested_positions = [q.position for q in dynamic_evaluation_questions]

    if len(requested_positions) != len(set(requested_positions)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate positions found in dynamic questions.",
        )

    requested_questions_map = {
        q.evaluation_template_id: q for q in dynamic_evaluation_questions
    }

    # 3. Validate Evaluation Templates exist
    statement = select(EvaluationTemplate.id).where(
        EvaluationTemplate.id.in_(requested_template_ids)
    )
    existing_template_ids = session.execute(statement).scalars().all()

    if len(existing_template_ids) != len(requested_template_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more evaluation templates not found.",
        )

    # 4. Synchronize Questions
    # Get existing questions to update/remove
    existing_questions = activity_db.evaluation.dynamic_questions
    existing_questions_map = {q.evaluation_template_id: q for q in existing_questions}

    # A. Update existing (position) and Remove unassigned
    # We can rebuild the list or modifying in place. Modifying in place is safer for ORM.

    # Identify to remove
    to_remove = []
    for q in existing_questions:
        if q.evaluation_template_id not in requested_template_ids:
            to_remove.append(q)
        else:
            # Update position
            new_data = requested_questions_map[q.evaluation_template_id]
            q.position = new_data.position

    for q in to_remove:
        session.delete(q)

    # B. Add new
    for template_id in requested_template_ids:
        if template_id not in existing_questions_map:
            new_data = requested_questions_map[template_id]
            new_question = ActivityEvaluationDynamicQuestions(
                activity_evaluation_id=activity_db.evaluation.id,
                evaluation_template_id=template_id,
                position=new_data.position,
                # Other fields Default
            )
            session.add(new_question)

    # Bump updated_at so concurrency checks detect this change
    activity_db.updated_at = func.now()

    session.commit()
    return activity_db
