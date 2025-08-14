from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, Relationship, SQLModel

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.message import Message


class BaseSummary(BaseModel):
    """サマリのベースモデル.

    Attributes:
    message_id (int): メッセージID.
        content (str): サマリ内容.
    """

    message_id: int
    content: str


class Summary(BaseSummary, BaseSQLModel, table=True):
    """サマリモデル.

    Attributes:
        id (int): サマリID.
        message_id (int): メッセージID(MESSAGES.id にユニーク1:1).
        content (str): サマリ内容.
        created_at (datetime): 作成日時.
        updated_at (datetime): 更新日時.
    """

    message_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("message.id", ondelete="CASCADE"),
            unique=True,
            index=True,
        ),
    )

    # 1:1 Relationship to Message model
    message: Message = Relationship(back_populates="summary")


class SummaryCreate(BaseSummary):
    """サマリ作成用モデル.

    アプリ内にサマリを新規登録する際に使用されるモデル。

    Attributes:
        message_id (str): メッセージID.
        content (str): サマリ内容.
    """


class SummaryRead(BaseSummary, BaseSQLModel):
    """サマリ読み取り用モデル.

    アプリ内でサマリを読み取る際に使用されるモデル。

    Attributes:
        id (int): サマリID.
        message_id (str): メッセージID.
        content (str): サマリ内容.
        created_at (datetime): 作成日時.
        updated_at (datetime): 更新日時.
    """


class SummaryUpdate(SQLModel):
    """サマリ更新用モデル.

    アプリ内でサマリを更新する際に使用されるモデル。

    Attributes:
        content (str): サマリ内容.
    """

    content: str | None = None
