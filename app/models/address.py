from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel

from models.common import BaseSQLModel


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
