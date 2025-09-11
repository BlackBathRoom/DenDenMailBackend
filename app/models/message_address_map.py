from enum import Enum

from pydantic import BaseModel
from sqlmodel import CheckConstraint, Column, Field, ForeignKey, Integer

from models.common import TimestampedSQLModel


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

    # note: relationships can be added in owner models if needed.


class MessageAddressMapCreate(BaseMessageAddressMap):
    """作成用モデル."""


class MessageAddressMapRead(BaseMessageAddressMap, TimestampedSQLModel):
    """読み取り用モデル."""
