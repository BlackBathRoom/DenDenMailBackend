"""Thunderbirdメールクライアントの実装."""

import mailbox

from datetime import datetime
from email.errors import MessageError
from email.header import decode_header
from email.message import Message
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from pathlib import Path

from pydantic import ValidationError

from app_conf import MailVendor
from services.mail.base import (
    BaseClientConfig,
    BaseMailClient,
    MessageAddressData,
    MessageData,
    MessagePartData,
)
from services.mail.thunderbird.thunderbird_path import ThunderbirdPath
from utils.logging import get_logger

logger = get_logger(__name__)

ALL_GET_MAILS_COUNT = -1


class ThunderbirdConfig(BaseClientConfig):
    """Thunderbirdメールクライアントの設定情報."""


class ThunderbirdClient(BaseMailClient[ThunderbirdConfig]):
    """Thunderbirdメールクライアントの実装."""

    def __init__(self, config: ThunderbirdConfig | None = None) -> None:
        if config is None:
            config = {"connection_type": "local"}
        super().__init__(config)
        self.path = ThunderbirdPath()

    def connect(self) -> None:
        """Thunderbirdクライアントはローカルファイルシステムを使用するため、特に接続処理は不要."""
        logger.info("Connected to Thunderbird client.")

    def disconnect(self) -> None:
        """Thunderbirdクライアントはローカルファイルシステムを使用するため、特に切断処理は不要."""
        logger.info("Disconnected from Thunderbird client.")

    def _parse_mailbox_file(self, file_path: Path, count: int = 10) -> list[MessageData]:
        """メールボックスファイルからメールをパースして取得.

        Args:
            file_path: メールボックスファイルのパス
            count: 取得するメール数

        Returns:
            list[MessageData]: パースされたメールのリスト
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

            for i, message in enumerate(messages[: count if count == ALL_GET_MAILS_COUNT else None]):
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

    def _parse_single_mail(self, message: Message) -> MessageData | None:
        """単一メールメッセージをパースしてMessageDataに変換.

        Args:
            message: emailメッセージオブジェクト

        Returns:
            MessageData | None: パースされたメールデータ
        """
        mail_data = None
        try:
            subject = self._decode_header(message.get("Subject", "件名なし"))
            date_header = self._decode_header(message.get("Date", ""))
            date_sent = self._parse_date(date_header)
            date_received = date_sent or datetime.now().astimezone()
            rfc822_message_id = message.get("Message-ID", "")

            parts = self._extract_parts(message)

            # アドレス抽出
            addrs = self._parse_addresses(message)

            # MailDataオブジェクト作成
            mail_data = MessageData(
                rfc822_message_id=rfc822_message_id,
                subject=subject,
                date_sent=date_sent,
                date_received=date_received,
                in_reply_to=self._decode_header(message.get("In-Reply-To", "")) or None,
                references_list=self._decode_header(message.get("References", "")) or None,
                is_read=False,
                is_replied=False,
                is_flagged=False,
                is_forwarded=False,
                vendor_id=0,  # db登録時に設定
                folder_id=None,  # db登録時に設定
                mail_vendor=MailVendor.THUNDERBIRD,
                parts=parts,
                from_addrs=addrs.get("from", []),
                to_addrs=addrs.get("to", []),
                cc_addrs=addrs.get("cc", []),
                bcc_addrs=addrs.get("bcc", []),
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

    def _parse_addresses(self, message: Message) -> dict[str, list[MessageAddressData]]:
        """ヘッダから From/To/Cc/Bcc のアドレスを抽出して返す.

        Returns:
            dict[str, list[MessageAddressData]]: keys are 'from', 'to', 'cc', 'bcc'.
        """

        def norm(addr: tuple[str, str]) -> MessageAddressData | None:
            name, email = addr
            email = (email or "").strip().lower()
            if not email or "@" not in email:
                return None
            name = (name or "").strip()
            try:
                return MessageAddressData(email_address=email, display_name=name or None)
            except ValidationError as ve:
                logger.debug("Invalid email address skipped: raw=%r error=%s", addr, ve)
                return None

        result: dict[str, list[MessageAddressData]] = {"from": [], "to": [], "cc": [], "bcc": []}
        # From は単数または複数あり得る
        from_list = getaddresses(message.get_all("From", []))
        to_list = getaddresses(message.get_all("To", []))
        cc_list = getaddresses(message.get_all("Cc", []))
        bcc_list = getaddresses(message.get_all("Bcc", []))

        for key, lst in (("from", from_list), ("to", to_list), ("cc", cc_list), ("bcc", bcc_list)):
            seen: set[str] = set()
            for raw in lst:
                item = norm(raw)
                if item is None:
                    continue
                if item.email_address in seen:
                    continue
                seen.add(item.email_address)
                result[key].append(item)

        return result

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

    def _extract_parts(self, message: Message) -> list[MessagePartData]:
        """メッセージからMIMEパーツを抽出して配列で返す.

        ネスト構造はフラットにしつつ、各要素に parent_part_order を付与する。
        multipart コンテナ自体も要素として出力するが、payload は持たない。
        """
        parts: list[MessagePartData] = []
        order = 0

        def walk(node: Message, parent_order: int | None) -> None:
            nonlocal order, parts
            try:
                if node.is_multipart():
                    # コンテナとして自身も追加 (payload は無し)
                    container = self._to_part_data(node, order)
                    container.content = None
                    container.is_attachment = False if container.is_attachment is None else container.is_attachment
                    container.parent_part_order = parent_order
                    parts.append(container)
                    current_order = order
                    order += 1

                    children = node.get_payload()
                    if isinstance(children, list):
                        for child in children:
                            # 再帰で子要素を処理 (Message のみ対象)
                            if isinstance(child, Message):
                                walk(child, current_order)
                else:
                    leaf = self._to_part_data(node, order)
                    leaf.parent_part_order = parent_order
                    parts.append(leaf)
                    order += 1
            except (UnicodeDecodeError, AttributeError, LookupError, ValueError) as e:
                logger.warning("Failed to process MIME node: %s", e)

        walk(message, None)
        return parts

    def _to_part_data(self, node: Message, order: int) -> MessagePartData:
        """email.message.Message から MessagePartData を生成する共通処理."""
        content_type = node.get_content_type() or "application/octet-stream"
        split_ct = content_type.split("/", 1)
        mime_type = split_ct[0] if len(split_ct) > 0 else None
        mime_subtype = split_ct[1] if len(split_ct) > 1 else None
        filename = node.get_filename()
        content_id_raw = node.get("Content-ID")
        content_id = content_id_raw.strip("<>") if content_id_raw else None
        content_disposition = node.get_content_disposition() or node.get("Content-Disposition")
        payload = node.get_payload(decode=True)
        size_bytes = len(payload) if isinstance(payload, (bytes, bytearray)) else None
        is_attachment = (content_disposition == "attachment") or (filename is not None)

        return MessagePartData(
            mime_type=mime_type,
            mime_subtype=mime_subtype,
            filename=filename,
            content_id=content_id,
            content_disposition=content_disposition,
            content=bytes(payload) if isinstance(payload, (bytes, bytearray)) else None,
            part_order=order,
            is_attachment=is_attachment,
            size_bytes=size_bytes,
        )

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

    def get_mails(self, count: int = 10, cursor_datetime: datetime | None = None) -> list[MessageData]:
        """全メールボックスから新規メールを取得.

        Args:
            count (int): 取得するメールの数.デフォルトは10件.-1は全件取得.
            cursor_datetime (datetime | None): この時刻以降のメールのみ取得.

        Returns:
            list[MessageData]: 取得したメールのリスト.
        """
        all_mails = []

        if count < ALL_GET_MAILS_COUNT or count == 0:
            msg = "Count must be -1 (all) or a positive integer"
            logger.error(msg)
            raise ValueError(msg)

        for mailbox_file in self.path.mailbox_files:
            try:
                mails = self._parse_mailbox_file(mailbox_file, count=count)

                # 日時フィルタリング
                if cursor_datetime:
                    filtered_mails = [
                        mail for mail in mails if mail.date_received and mail.date_received > cursor_datetime
                    ]
                    all_mails.extend(filtered_mails)
                else:
                    all_mails.extend(mails)

            except (OSError, mailbox.Error) as e:
                logger.warning("Failed to get mails from %s: %s", mailbox_file, e)
                continue

        all_mails.sort(
            key=lambda x: x.date_received or datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo),
            reverse=True,
        )

        result = all_mails[:count]
        logger.info("Retrieved %d mails from %d mailboxes", len(result), len(self.path.mailbox_files))

        return result

    def get_mail(self, message_id: str) -> MessageData | None:
        """指定されたメッセージIDのメールを取得.

        Args:
            message_id: 検索するメッセージID

        Returns:
            MessageData | None: 見つかったメール、または None
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

        # 最新メール1件の取得テスト (MessageData の表示)
        if client.path.mailbox_files:
            logger.info("Testing latest mail retrieval...")
            mails = client.get_mails(count=1)
            if not mails:
                logger.info("No mails found.")
            else:
                mail = mails[0]
                if mail.date_sent is not None:
                    logger.info("  date_sent=%s", mail.date_sent.isoformat())
                if mail.in_reply_to:
                    logger.info("  in_reply_to=%s", mail.in_reply_to)
                if mail.references_list:
                    logger.info("  references=%s", mail.references_list)

                parts = mail.parts
                logger.info("  parts=%d", len(parts))
                for p in parts:
                    ct_main = p.mime_type
                    ct_sub = p.mime_subtype
                    ct = "/".join([x for x in (ct_main, ct_sub) if x]) or "unknown"
                    logger.info(
                        "    - order=%s parent=%s type=%s filename=%s size=%s attach=%s content=%s",
                        p.part_order,
                        p.parent_part_order,
                        ct,
                        p.filename or "-",
                        p.size_bytes,
                        p.is_attachment,
                        "yes" if p.content else "no",
                    )

                # Body preview from parts (prefer text/plain, fallback to text/html)
                text_part = next(
                    (
                        pp
                        for pp in parts
                        if (pp.is_attachment is False or pp.is_attachment is None)
                        and pp.mime_type == "text"
                        and (pp.mime_subtype or "").lower() == "plain"
                    ),
                    None,
                )
                html_part = next(
                    (
                        pp
                        for pp in parts
                        if (pp.is_attachment is False or pp.is_attachment is None)
                        and pp.mime_type == "text"
                        and (pp.mime_subtype or "").lower() == "html"
                    ),
                    None,
                )
                body_bytes = (text_part.content if text_part and text_part.content else None) or (
                    html_part.content if html_part and html_part.content else None
                )
                if body_bytes:
                    try:
                        body_text = body_bytes.decode("utf-8", errors="ignore")
                    except UnicodeDecodeError:
                        body_text = str(body_bytes)
                    PREVIEW_LIMIT = 500
                    preview = (
                        body_text[:PREVIEW_LIMIT] + ("..." if len(body_text) > PREVIEW_LIMIT else "")
                        if body_text
                        else ""
                    )
                    logger.info("  body_preview=%s", preview)
                else:
                    logger.info("  body_preview=(none)")

    except FileNotFoundError:
        logger.exception("Thunderbird not found")
    except Exception:
        logger.exception("Unexpected error occurred")
    finally:
        client.disconnect()
