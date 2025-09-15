from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router as v1_router
from app.core.config import configs
from app.core.container import Container


def create_app(*, wiring_modules: list[str] | None = None) -> FastAPI:
    app = FastAPI(title=configs.PROJECT_NAME)

    # DI container
    container = Container()
    if wiring_modules:
        container.wiring_config.modules = wiring_modules
    app.container = container

    # CORS
    if configs.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=configs.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Health
    @app.get("/health")
    def health():
        return "service is working"

    # Important: include the v1 router ONCE, without adding another prefix.
    app.include_router(v1_router)

    return app


# Uvicorn entry point
app = create_app(
    wiring_modules=[
        "app.api.v1.endpoints.sample",
    ],
)
