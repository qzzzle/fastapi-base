from fastapi import APIRouter

from app.api.v1.endpoints.sample import router as sample_router

routers = APIRouter()
router_list = [
    sample_router, 
    ]

for router in router_list:
    router.tags = routers.tags.append("v1")
    routers.include_router(router)
