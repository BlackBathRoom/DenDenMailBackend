"""Document変換の詳細テスト - 生成されたpage_contentとメタデータの確認."""

import sys

from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ローカルモジュールのインポート
try:
    from document_processor import EMLDocumentProcessor  # type: ignore[import-untyped]
    from eml_reader import DemoEMLReader  # type: ignore[import-untyped]
    from generator import DemoEMLGenerator  # type: ignore[import-untyped]
except ImportError:
    EMLDocumentProcessor = None  # type: ignore[assignment]
    DemoEMLReader = None  # type: ignore[assignment]
    DemoEMLGenerator = None  # type: ignore[assignment]

try:
    from app.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)


def main() -> None:
    """Document変換の詳細テスト."""
    logger.info("Document変換詳細テスト開始")

    # 必要なクラスがインポートできているかチェック
    if DemoEMLGenerator is None or DemoEMLReader is None or EMLDocumentProcessor is None:
        logger.error("必要なモジュールがインポートできません")
        logger.error("DemoEMLGenerator: %s", DemoEMLGenerator)
        logger.error("DemoEMLReader: %s", DemoEMLReader)
        logger.error("EMLDocumentProcessor: %s", EMLDocumentProcessor)
        return

    try:
        # EMLファイル生成と読み込み
        generator = DemoEMLGenerator()
        generator.generate_all_demo_files()

        reader = DemoEMLReader()
        mail_data_list = reader.read_all_demo_files()

        # Document変換テスト
        processor = EMLDocumentProcessor()

        # 1件目のメールで詳細テスト
        first_mail = mail_data_list[0]
        logger.info("=== メール詳細 ===")
        logger.info("ファイル名: %s", first_mail["file_name"])
        logger.info("元の件名: %s", first_mail["subject"])
        logger.info("送信者: %s", first_mail["sender"])
        logger.info("本文長: %d文字", len(first_mail["body"]))

        # Step 1-4: page_content整形
        page_content = processor.format_page_content(first_mail)
        logger.info("\n=== Step 1-4: 整形されたpage_content ===")
        logger.info("page_content長: %d文字", len(page_content))
        logger.info("page_content内容:")
        logger.info("---")
        logger.info("%s", page_content)
        logger.info("---")

        # Step 1-5: Document作成
        document = processor.create_document(first_mail)
        logger.info("\n=== Step 1-5: 作成されたDocument ===")
        logger.info("Document.page_content長: %d文字", len(document.page_content))
        logger.info("Document.metadata:")
        for key, value in document.metadata.items():
            logger.info("  %s: %s", key, value)

        # page_contentとDocumentのpage_contentが一致するか確認
        content_match = page_content == document.page_content
        logger.info("\npage_content一致確認: %s", content_match)

        logger.info("\nDocument変換詳細テスト完了!")

    except (TypeError, ValueError, KeyError, AttributeError):
        logger.exception("Document変換詳細テストでエラーが発生")
        raise


if __name__ == "__main__":
    main()
