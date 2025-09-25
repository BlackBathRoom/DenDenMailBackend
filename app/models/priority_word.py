from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from models.common import BaseSQLModel


class BasePriorityWord(BaseModel):
    """単語優先度(ベース)."""

    word: str
    priority: int


class PriorityWord(BasePriorityWord, BaseSQLModel, table=True):
    """単語優先度モデル."""

    word: str = Field(unique=True, index=True)
    priority: int = Field(ge=1, le=100)


class PriorityWordCreate(BasePriorityWord):
    """作成用モデル."""


class PriorityWordRead(BasePriorityWord, BaseSQLModel):
    """読み取り用モデル."""


class PriorityWordUpdate(SQLModel):
    """更新用モデル.

    Attributes:
        priority (int | None): 優先度.
    """

    priority: int | None = Field(default=None, ge=1, le=100)
