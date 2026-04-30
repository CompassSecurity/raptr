from fastapi import APIRouter

from app.api.v1.assessments import (
    activity,
    activity_group,
    asset,
    exports,
    imports,
    statistics,
    tag,
)

router = APIRouter(
    prefix="/assessments/{assessment_id}",
)

router.include_router(activity_group.router)
router.include_router(activity.router)
router.include_router(asset.router)
router.include_router(tag.router)
router.include_router(imports.router)
router.include_router(exports.router)
router.include_router(statistics.router)
