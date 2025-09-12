from __future__ import annotations

from datetime import datetime  # noqa: TC003 # datetime is used in validation
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, Relationship, SQLModel

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.folder import Folder
    from models.summary import Summary
    from models.vendor import Vendor


class BaseMessage(BaseModel):
    """MESSAGES のベースモデル.

    vendor_id: 取得元クライアント(Vendor)へのFK
    folder_id: 所属フォルダ(Folder)へのFK (NULL可 / 移動で更新可)
    """

    rfc822_message_id: str
    subject: str
    date_sent: datetime | None = None
    date_received: datetime
    in_reply_to: str | None = None
    references_list: str | None = None
    is_read: bool = False
    is_replied: bool = False
    is_flagged: bool = False
    is_forwarded: bool = False
    vendor_id: int
    folder_id: int | None = None


class Message(BaseMessage, BaseSQLModel, table=True):
    """MESSAGES テーブルモデル."""

    rfc822_message_id: str = Field(unique=True, index=True)
    date_received: datetime = Field(index=True)

    # FK 定義 (明示的に ondelete 設定)
    vendor_id: int = Field(sa_column=Column(Integer, ForeignKey("vendor.id", ondelete="RESTRICT"), nullable=False))
    folder_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("folder.id", ondelete="SET NULL"), nullable=True),
    )

    # Relationships
    vendor: Vendor = Relationship(back_populates="messages")
    folder: Folder | None = Relationship(back_populates="messages")
    summary: Summary | None = Relationship(back_populates="message")  # 1:1 Summary


class MessageCreate(BaseMessage):
    """作成用モデル."""


class MessageRead(BaseMessage, BaseSQLModel):
    """読み取り用モデル."""


class MessageUpdate(SQLModel):
    """更新用モデル(更新可のみ)."""

    is_read: bool | None = None
    is_replied: bool | None = None
    is_flagged: bool | None = None
    is_forwarded: bool | None = None
    folder_id: int | None = None  # フォルダ移動を許可
