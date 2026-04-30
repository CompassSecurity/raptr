from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.schemas.general import PaginatedResponse
from app.schemas.knowledge_base import KnowledgeBaseFilter, KnowledgeBaseRead
from app.services.utils.query import paginated_query


def get_knowledge_base_articles_service(
    user: User,
    session: Session,
    filter_query: KnowledgeBaseFilter,
) -> PaginatedResponse[KnowledgeBaseRead]:
    """
    Get all knowledge base articles based on filters.
    """
    base_statement = select(KnowledgeBase)

    filters = []
    if filter_query.mitre_technique_id:
        filters.append(
            KnowledgeBase.mitre_technique_id == filter_query.mitre_technique_id
        )
    if filter_query.names:
        filters.append(KnowledgeBase.name.in_(filter_query.names))

    if filters:
        base_statement = base_statement.where(or_(*filters))

    # Paginated query applies filters with AND logic (we want an OR between the filters), so we need to clear the specific search filters from the query object passed to paginated_query
    pagination_filter = filter_query.model_copy(
        update={"mitre_technique_id": None, "names": None}
    )

    return paginated_query(
        session, KnowledgeBase, pagination_filter, base_statement=base_statement
    )
