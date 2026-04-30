import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.authorization import (
    require_assessment_role,
    validate_activity_update_permission,
)
from app.db.session import get_session
from app.enums.enums import AclRole, ActivityAssetRole
from app.models.user import User
from app.schemas.activity import (
    ActivityBase,
    ActivityFilter,
    ActivityRead,
    ActivityUpdate,
)
from app.schemas.activity_evaluation_dynamic_questions import (
    DynamicEvaluationQuestionAssign,
)
from app.schemas.activity_group import ActivityGroupUpdate
from app.schemas.activity_history import ActivityHistoryRead
from app.schemas.asset import ActivityAssetUpdate
from app.schemas.file import FileFilter, FileRead, FileUploadResponse
from app.schemas.general import MessageResponse, PaginatedResponse
from app.schemas.tag import ActivityTagsUpdate
from app.services.activity.activity import (
    assign_dynamic_evaluation_questions_service,
    clone_activity_service,
    create_activity_service,
    get_activity_by_id_service,
    get_all_activities_service,
    toggle_delete_activity_service,
    toggle_visible_activity_service,
    update_activity_service,
)
from app.services.activity_group.activity_group import (
    assign_activity_to_activity_group_service,
    remove_activity_from_activity_group_service,
)
from app.services.activity_history.activity_history import (
    get_activity_history_list_service,
    get_activity_history_version_service,
)
from app.services.asset.asset import assign_assets_to_activity
from app.services.file.file import (
    delete_file_service,
    get_activity_file_by_id_service,
    get_activity_files_service,
    upload_file_service,
)
from app.services.tag.tag import update_activity_tags_service

router = APIRouter(
    prefix="/activity",
    tags=["activity"],
)


@router.get("/", response_model=PaginatedResponse[ActivityRead])
def get_all_activities(
    assessment_id: uuid.UUID,
    filter_query: Annotated[ActivityFilter, Query()],
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get all activities for an assessment.
    """
    return get_all_activities_service(assessment_id, user, session, filter_query)


@router.get("/{activity_id}", response_model=ActivityRead)
def get_activity_by_id(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get an activity by ID.
    """
    return get_activity_by_id_service(activity_id, assessment_id, user, session)


@router.post("/", response_model=ActivityRead)
def create_activity(
    activity: ActivityBase,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Create a new activity for an assessment.
    """
    return create_activity_service(activity, assessment_id, user, session)


@router.put("/{activity_id}", response_model=ActivityRead)
def update_activity(
    activity_id: uuid.UUID,
    activity: ActivityUpdate,
    assessment_id: uuid.UUID,
    user: User = Depends(validate_activity_update_permission),
    session: Session = Depends(get_session),
):
    """
    Update an activity by ID.
    """
    return update_activity_service(activity_id, activity, assessment_id, user, session)


@router.put("/{activity_id}/delete", response_model=MessageResponse)
def toggle_delete_activity_state(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Toggle delete state of an activity by ID.
    """
    toggle_delete_activity_service(activity_id, assessment_id, user, session)
    return MessageResponse(message="Activity deleted state toggled successfully")


@router.put("/{activity_id}/clone", response_model=ActivityRead)
def clone_activity(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Clone an activity by ID.
    """
    return clone_activity_service(activity_id, assessment_id, user, session)


@router.put("/{activity_id}/tags", response_model=ActivityRead)
def assign_update_activity_tags(
    activity_id: uuid.UUID,
    tags: ActivityTagsUpdate,
    assessment_id: uuid.UUID,
    user: User = Depends(validate_activity_update_permission),
    session: Session = Depends(get_session),
):
    """
    Update tags for an activity. Replaces all existing tags with the provided list.
    """
    return update_activity_tags_service(
        activity_id, tags.tag_ids, assessment_id, user, session
    )


@router.put("/{activity_id}/activity_group", response_model=ActivityRead)
def assign_update_activity_to_activity_group(
    activity_id: uuid.UUID,
    activity_group_update: ActivityGroupUpdate,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Assign an activity to a group or remove it.
    To assign: Provide activity_group_id.
    To remove: Provide activity_group_id as null.
    """
    if activity_group_update.activity_group_id:
        return assign_activity_to_activity_group_service(
            activity_id,
            activity_group_update.activity_group_id,
            assessment_id,
            user,
            session,
        )
    else:
        return remove_activity_from_activity_group_service(
            activity_id, assessment_id, user, session
        )


@router.put("/{activity_id}/assets/{role}", response_model=MessageResponse)
def assign_update_assets_to_activity(
    activity_id: uuid.UUID,
    role: ActivityAssetRole,
    asset_update: ActivityAssetUpdate,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Assign assets to an activity for a specific role (source, target, tool, etc.).
    Replaces all existing assets for this role.
    """
    assign_assets_to_activity(
        activity_id, role, asset_update.asset_ids, assessment_id, user, session
    )
    return MessageResponse(message=f"Assets assigned to activity as {role.value}")


@router.put("/{activity_id}/visible", response_model=MessageResponse)
def toggle_visible_activity(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    toggle_visible_activity_service(activity_id, assessment_id, user, session)
    return MessageResponse(message="Activity visible state toggled successfully")


@router.put("/{activity_id}/dynamic_evaluation_questions", response_model=ActivityRead)
def assign_dynamic_evaluation_questions(
    activity_id: uuid.UUID,
    dynamic_evaluation_questions: list[DynamicEvaluationQuestionAssign],
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Assign, update, remove dynamic evaluation questions to an activity.
    """
    return assign_dynamic_evaluation_questions_service(
        activity_id, dynamic_evaluation_questions, assessment_id, user, session
    )


@router.get("/{activity_id}/files", response_model=list[FileRead])
def get_activity_files(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    filter_query: Annotated[FileFilter, Query()],
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get files for an activity.
    """
    return get_activity_files_service(
        activity_id, assessment_id, user, session, filter_query
    )


@router.get("/{activity_id}/files/{file_id}", response_model=FileRead)
def get_activity_file(
    activity_id: uuid.UUID,
    file_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Get a file for an activity.
    """
    return get_activity_file_by_id_service(
        file_id, activity_id, assessment_id, user, session
    )


@router.get("/{activity_id}/files/{file_id}/download")
def download_activity_file(
    activity_id: uuid.UUID,
    file_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.SPECTATOR)),
    session: Session = Depends(get_session),
):
    """
    Download a file for an activity.
    """
    file = get_activity_file_by_id_service(
        file_id, activity_id, assessment_id, user, session
    )

    return StreamingResponse(
        io.BytesIO(file.file_content),
        media_type=file.content_type,
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )


@router.post("/{activity_id}/upload", response_model=FileUploadResponse)
def upload_file(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Upload a file to an activity.
    """
    return upload_file_service(activity_id, file, assessment_id, user, session)


@router.delete("/{activity_id}/files/{file_id}", response_model=MessageResponse)
def delete_activity_file(
    file_id: uuid.UUID,
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.BLUE)),
    session: Session = Depends(get_session),
):
    """
    Delete a file for an activity.
    """
    delete_file_service(file_id, activity_id, assessment_id, user, session)
    return MessageResponse(message="File deleted successfully")


@router.get("/{activity_id}/version", response_model=list[ActivityHistoryRead])
def get_activity_history_list(
    activity_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Get a list of all historical versions of an activity.
    """
    return get_activity_history_list_service(activity_id, assessment_id, user, session)


@router.get("/{activity_id}/version/{version_id}", response_model=ActivityHistoryRead)
def get_activity_history_version(
    activity_id: uuid.UUID,
    version_id: uuid.UUID,
    assessment_id: uuid.UUID,
    user: User = Depends(require_assessment_role(AclRole.RED)),
    session: Session = Depends(get_session),
):
    """
    Get a specific historical version (snapshot) of an activity.
    """
    return get_activity_history_version_service(
        activity_id, version_id, assessment_id, user, session
    )
