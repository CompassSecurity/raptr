from fastapi import APIRouter

from app.api.v1.acl import acl
from app.api.v1.activity_group_template import activity_group_template
from app.api.v1.activity_template import activity_template
from app.api.v1.admin import admin
from app.api.v1.assessment import assessment
from app.api.v1.assessments import assessments_router
from app.api.v1.auth import auth
from app.api.v1.campaign_template import campaign_template
from app.api.v1.evaluation_template import evaluation_template
from app.api.v1.health import health
from app.api.v1.knowledge_base import knowledge_base
from app.api.v1.mitre import mitre
from app.api.v1.report_template import report_template
from app.api.v1.user import user

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(acl.router)
router.include_router(activity_template.router)
router.include_router(activity_group_template.router)
router.include_router(campaign_template.router)
router.include_router(evaluation_template.router)
router.include_router(report_template.router)
router.include_router(knowledge_base.router)
router.include_router(mitre.router)
router.include_router(admin.router)
router.include_router(user.router)
router.include_router(assessment.router)
router.include_router(assessments_router.router)
