from typing import TYPE_CHECKING

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, Relationship, SQLModel

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.message_address_map import MessageAddressMap
    from models.priority_person import PriorityPerson


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
    priority: "PriorityPerson | None" = Relationship(
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
