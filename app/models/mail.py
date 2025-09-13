from __future__ import annotations

from datetime import datetime  # noqa: TC003 # pydanticバリデーションのために必要

from pydantic import BaseModel, EmailStr
from sqlmodel import VARCHAR, Column, Field, SQLModel

from app_conf import MailVendor  # noqa: TC001 # pydanticバリデーションのために必要
from models.common import BaseSQLModel


class BaseMail(BaseModel):
    """メールのベースモデル.

    Attributes:
        message_id (str): メッセージID.
        subject (str): 件名.
        received_at (datetime): 受信日時.
        sender_name (str): 送信者.
        sender_address (pydantic.EmailStr): 送信者アドレス.
        mail_folder (str): フォルダ.
        is_read (bool): 既読フラグ.
        vender (MailVendor): メールクライアント名.
    """

    message_id: str
    subject: str
    received_at: datetime
    sender_name: str
    sender_address: EmailStr
    mail_folder: str
    is_read: bool = False
    vender: MailVendor


class Mail(BaseMail, BaseSQLModel, table=True):
    """メールモデル.

    Attributes:
        id (int): アプリ内メールID.
        message_id (str): メッセージID.
        subject (str): 件名.
        received_at (datetime): 受信日時.
        sender_name (str): 送信者.
        sender_address (str): 送信者アドレス.
        mail_folder (str): フォルダ.
        is_read (bool): 既読フラグ.
        created_at (datetime): アプリdbに登録された日時.
        updated_at (datetime): アプリdbで更新された日時.
        vender (MailVendor): メールクライアント名.
    """

    message_id: str = Field(index=True, unique=True)
    vender: MailVendor = Field(sa_column=Column(VARCHAR))

    # 旧モデル。MESSAGESへ移行予定。リレーションは未使用化。


class MailCreate(BaseMail):
    """メール作成用モデル.

    アプリ内にメールを新規登録する際に使用されるモデル。

    Attributes:
        message_id (str): メッセージID.
        subject (str): 件名.
        received_at (datetime): 受信日時.
        sender_name (str): 送信者.
        sender_address (str): 送信者アドレス.
        mail_folder (str): フォルダ.
        is_read (bool): 既読フラグ.
        vender (MailVendor): メールクライアント名.
    """


class MailRead(BaseMail, BaseSQLModel):
    """メール読み取り用モデル.

    メールを読み取る際に使用されるモデル。

    Attributes:
        id (int): アプリ内メールID.
        message_id (str): メッセージID.
        subject (str): 件名.
        received_at (datetime): 受信日時.
        sender_name (str): 送信者.
        sender_address (str): 送信者アドレス.
        mail_folder (str): フォルダ.
        is_read (bool): 既読フラグ.
        created_at (datetime): アプリdbに登録された日時.
        vender (MailVendor): メールクライアント名.
    """


class MailUpdate(SQLModel):
    """メール更新用モデル.

    メールを更新する際に使用されるモデル。

    Attributes:
        mail_folder (str | None): フォルダ.
        is_read (bool | None): 既読フラグ.
    """

    mail_folder: str | None = None
    is_read: bool | None = None
