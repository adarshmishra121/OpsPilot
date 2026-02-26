"""Database engine and session management (SQLModel)."""

import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./opspilot.db")

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create all tables that don't exist yet."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for dependency injection in FastAPI routes."""
    with Session(engine) as session:
        yield session
