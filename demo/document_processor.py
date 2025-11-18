"""EMLデータをLangChain Documentに変換するためのユーティリティ."""

import email.header
import re

from email.utils import parsedate_to_datetime
from typing import Any

from langchain_core.documents import Document


class EMLDocumentProcessor:
    """EMLデータをLangChainのDocumentオブジェクトに変換するプロセッサー."""

    def __init__(self) -> None:
        """初期化."""

    def format_page_content(self, mail_data: dict[str, Any]) -> str:
        """Step 1-4: メールデータからpage_contentを整形.

        Args:
            mail_data: EMLリーダーから取得したメールデータ

        Returns:
            整形されたpage_content文字列
        """
        try:
            # 件名のデコード処理
            subject = self._decode_header(mail_data.get("subject", "件名なし"))

            # 送信者・受信者の整形
            sender = mail_data.get("sender", "送信者不明")
            recipient = mail_data.get("recipient", "受信者不明")

            # 日付の整形
            date_str = mail_data.get("date", "")
            formatted_date = self._format_date(date_str)

            # 本文の整形
            body = mail_data.get("body", "")
            formatted_body = self._clean_body_text(body)

            # page_contentを構築
            page_content_parts = [
                f"件名: {subject}",
                f"送信者: {sender}",
                f"受信者: {recipient}",
                f"日付: {formatted_date}",
                "",
                "本文:",
                formatted_body,
            ]

        except (KeyError, TypeError, ValueError, AttributeError) as e:
            error_msg = f"page_content整形エラー: {e}"
            return f"エラー: メールデータの整形に失敗しました\n{error_msg}"
        else:
            return "\n".join(page_content_parts)

    def create_document(self, mail_data: dict[str, Any]) -> Document:
        """Step 1-5: LangChain Documentオブジェクトを作成.

        Args:
            mail_data: EMLリーダーから取得したメールデータ

        Returns:
            LangChainのDocumentオブジェクト
        """
        try:
            # page_contentを整形
            page_content = self.format_page_content(mail_data)

            # メタデータを構築
            metadata = self._build_metadata(mail_data)

        except (KeyError, TypeError, ValueError, AttributeError) as e:
            # エラー時でもDocumentオブジェクトを返す
            error_content = f"Document作成エラー: {e}"
            error_metadata = {
                "error": True,
                "error_message": str(e),
                "file_name": mail_data.get("file_name", "unknown"),
            }
            return Document(
                page_content=error_content,
                metadata=error_metadata,
            )
        else:
            # Documentオブジェクトを作成
            return Document(
                page_content=page_content,
                metadata=metadata,
            )

    def process_mail_list(self, mail_data_list: list[dict[str, Any]]) -> list[Document]:
        """複数のメールデータをまとめてDocumentリストに変換.

        Args:
            mail_data_list: EMLリーダーから取得したメールデータのリスト

        Returns:
            LangChain Documentオブジェクトのリスト
        """
        documents = []

        for i, mail_data in enumerate(mail_data_list, 1):
            try:
                document = self.create_document(mail_data)
                documents.append(document)
            except (KeyError, TypeError, ValueError, AttributeError) as e:
                # 個別のエラーは無視して処理を続行
                error_doc = Document(
                    page_content=f"処理エラー (メール {i}): {e}",
                    metadata={
                        "error": True,
                        "error_message": str(e),
                        "mail_index": i,
                    },
                )
                documents.append(error_doc)

        return documents

    def _decode_header(self, header_value: str) -> str:
        """メールヘッダーのデコード(Base64など)."""
        try:
            # email.headerのdecode_headerを使用
            decoded_parts = email.header.decode_header(header_value)
            decoded_text = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    # バイト列の場合はデコード
                    if encoding:
                        decoded_text += part.decode(encoding, errors="replace")
                    else:
                        decoded_text += part.decode("utf-8", errors="replace")
                else:
                    # 文字列の場合はそのまま
                    decoded_text += part

            return decoded_text.strip()

        except (UnicodeDecodeError, LookupError, ValueError):
            # デコードに失敗した場合は元の文字列を返す
            return header_value

    def _format_date(self, date_str: str) -> str:
        """日付文字列を読みやすい形式に変換."""
        if not date_str:
            return "日付不明"

        try:
            # email.utilsのparsedate_to_datetimeを使用
            parsed_date = parsedate_to_datetime(date_str)
            return parsed_date.strftime("%Y年%m月%d日 %H:%M:%S")
        except (ValueError, TypeError, OverflowError):
            # パースに失敗した場合は元の文字列を返す
            return date_str

    def _clean_body_text(self, body: str) -> str:
        """本文テキストをクリーニング."""
        if not body:
            return "本文なし"

        # 改行の正規化
        body_normalized = re.sub(r"\r\n", "\n", body)
        body_normalized = re.sub(r"\r", "\n", body_normalized)

        # 連続する空行を削除
        body_normalized = re.sub(r"\n{3,}", "\n\n", body_normalized)

        # 前後の空白を削除
        return body_normalized.strip()

    def _build_metadata(self, mail_data: dict[str, Any]) -> dict[str, Any]:
        """メールデータからメタデータを構築."""
        metadata = {
            "source": "eml_file",
            "file_name": mail_data.get("file_name", "unknown"),
            "message_id": mail_data.get("message_id", ""),
            "content_type": mail_data.get("content_type", ""),
        }

        # 件名を取得してデコード
        subject = self._decode_header(mail_data.get("subject", ""))
        if subject:
            metadata["subject"] = subject

        # 送信者・受信者
        if mail_data.get("sender"):
            metadata["sender"] = mail_data["sender"]
        if mail_data.get("recipient"):
            metadata["recipient"] = mail_data["recipient"]

        # 日付
        date_str = mail_data.get("date", "")
        if date_str:
            metadata["date_raw"] = date_str
            formatted_date = self._format_date(date_str)
            metadata["date_formatted"] = formatted_date

        # 本文の長さ
        body_length = len(mail_data.get("body", ""))
        metadata["body_length"] = body_length

        return metadata
