from pydantic import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer

from models.common import TimestampedSQLModel


class BaseMessageTagMap(BaseModel):
    """メールとタグの対応(ベース)."""

    message_id: int
    tag_id: int


class MessageTagMap(BaseMessageTagMap, TimestampedSQLModel, table=True):
    """メールとタグの対応テーブル.

    複合主キー: (message_id, tag_id)
    """

    message_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("message.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    tag_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("tag.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # 複合主キーで一意性を担保

    # note: relationships are defined on demand in owner models if needed.


class MessageTagMapCreate(BaseMessageTagMap):
    """作成用モデル."""


class MessageTagMapRead(BaseMessageTagMap, TimestampedSQLModel):
    """読み取り用モデル."""
