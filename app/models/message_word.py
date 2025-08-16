from __future__ import annotations

from pydantic import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer

from models.common import TimestampedSQLModel


class BaseMessageWord(BaseModel):
    """メッセージの単語(ベース)."""

    message_id: int
    word: str
    tf: int


class MessageWord(BaseMessageWord, TimestampedSQLModel, table=True):
    """メッセージの単語テーブル.

    複合主キー: (message_id, word)
    """

    message_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("message.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    word: str = Field(primary_key=True, index=True)
    tf: int = Field(ge=1)

    # 複合主キーで一意性を担保


class MessageWordCreate(BaseMessageWord):
    """作成用モデル."""


class MessageWordRead(BaseMessageWord, TimestampedSQLModel):
    """読み取り用モデル."""
