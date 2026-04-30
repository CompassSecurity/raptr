from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.mfa import mfa_validation_service
from app.db.session import get_session
from app.models.user import User
from app.schemas.general import PaginatedResponse
from app.schemas.knowledge_base import KnowledgeBaseFilter, KnowledgeBaseRead
from app.services.knowledge_base.knowledge_base import (
    get_knowledge_base_articles_service,
)

router = APIRouter(
    prefix="/knowledge-base",
    tags=["knowledge-base"],
)


@router.get("/", response_model=PaginatedResponse[KnowledgeBaseRead])
def get_knowledge_base_articles(
    filter_query: Annotated[KnowledgeBaseFilter, Query()],
    user: Annotated[User, Depends(mfa_validation_service)],
    session: Annotated[Session, Depends(get_session)],
) -> PaginatedResponse[KnowledgeBaseRead]:
    """
    Get knowledge base articles.
    """
    return get_knowledge_base_articles_service(user, session, filter_query)
