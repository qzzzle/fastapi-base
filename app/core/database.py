"""
Portable DB utilities
- Keep your BaseModel pattern.
- Make engine echo depend on ENV (quiet in prod, verbose otherwise).
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session, scoped_session, sessionmaker

from app.core.config import configs

BaseModel = declarative_base()


def _engine_echo() -> bool:
    # Why: minimal behavior without adding settings
    return configs.ENV != "prod"


class Database:
    """Holds the engine and the scoped session factory."""

    def __init__(self, db_url: str):
        self._engine = create_engine(db_url, echo=_engine_echo(), future=True)
        self._session_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self._engine, future=True)
        )

    def create_database(self):
        """Create all tables (for quick starts). Prefer Alembic for real migrations."""
        BaseModel.metadata.create_all(self._engine)

    @contextmanager
    def session(self):
        """
        Yield a session per usage.
        - Commit is explicit (services/repos decide when).
        - On exception: rollback & re-raise.
        - Always close.
        """
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
