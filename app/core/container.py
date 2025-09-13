"""
Portable DI container
- Do not hardcode endpoint modules to wire.
- Let main.py pass the modules list at startup.
"""

from dependency_injector import containers, providers

from app.core.config import configs
from app.core.database import Database


# NOTE: Repositories/Services remain app-specific; we *declare* providers here when the app passes them.


class Container(containers.DeclarativeContainer):
    """Dependency-Injection container."""

    # Wiring will be assigned dynamically in main.py
    wiring_config = containers.WiringConfiguration(modules=[])

    # Core singletons
    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    # The following providers are declared in app-layer code when needed.
    # Example (kept as guidance; comment them out or define in app bootstrap):
    # user_repository = providers.Factory(UserRepository, session_factory=db.provided.session)
    # user_service = providers.Factory(UserService, user_repository=user_repository)
