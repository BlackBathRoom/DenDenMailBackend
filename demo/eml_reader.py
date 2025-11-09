"""デモEMLファイル読み込みユーティリティ."""

import email
import email.message
import logging
import sys

from pathlib import Path
from typing import Any

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    # ロガーが利用できない場合は標準ロガーを使用
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)


class DemoEMLReader:
    """デモEMLファイル読み込みクラス."""

    def __init__(self, eml_files_dir: Path | None = None) -> None:
        """初期化.

        Args:
            eml_files_dir: EMLファイルディレクトリ(デフォルト: demo/eml_files/)
        """
        self.eml_files_dir = eml_files_dir or Path(__file__).parent / "eml_files"
        self._validate_directory()

    def _validate_directory(self) -> None:
        """ディレクトリの存在確認."""
        if not self.eml_files_dir.exists():
            msg = f"EMLファイルディレクトリが存在しません: {self.eml_files_dir}"
            raise FileNotFoundError(msg)

    def _validate_file_exists(self, file_path: Path) -> None:
        """ファイルの存在確認."""
        if not file_path.exists():
            msg = f"EMLファイルが存在しません: {file_path}"
            raise FileNotFoundError(msg)

    def read_eml_file(self, file_path: Path) -> email.message.Message:
        """EMLファイルを読み込んでメールオブジェクトに変換.

        Args:
            file_path: EMLファイルのパス

        Returns:
            解析されたメールオブジェクト

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: ファイル解析に失敗した場合
        """
        try:
            self._validate_file_exists(file_path)

            # EMLファイルを読み込み
            with file_path.open("r", encoding="utf-8") as f:
                content = f.read()

            # emailオブジェクトに変換
            message = email.message_from_string(content)

        except UnicodeDecodeError as e:
            logger.exception("文字エンコードエラー: %s", file_path)
            msg = f"ファイルの文字エンコードが正しくありません: {e}"
            raise ValueError(msg) from e
        except OSError as e:
            logger.exception("EMLファイル読み込みエラー: %s", file_path)
            msg = f"EMLファイルの解析に失敗しました: {e}"
            raise ValueError(msg) from e
        else:
            logger.info("EMLファイルを読み込み: %s", file_path.name)
            return message

    def extract_mail_data(self, message: email.message.Message) -> dict[str, Any]:
        """メールオブジェクトからデータを抽出.

        Args:
            message: 解析されたメールオブジェクト

        Returns:
            抽出されたメールデータ
        """
        try:
            # ヘッダー情報を抽出
            subject = message.get("Subject", "件名なし")
            from_addr = message.get("From", "送信者不明")
            to_addr = message.get("To", "宛先不明")
            date_str = message.get("Date", "")
            message_id = message.get("Message-ID", "")

            # 本文を抽出
            body = ""
            if message.is_multipart():
                # マルチパートの場合
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or "utf-8"
                        payload = part.get_payload(decode=True)
                        body = payload.decode(charset, errors="replace") if isinstance(payload, bytes) else str(payload)
                        break
            elif message.get_content_type() == "text/plain":
                # シンプルなテキストの場合
                charset = message.get_content_charset() or "utf-8"
                payload = message.get_payload(decode=True)
                body = payload.decode(charset, errors="replace") if isinstance(payload, bytes) else str(payload)

            # データ辞書を作成
            mail_data = {
                "subject": subject,
                "sender": from_addr,
                "recipient": to_addr,
                "date": date_str,
                "message_id": message_id,
                "body": body,
                "content_type": message.get_content_type(),
            }

        except (AttributeError, TypeError, UnicodeDecodeError) as e:
            logger.exception("メールデータ抽出エラー")
            msg = f"メールデータの抽出に失敗しました: {e}"
            raise ValueError(msg) from e
        else:
            logger.debug("メールデータを抽出: 件名='%s'", subject[:50])
            return mail_data

    def read_all_demo_files(self) -> list[dict[str, Any]]:
        """全てのデモEMLファイルを読み込み.

        Returns:
            全メールデータのリスト
        """
        mail_data_list = []

        # EMLファイルを検索
        eml_files = list(self.eml_files_dir.glob("*.eml"))

        if not eml_files:
            logger.warning("EMLファイルが見つかりません: %s", self.eml_files_dir)
            return []

        # 各ファイルを処理
        for eml_file in sorted(eml_files):
            try:
                # EMLファイル読み込み
                message = self.read_eml_file(eml_file)

                # データ抽出
                mail_data = self.extract_mail_data(message)
                mail_data["file_name"] = eml_file.name

                mail_data_list.append(mail_data)

            except (FileNotFoundError, ValueError, OSError):
                logger.exception("ファイル処理エラー: %s", eml_file)
                # エラーがあっても他のファイルは続行
                continue

        logger.info("デモEMLファイル読み込み完了: %d件", len(mail_data_list))
        return mail_data_list

    def get_available_files(self) -> list[Path]:
        """利用可能なEMLファイル一覧を取得.

        Returns:
            EMLファイルパスのリスト
        """
        eml_files = list(self.eml_files_dir.glob("*.eml"))
        return sorted(eml_files)


def main() -> None:
    """メイン処理 - デモ用."""
    logger.info("デモEMLファイル読み込み開始!")

    try:
        reader = DemoEMLReader()

        # 利用可能ファイル一覧を表示
        available_files = reader.get_available_files()
        logger.info("利用可能なEMLファイル: %d件", len(available_files))
        for file_path in available_files:
            file_size = file_path.stat().st_size
            logger.info("  - %s (%d bytes)", file_path.name, file_size)

        # 全ファイルを読み込み
        mail_data_list = reader.read_all_demo_files()

        logger.info("読み込み完了: %d件", len(mail_data_list))

        # 各メールの概要を表示
        logger.info("読み込まれたメールの概要:")
        for i, mail_data in enumerate(mail_data_list, 1):
            logger.info("  %d. %s", i, mail_data["file_name"])
            logger.info("     件名: %s", mail_data["subject"])
            logger.info("     送信者: %s", mail_data["sender"])
            logger.info("     本文サイズ: %d 文字", len(mail_data["body"]))
            body_preview = mail_data["body"][:100].replace("\n", " ")
            logger.info("     本文プレビュー: %s...", body_preview)

        logger.info("デモEMLファイル読み込み完了!")

    except (FileNotFoundError, ValueError, OSError):
        logger.exception("デモEMLファイル読み込みでエラーが発生")
        raise


if __name__ == "__main__":
    main()
