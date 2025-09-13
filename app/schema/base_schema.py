from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ModelBaseInfo(BaseModel):
    """Matches your SQLModel BaseModel field names for read models."""
    id: int
    created_at: datetime
    modified_at: datetime
    deleted_at: datetime | None = None

    created_by: int | None = None
    modified_by: int | None = None
    deleted_by: int | None = None


class FindBase(BaseModel):
    """Common pagination/sorting inputs used by list endpoints."""
    ordering: str | None = None              # e.g. "created_at" or "-created_at"
    page: int | None = Field(default=1, ge=1)
    page_size: int | str | None = None       # keep your design (int or "all")


class SearchOptions(FindBase):
    """Echo back effective search options + optional counters."""
    total_count: int | None = None


class FindResult(BaseModel, Generic[T]):
    """Generic wrapper for search/list responses."""
    founds: list[T] | None = None
    search_options: SearchOptions | None = None


class FindDateRange(BaseModel):
    """
    Date range filters (Django-style lookups).
    Use aware datetimes; your DB model uses timezone=True.
    """
    created_at__lt: datetime | None = None
    created_at__lte: datetime | None = None
    created_at__gt: datetime | None = None
    created_at__gte: datetime | None = None


class Blank(BaseModel):
    """Empty body placeholder where an object is required by the route."""
    pass
