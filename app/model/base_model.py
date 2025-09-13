from datetime import datetime

from sqlmodel import Column, DateTime, Field, SQLModel, func, Integer


class BaseModel(SQLModel):
    id: int = Field(primary_key=True)

    # timestamps
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    modified_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # user references
    created_by: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="User ID who created the record"
    )
    modified_by: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="User ID who last modified the record"
    )
    deleted_by: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="User ID who deleted the record"
    )
