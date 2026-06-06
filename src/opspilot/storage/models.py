"""SQLModel table definitions for persistent storage."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class FeedbackRow(SQLModel, table=True):
    """Stores human feedback on incident analysis quality."""

    id: int | None = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True)
    helpful: bool
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
