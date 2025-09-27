"""リレーションシップ関係で循環参照が起きやすいモデル群を1箇所に集約して定義します.

各モデルは個別モジュールから再エクスポートし、利用側の import パスは変えずに疎結合を保ちます。
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr
from sqlmodel import (
    CheckConstraint,
    Column,
    Field,
    ForeignKey,
    Index,
    Integer,
    Relationship,
    SQLModel,
)

from models.common import BaseSQLModel, TimestampedSQLModel


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
    # 代表送信者(Address)へのFK (from アドレスの先頭を採用 / 無ければ None)
    sender_address_id: int | None = None


class Message(BaseMessage, BaseSQLModel, table=True):
    """MESSAGES テーブルモデル."""

    rfc822_message_id: str = Field(unique=True, index=True)
    date_received: datetime = Field(index=True)

    vendor_id: int = Field(sa_column=Column(Integer, ForeignKey("vendor.id", ondelete="RESTRICT"), nullable=False))
    folder_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("folder.id", ondelete="SET NULL"), nullable=True),
    )
    sender_address_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("address.id", ondelete="SET NULL"), nullable=True, index=True),
    )

    vendor: "Vendor" = Relationship(back_populates="messages")
    folder: "Folder" = Relationship(back_populates="messages")

    # 1:N related collections
    parts: list["MessagePart"] = Relationship(back_populates="message")
    words: list["MessageWord"] = Relationship(back_populates="message")
    tag_maps: list["MessageTagMap"] = Relationship(back_populates="message")
    address_maps: list["MessageAddressMap"] = Relationship(back_populates="message")
    summary: "Summary" = Relationship(
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
    message: "Message" = Relationship(back_populates="summary")


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


# -----------------------------
# Address
# -----------------------------


class BaseAddress(BaseModel):
    """アドレスのベースモデル.

    Attributes:
        email_address (EmailStr): メールアドレス.
        display_name (str | None): 表示名.
    """

    email_address: EmailStr
    display_name: str | None = None


class Address(BaseAddress, BaseSQLModel, table=True):
    """アドレスモデル.

    Attributes:
        id (int): アドレスID.
        email_address (str): メールアドレス(ユニーク制約).
        display_name (str | None): 表示名.
    """

    email_address: str = Field(index=True, unique=True)
    message_maps: list["MessageAddressMap"] = Relationship(back_populates="address")
    priority: "PriorityPerson" = Relationship(
        back_populates="address",
        sa_relationship_kwargs={"uselist": False},
    )


class AddressCreate(BaseAddress):
    """アドレス作成用モデル."""


class AddressRead(BaseAddress, BaseSQLModel):
    """アドレス読み取り用モデル."""


class AddressUpdate(SQLModel):
    """アドレス更新用モデル.

    Attributes:
        display_name (str | None): 表示名.
    """

    display_name: str | None = None


# -----------------------------
# MessageAddressMap
# -----------------------------


class AddressType(str, Enum):
    FROM = "from"
    TO = "to"
    CC = "cc"
    BCC = "bcc"


class BaseMessageAddressMap(BaseModel):
    """メールとアドレスの対応(ベース)."""

    message_id: int
    address_id: int
    address_type: AddressType


class MessageAddressMap(BaseMessageAddressMap, TimestampedSQLModel, table=True):
    """メールとアドレスの対応テーブル.

    複合主キー: (message_id, address_id, address_type)
    """

    message_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("message.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    address_id: int = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("address.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    address_type: AddressType = Field(primary_key=True)

    # 複合主キーで一意性を担保
    __table_args__ = (
        CheckConstraint(
            "address_type in ('from','to','cc','bcc')",
            name="ck_message_address_map_address_type",
        ),
    )

    message: "Message" = Relationship(back_populates="address_maps")
    address: "Address" = Relationship(back_populates="message_maps")


class MessageAddressMapCreate(BaseMessageAddressMap):
    """作成用モデル."""


class MessageAddressMapRead(BaseMessageAddressMap, TimestampedSQLModel):
    """読み取り用モデル."""


# -----------------------------
# PriorityPerson
# -----------------------------


class BasePriorityPerson(BaseModel):
    """人物優先度(ベース)."""

    address_id: int
    priority: int


class PriorityPerson(BasePriorityPerson, BaseSQLModel, table=True):
    """人物優先度モデル."""

    address_id: int = Field(foreign_key="address.id", unique=True, index=True)
    priority: int = Field(ge=1, le=100)
    address: "Address" = Relationship(back_populates="priority")


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


# -----------------------------
# MessagePart
# -----------------------------


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
    # Relations
    message: "Message" = Relationship(back_populates="parts")


class MessagePartCreate(BaseMessagePart):
    """作成用モデル."""

    message_id: int
    parent_part_id: int | None = None


class MessagePartRead(BaseMessagePart, BaseSQLModel):
    """読み取り用モデル."""

    message_id: int
    parent_part_id: int | None = None


# -----------------------------
# MessageTagMap
# -----------------------------


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
    message: "Message" = Relationship(back_populates="tag_maps")
    tag: "Tag" = Relationship(back_populates="message_maps")


class MessageTagMapCreate(BaseMessageTagMap):
    """作成用モデル."""


class MessageTagMapRead(BaseMessageTagMap, TimestampedSQLModel):
    """読み取り用モデル."""


# -----------------------------
# MessageWord
# -----------------------------


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
    message: "Message" = Relationship(back_populates="words")


class MessageWordCreate(BaseMessageWord):
    """作成用モデル."""


class MessageWordRead(BaseMessageWord, TimestampedSQLModel):
    """読み取り用モデル."""


# -----------------------------
# Tag
# -----------------------------


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
