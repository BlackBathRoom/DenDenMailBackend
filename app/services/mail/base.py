from abc import ABC, abstractmethod
from typing import TypedDict

from models.mail import BaseMail
from utils.check_implementation import check_implementation


class MailData(BaseMail):
    """メールデータの型定義.

    メールクライアントから取得した情報も含む.

    Attributes:
        message_id (str): メッセージID.
        subject (str): 件名.
        body (str): メール本文.
        received_at (datetime): 受信日時.
        sender_name (str): 送信者名.
        sender_address (str): 送信者アドレス.
        mail_folder (str): フォルダ名.
        is_read (bool): 既読フラグ.
        vender (str): メールクライアント名.
    """

    body: str


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
    def get_mails(self, count: int = 10) -> list[MailData]:
        """アプリ上に登録されていない新規メールを取得する.

        Args:
            count (int): 取得するメールの数.デフォルトは10件.

        Returns:
            list[MailData]: 取得したメールのリスト.
        """

    @abstractmethod
    @check_implementation
    def get_mail(self, message_id: str) -> MailData | None:
        """メッセージIDでメールを取得する.

        Args:
            message_id (str): メッセージID.

        Returns:
            MailData | None: メールデータ.見つからない場合はNone.
        """
