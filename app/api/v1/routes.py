from fastapi import APIRouter

from app.api.v1.endpoints.sample import router as sample_router

router = APIRouter(prefix="/api/v1")

router.include_router(sample_router, prefix="/sample", tags=["sample"])
