from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from models.common import BaseSQLModel
from models.summary import Summary


class BaseMessage(BaseModel):
    """MESSAGES のベースモデル."""

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
    vendor: str


class Message(BaseMessage, BaseSQLModel, table=True):
    """MESSAGES テーブルモデル."""

    rfc822_message_id: str = Field(unique=True, index=True)
    date_received: datetime = Field(index=True)

    # 1:1 Summary
    summary: Summary | None = Relationship(back_populates="message")


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
