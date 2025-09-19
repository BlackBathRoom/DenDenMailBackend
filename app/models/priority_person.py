from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.address import Address


class BasePriorityPerson(BaseModel):
    """人物優先度(ベース)."""

    address_id: int
    priority: int


class PriorityPerson(BasePriorityPerson, BaseSQLModel, table=True):
    """人物優先度モデル."""

    address_id: int = Field(foreign_key="address.id", unique=True, index=True)
    priority: int = Field(ge=1, le=100)
    address: "Address | None" = Relationship(back_populates="priority")


class PriorityPersonCreate(BasePriorityPerson):
    """作成用モデル."""


class PriorityPersonRead(BasePriorityPerson, BaseSQLModel):
    """読み取り用モデル."""


class PriorityPersonUpdate(SQLModel):
    """更新用モデル.

    Attributes:
        priority (int | None): 優先度.
    """

    priority: int | None = Field(default=None, ge=1, le=100)
