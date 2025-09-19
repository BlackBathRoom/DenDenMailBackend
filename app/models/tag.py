from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.message_tag_map import MessageTagMap


class BaseTag(BaseModel):
    """タグ(ベース)."""

    tag_name: str


class Tag(BaseTag, BaseSQLModel, table=True):
    """タグモデル."""

    tag_name: str = Field(unique=True, index=True)
    message_maps: list["MessageTagMap"] = Relationship(back_populates="tag")


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
