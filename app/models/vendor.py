from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.message import Message


class BaseVendor(BaseModel):
    """VENDORS のベースモデル."""

    name: str


class Vendor(BaseVendor, BaseSQLModel, table=True):
    """取得元クライアント/サービスベンダー."""

    name: str = Field(unique=True, index=True)

    # reverse relationship
    messages: list[Message] = Relationship(back_populates="vendor")


class VendorCreate(BaseVendor):
    pass


class VendorRead(BaseVendor, BaseSQLModel):
    pass


class VendorUpdate(BaseModel):
    # name は更新不可ポリシーなので空 (将来追加する場合用意)
    pass
