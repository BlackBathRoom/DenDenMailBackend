"""Thunderbirdメールクライアントの実装."""

import mailbox

from datetime import datetime
from email.errors import MessageError
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

from app.services.mail.thunderbird.thunderbird_path import ThunderbirdPath
from app_conf import MailVender
from services.mail.base import BaseClientConfig, BaseMailClient, MailData
from utils.log_config import get_logger

logger = get_logger(__name__)


class ThunderbirdConfig(BaseClientConfig):
    """Thunderbirdメールクライアントの設定情報."""


class ThunderbirdClient(BaseMailClient[ThunderbirdConfig]):
    """Thunderbirdメールクライアントの実装."""

    def __init__(self, config: ThunderbirdConfig) -> None:
        super().__init__(config)
        self.path = ThunderbirdPath()

    def connect(self) -> None:
        """Thunderbirdクライアントはローカルファイルシステムを使用するため、特に接続処理は不要."""
        logger.info("Connected to Thunderbird client.")

    def disconnect(self) -> None:
        """Thunderbirdクライアントはローカルファイルシステムを使用するため、特に切断処理は不要."""
        logger.info("Disconnected from Thunderbird client.")

    def _parse_mailbox_file(self, file_path: Path, count: int = 10) -> list[MailData]:
        """メールボックスファイルからメールをパースして取得.

        Args:
            file_path: メールボックスファイルのパス
            count: 取得するメール数

        Returns:
            list[MailData]: パースされたメールのリスト
        """
        mails = []

        try:
            logger.info("Parsing mailbox file: %s", file_path)

            # mboxファイルとして開く
            mbox = mailbox.mbox(str(file_path))

            logger.info("Total messages in %s: %d", file_path.name, len(mbox))

            # メールを最新順でソートして取得
            messages = list(mbox)
            messages.reverse()

            for i, message in enumerate(messages[:count]):
                try:
                    mail_data = self._parse_single_mail(message)
                    if mail_data:
                        mails.append(mail_data)
                        logger.debug("Parsed mail %d: %s", i + 1, mail_data.subject)
                except (MessageError, UnicodeDecodeError) as e:
                    logger.warning("Failed to parse mail %d: %s", i + 1, e)
                    continue

        except (OSError, mailbox.Error):
            logger.exception("Failed to parse mailbox file %s", file_path)

        logger.info("Successfully parsed %d mails from %s", len(mails), file_path.name)
        return mails

    def _parse_single_mail(self, message: Message) -> MailData | None:
        """単一メールメッセージをパースしてMailDataに変換.

        Args:
            message: emailメッセージオブジェクト

        Returns:
            MailData | None: パースされたメールデータ
        """
        mail_data = None
        try:
            subject = self._decode_header(message.get("Subject", "件名なし"))
            sender = self._decode_header(message.get("From", "送信者不明"))
            sender_name, sender_address = self._parse_sender(sender)
            received_time = self._parse_date(message.get("Date", "")) or datetime.now().astimezone()
            message_id = message.get("Message-ID", "")

            # メール本文を取得してHTMLとテキストを統合処理
            text_body, html_body = self._extract_body(message)
            body = html_body if html_body else text_body

            # MailDataオブジェクト作成
            mail_data = MailData(
                message_id=message_id,
                subject=subject,
                received_at=received_time,
                sender_name=sender_name,
                sender_address=sender_address,
                mail_folder="INBOX",  # Thunderbirdの場合は固定
                is_read=False,  # 新規取得メールは未読として扱う
                vender=MailVender.THUNDERBIRD,
                body=body,
            )

        except (MessageError, UnicodeDecodeError, ValueError) as e:
            logger.warning("Failed to parse single mail: %s", e)
            return None
        return mail_data

    def _parse_sender(self, sender_str: str) -> tuple[str, str]:
        """送信者文字列から名前とアドレスを分離.

        Args:
            sender_str: 送信者の文字列 (例: "田中太郎 <taro@example.com>")

        Returns:
            tuple[str, str]: (送信者名, 送信者アドレス)
        """
        try:
            # email.utils.parseaddr を使用してパース
            name, address = parseaddr(sender_str)

            # 名前が空の場合はアドレスから@より前を使用
            if not name and address:
                name = address.split("@")[0]

            # アドレスが空の場合はデフォルト値
            if not address:
                address = "unknown@example.com"

        except (ValueError, AttributeError):
            # パースに失敗した場合はデフォルト値を返す
            return "送信者不明", "unknown@example.com"
        return name or "送信者不明", address

    def _decode_header(self, header: str) -> str:
        """メールヘッダーをデコード.

        Args:
            header: エンコードされたヘッダー文字列

        Returns:
            str: デコードされた文字列
        """
        if not header:
            return ""

        try:
            decoded_header = decode_header(header)
            result = ""
            for part, encoding in decoded_header:
                if isinstance(part, bytes):
                    result += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    result += part
        except (UnicodeDecodeError, LookupError):
            return str(header)
        return result

    def _parse_date(self, date_str: str) -> datetime | None:
        """日付文字列をdatetimeオブジェクトに変換.

        Args:
            date_str: RFC 2822形式の日付文字列

        Returns:
            datetime | None: パースされた日時
        """
        if not date_str:
            return None

        try:
            # RFC 2822形式の日付をパース
            parsed_time = parsedate_to_datetime(date_str)
            # タイムゾーン情報がない場合は現在のタイムゾーンを設定
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
        except (ValueError, OverflowError):
            # パースできない場合は現在時刻を返す
            return datetime.now().astimezone()
        return parsed_time

    def _extract_body(self, message: Message) -> tuple[str, str]:
        """メッセージから本文を抽出.

        Args:
            message: emailメッセージオブジェクト

        Returns:
            tuple[str, str]: (テキスト本文, HTML本文)
        """
        text_body = ""
        html_body = ""

        try:
            if message.is_multipart():
                # マルチパートメッセージの場合
                for part in message.walk():
                    content_type = part.get_content_type()

                    if content_type == "text/plain" and not text_body:
                        text_body = self._decode_payload(part)
                    elif content_type == "text/html" and not html_body:
                        html_body = self._decode_payload(part)
            else:
                # シングルパートメッセージの場合
                content_type = message.get_content_type()
                body = self._decode_payload(message)

                if content_type == "text/html":
                    html_body = body
                else:
                    text_body = body

        except (UnicodeDecodeError, AttributeError) as e:
            logger.warning("Failed to extract body: %s", e)

        return text_body, html_body

    def _decode_payload(self, part: Message) -> str:
        """メッセージパートのペイロードをデコード.

        Args:
            part: メッセージパート

        Returns:
            str: デコードされたテキスト
        """
        try:
            payload = part.get_payload(decode=True)
            if isinstance(payload, bytes):
                return payload.decode("utf-8", errors="ignore")
            return str(payload)
        except (UnicodeDecodeError, AttributeError):
            return ""

    def get_mails(self, count: int = 10, cursor_datetime: datetime | None = None) -> list[MailData]:
        """全メールボックスから新規メールを取得.

        Args:
            count (int): 取得するメールの数.デフォルトは10件.
            cursor_datetime (datetime | None): この時刻以降のメールのみ取得.

        Returns:
            list[MailData]: 取得したメールのリスト.
        """
        all_mails = []

        for mailbox_file in self.path.mailbox_files:
            try:
                mails = self._parse_mailbox_file(mailbox_file, count=count)

                # 日時フィルタリング
                if cursor_datetime:
                    filtered_mails = [mail for mail in mails if mail.received_at and mail.received_at > cursor_datetime]
                    all_mails.extend(filtered_mails)
                else:
                    all_mails.extend(mails)

            except (OSError, mailbox.Error) as e:
                logger.warning("Failed to get mails from %s: %s", mailbox_file, e)
                continue

        all_mails.sort(
            key=lambda x: x.received_at or datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo),
            reverse=True,
        )

        result = all_mails[:count]
        logger.info("Retrieved %d mails from %d mailboxes", len(result), len(self.path.mailbox_files))

        return result

    def get_mail(self, message_id: str) -> MailData | None:
        """指定されたメッセージIDのメールを取得.

        Args:
            message_id: 検索するメッセージID

        Returns:
            MailData | None: 見つかったメール、または None
        """
        # 全メールボックスファイルから検索
        for mailbox_file in self.path.mailbox_files:
            try:
                mbox = mailbox.mbox(str(mailbox_file))

                for message in mbox:
                    msg_id = message.get("Message-ID", "")
                    if msg_id == message_id:
                        return self._parse_single_mail(message)

            except (OSError, mailbox.Error) as e:
                logger.warning("Failed to search in %s: %s", mailbox_file, e)
                continue

        logger.info("Mail with message ID %s not found", message_id)
        return None


if __name__ == "__main__":
    # サンプルのThunderbirdConfigを作成してクライアントを初期化
    config = ThunderbirdConfig(connection_type="local")
    client = ThunderbirdClient(config)

    try:
        client.connect()
        logger.info("Mailbox files: %s", client.path.mailbox_files)

        # メール取得のテスト
        if client.path.mailbox_files:
            logger.info("Testing mail retrieval...")
            mails = client.get_mails(count=5)
            logger.info("Retrieved %d mails", len(mails))

            for i, mail in enumerate(mails, 1):
                subject = getattr(mail, "subject", "No Subject")
                sender_name = getattr(mail, "sender_name", "Unknown Sender")
                logger.info("Mail %d: %s from %s", i, subject, sender_name)

    except FileNotFoundError:
        logger.exception("Thunderbird not found")
    except Exception:
        logger.exception("Unexpected error occurred")
    finally:
        client.disconnect()
