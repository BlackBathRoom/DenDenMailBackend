"""リレーションシップ関係で別モジュールで定義すると循環参照などの問題が発生するMessage関連のモデルを定義.

各モデルは別モジュールからエクスポートし、定義部分を分離しているように見せる.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Column, Field, ForeignKey, Integer, Relationship, SQLModel

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.message_address_map import MessageAddressMap
    from models.message_part import MessagePart
    from models.message_tag_map import MessageTagMap
    from models.message_word import MessageWord


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

    vendor_id: int = Field(sa_column=Column(Integer, ForeignKey("vendor.id", ondelete="RESTRICT"), nullable=False))
    folder_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("folder.id", ondelete="SET NULL"), nullable=True),
    )

    vendor: "Vendor | None" = Relationship(back_populates="messages")
    folder: "Folder | None" = Relationship(back_populates="messages")

    # 1:N related collections
    parts: list["MessagePart"] = Relationship(back_populates="message")
    words: list["MessageWord"] = Relationship(back_populates="message")
    tag_maps: list["MessageTagMap"] = Relationship(back_populates="message")
    address_maps: list["MessageAddressMap"] = Relationship(back_populates="message")
    summary: "Summary | None" = Relationship(
        back_populates="message",
        sa_relationship_kwargs={"uselist": False},
    )


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


class BaseFolder(BaseModel):
    """FOLDERS ベースモデル."""

    name: str
    system_type: str | None = None  # 予約済みフォルダタイプ (Inbox, Trash など)


class Folder(BaseFolder, BaseSQLModel, table=True):
    name: str = Field(unique=True, index=True)
    system_type: str | None = Field(default=None, unique=True, index=True)

    messages: list[Message] = Relationship(back_populates="folder")


class FolderCreate(BaseFolder):
    pass


class FolderRead(BaseFolder, BaseSQLModel):
    pass


class FolderUpdate(SQLModel):
    name: str | None = None


class BaseSummary(BaseModel):
    """サマリのベースモデル.

    Attributes:
    message_id (int): メッセージID.
        content (str): サマリ内容.
    """

    message_id: int
    content: str


class Summary(BaseSummary, BaseSQLModel, table=True):
    """サマリモデル."""

    message_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("message.id", ondelete="CASCADE"),
            unique=True,
            index=True,
        ),
    )

    # 1:1 relation back to Message (scalar)
    message: "Message | None" = Relationship(back_populates="summary")


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


class BaseVendor(BaseModel):
    """VENDORS のベースモデル."""

    name: str


class Vendor(BaseVendor, BaseSQLModel, table=True):
    """取得元クライアント/サービスベンダー."""

    name: str = Field(unique=True, index=True)

    messages: list[Message] = Relationship(back_populates="vendor")


class VendorCreate(BaseVendor):
    pass


class VendorRead(BaseVendor, BaseSQLModel):
    pass
