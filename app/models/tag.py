from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from models.common import BaseSQLModel


class BaseTag(BaseModel):
    """タグ(ベース)."""

    tag_name: str


class Tag(BaseTag, BaseSQLModel, table=True):
    """タグモデル."""

    tag_name: str = Field(unique=True, index=True)


class TagCreate(BaseTag):
    """作成用モデル."""


class TagRead(BaseTag, BaseSQLModel):
    """読み取り用モデル."""


class TagUpdate(SQLModel):
    """更新用モデル.

    Attributes:
        tag_name (str | None): タグ名.
    """

    tag_name: str | None = None
