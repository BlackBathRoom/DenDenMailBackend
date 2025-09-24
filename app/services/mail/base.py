from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict

from pydantic import BaseModel, EmailStr, Field

from app_conf import MailVendor  # noqa: TC001
from models.message import BaseMessage
from models.message_part import BaseMessagePart
from utils.check_implementation import check_implementation


class MessagePartData(BaseMessagePart):
    """取得時に扱うMIMEパーツデータ(保存ロジックと分離).

    Notes:
        parent_part_order は直近の親パート (multipart など) の part_order を指す。
        ルート直下のパートは None。
    """

    parent_part_order: int | None = None


class MessageAddressData(BaseModel):
    """メールアドレスの取得時データ.

    Notes:
        DBの Address とは分離し、取得レイヤの最小データとして保持する。
    """

    email_address: EmailStr
    display_name: str | None = None


class MessageData(BaseMessage):
    """メールデータの型定義.

    メールクライアントから取得した情報も含む.

    Attributes:
    rfc822_message_id (str): RFC 822 Message-ID.
        subject (str): 件名.
    date_received (datetime): 受信日時.
    date_sent (datetime | None): 送信日時(ヘッダーのDate).
        is_read (bool): 既読フラグ.
    vendor (str): メールクライアント名.
    """

    # dbのidを検索し含めるのは冗長なのでenumをフィールドで保持、判断
    mail_vendor: MailVendor
    folder: str | None = Field(default="INBOX")
    parts: list[MessagePartData] = Field(default_factory=list)
    # 取得時に判明しているアドレス群(保存時に正規化し Address/MESSAGE_ADDRESS_MAP へ)
    from_addrs: list[MessageAddressData] = Field(default_factory=list)
    to_addrs: list[MessageAddressData] = Field(default_factory=list)
    cc_addrs: list[MessageAddressData] = Field(default_factory=list)
    bcc_addrs: list[MessageAddressData] = Field(default_factory=list)


class BaseClientConfig(TypedDict):
    """メールクライアントの設定情報.

    各クライアントで接続に必要な情報をこのクラスを継承しまとめる.
    """

    connection_type: str


class BaseMailClient[T: BaseClientConfig](ABC):
    """メールクライアントの基底クラス."""

    def __init__(self, config: T) -> None:
        self.config = config

    @abstractmethod
    @check_implementation
    def connect(self) -> None:
        """メールサーバーに接続する."""

    @abstractmethod
    @check_implementation
    def disconnect(self) -> None:
        """メールサーバーから切断する."""

    @abstractmethod
    @check_implementation
    def get_mails(self, count: int = 10) -> list[MessageData]:
        """アプリ上に登録されていない新規メールを取得する.

        Args:
            count (int): 取得するメールの数.デフォルトは10件.

        Returns:
            list[MessageData]: 取得したメールのリスト.
        """

    @abstractmethod
    @check_implementation
    def get_mail(self, message_id: str) -> MessageData | None:
        """メッセージIDでメールを取得する.

        Args:
            message_id (str): メッセージID.

        Returns:
            MessageData | None: メールデータ.見つからない場合はNone.
        """
