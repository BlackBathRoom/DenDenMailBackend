from pydantic import BaseModel
from sqlmodel import Column, Field, ForeignKey, Index, Integer

from models.common import BaseSQLModel


class BaseMessagePart(BaseModel):
    """MIMEパーツの共通ベース."""

    mime_type: str | None = None
    mime_subtype: str | None = None
    filename: str | None = None
    content_id: str | None = Field(default=None)
    content_disposition: str | None = None
    content: bytes | None = None
    part_order: int | None = None
    is_attachment: bool | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class MessagePart(BaseMessagePart, BaseSQLModel, table=True):
    """MIMEパーツモデル."""

    __table_args__ = (
        Index(
            "ix_message_part_message_id_is_attachment_part_order",
            "message_id",
            "is_attachment",
            "part_order",
        ),
    )

    message_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("message.id", ondelete="CASCADE"),
            index=True,
        ),
    )
    parent_part_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("messagepart.id", ondelete="CASCADE"),
        ),
    )
    content_id: str | None = Field(default=None, index=True)

    # note: relationships are defined on demand in Message side if needed.


class MessagePartCreate(BaseMessagePart):
    """作成用モデル."""

    message_id: int
    parent_part_id: int | None = None


class MessagePartRead(BaseMessagePart, BaseSQLModel):
    """読み取り用モデル."""

    message_id: int
    parent_part_id: int | None = None
