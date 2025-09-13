"""
Portable app factory
- No hardcoded router imports.
- Accept routers and wiring modules from the caller (the app layer).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import configs
from app.core.container import Container


def create_app(*, wiring_modules: list[str] = None, routers: list[tuple[str, object]] = None) -> FastAPI:
    """
    Create a FastAPI app.

    Params:
      wiring_modules: list of module dotted paths to wire with DI
                      e.g., ["app.api.v1.endpoints.auth", "app.api.v1.endpoints.user"]
      routers: list of (prefix, router) tuples to include
               e.g., [("/api/v1", v1_router), ("/api/v2", v2_router)]
    """
    app = FastAPI(title=configs.PROJECT_NAME)

    # DI container
    container = Container()
    if wiring_modules:
        container.wiring_config.modules = wiring_modules
    app.container = container  # optional access for tests/diagnostics

    # CORS
    if configs.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=configs.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Health/root
    @app.get("/")
    def root():
        return "service is working"

    # Routers
    if routers:
        for prefix, router in routers:
            app.include_router(router, prefix=prefix)

    return app


# Typical runtime entry (keep it here so uvicorn can find 'app'):
# In your service's __main__ or run file, build the routers and call create_app.
# Example:
from app.api.v1.routes import router as v1_router
app = create_app(
    wiring_modules=["app.api.v1.endpoints.sample",
                    ],
    routers=[(configs.API_V1_STR, v1_router),
             ],
)

