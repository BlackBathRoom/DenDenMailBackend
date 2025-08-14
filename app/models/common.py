from datetime import datetime

from sqlmodel import Field, SQLModel


class TimestampedSQLModel(SQLModel):
    """タイムスタンプ共通モデル."""

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
    )


class IdModel(SQLModel):
    """数値ID主キーモデル."""

    id: int | None = Field(primary_key=True)


class BaseSQLModel(IdModel, TimestampedSQLModel):
    """従来のベースSQLモデル(id + タイムスタンプ)."""
