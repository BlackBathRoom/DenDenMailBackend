"""EML読み込み機能とcon_thunderbird.pyの統合テスト."""

import logging
import sys

from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "demo"))

# ローカルモジュールのインポート
try:
    from document_processor import EMLDocumentProcessor  # type: ignore[import-untyped]
    from eml_reader import DemoEMLReader  # type: ignore[import-untyped]
    from generator import DemoEMLGenerator  # type: ignore[import-untyped]
except ImportError:
    # モジュールが見つからない場合はNoneに設定
    DemoEMLReader = None
    DemoEMLGenerator = None
    EMLDocumentProcessor = None

try:
    from app.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    # ロガーが利用できない場合は標準ロガーを使用
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

try:
    from study.con_thunderbird import get_mails_from_all_accounts
except ImportError:
    get_mails_from_all_accounts = None


def _raise_validation_error(message: str) -> None:
    """バリデーションエラーを発生させるヘルパー関数."""
    raise ValueError(message)


def _raise_import_error(message: str) -> None:
    """インポートエラーを発生させるヘルパー関数."""
    raise ImportError(message)


def test_document_conversion(mail_data_list: list[dict]) -> None:
    """Document変換テスト(Step 1-4, 1-5の実装)."""
    logger.info("5. Document変換テスト...")
    try:
        # グローバルにインポートされたEMLDocumentProcessorを使用
        if EMLDocumentProcessor is None:
            logger.warning("EMLDocumentProcessorがインポートできません")
            return

        processor = EMLDocumentProcessor()

        # Step 1-4: page_content整形テスト
        logger.info("   1-4: page_content整形テスト")
        for i, mail_data in enumerate(mail_data_list[:2], 1):  # 最初の2件をテスト
            page_content = processor.format_page_content(mail_data)
            logger.info("     メール %d page_content長: %d文字", i, len(page_content))
            # page_contentの先頭100文字を表示
            preview = page_content[:100].replace("\n", " ")
            logger.info("     プレビュー: %s...", preview)

        # Step 1-5: Document作成テスト
        logger.info("   1-5: Document作成テスト")
        documents = processor.process_mail_list(mail_data_list)
        logger.info("     作成されたDocument数: %d件", len(documents))

        # Documentの詳細を表示
        for i, doc in enumerate(documents[:2], 1):  # 最初の2件をテスト
            logger.info("     Document %d:", i)
            logger.info("       page_content長: %d文字", len(doc.page_content))
            logger.info("       メタデータ数: %d項目", len(doc.metadata))
            logger.info("       件名: %s", doc.metadata.get("subject", "N/A"))
            logger.info("       送信者: %s", doc.metadata.get("sender", "N/A"))
            logger.info("       エラー有無: %s", doc.metadata.get("error", False))

        logger.info("   Document変換テスト完了!")

    except ImportError as e:
        logger.warning("Document変換テストをスキップ: %s", e)
    except Exception:
        logger.exception("Document変換テストでエラーが発生")


def test_eml_generation_and_reading() -> None:
    """EML生成と読み込みの統合テスト."""
    logger.info("EML生成・読み込み統合テスト開始")

    # 必要なクラスがインポートできているかチェック
    if DemoEMLGenerator is None or DemoEMLReader is None:
        logger.error("必要なモジュールがインポートできません")
        logger.error("DemoEMLGenerator: %s, DemoEMLReader: %s", DemoEMLGenerator, DemoEMLReader)
        return

    try:
        # Step 1: EMLファイル生成
        logger.info("1. EMLファイル生成...")
        generator = DemoEMLGenerator()
        generated_files = generator.generate_all_demo_files()
        logger.info("   生成完了: %d件", len(generated_files))

        # Step 2: EMLファイル読み込み
        logger.info("2. EMLファイル読み込み...")
        reader = DemoEMLReader()
        mail_data_list = reader.read_all_demo_files()
        logger.info("   読み込み完了: %d件", len(mail_data_list))

        # Step 3: データ検証
        logger.info("3. データ検証...")
        if len(generated_files) != len(mail_data_list):
            msg = "生成ファイル数と読み込みファイル数が一致しません"
            _raise_validation_error(msg)

        for mail_data in mail_data_list:
            # 必須フィールドの存在確認
            required_fields = ["subject", "sender", "recipient", "body", "message_id"]
            for field in required_fields:
                if field not in mail_data:
                    msg = f"必須フィールド '{field}' が見つかりません"
                    _raise_validation_error(msg)
                if not mail_data[field]:
                    msg = f"フィールド '{field}' が空です"
                    _raise_validation_error(msg)

            # 日本語文字の確認
            body_contains_expected = any(
                keyword in mail_data["body"] for keyword in ["プロジェクト", "システム", "新機能"]
            )
            if not body_contains_expected:
                msg = "期待する日本語コンテンツが見つかりません"
                _raise_validation_error(msg)

        logger.info("   全データ検証OK")

        # Step 4: 詳細情報表示
        logger.info("4. 読み込みデータ詳細:")
        for i, mail_data in enumerate(mail_data_list, 1):
            logger.info("   メール %d: %s", i, mail_data["file_name"])
            logger.info("      件名: %s", mail_data["subject"])
            logger.info("      送信者: %s", mail_data["sender"])
            logger.info("      Message-ID: %s", mail_data["message_id"])
            logger.info("      本文長: %d 文字", len(mail_data["body"]))

        logger.info("統合テスト完了! 全て正常に動作しています。")

        # Step 5: Document変換テスト(1-4, 1-5の実装)
        test_document_conversion(mail_data_list)

    except Exception:
        logger.exception("統合テストでエラーが発生")
        raise


def test_con_thunderbird_compatibility() -> None:
    """con_thunderbird.pyとの互換性テスト."""
    logger.info("con_thunderbird.py互換性テスト開始")

    try:
        # con_thunderbird.pyをインポート
        if get_mails_from_all_accounts is None:
            logger.warning("con_thunderbird.pyがインポートできません")
            logger.info("study/con_thunderbird.pyが存在することを確認してください")
            return

        # DemoEMLReaderがインポートできているかチェック
        if DemoEMLReader is None:
            logger.error("DemoEMLReaderがインポートできません")
            return

        reader = DemoEMLReader()
        mail_data_list = reader.read_all_demo_files()

        logger.info("%d件のメールでcon_thunderbird.py互換性をテスト", len(mail_data_list))

        for i, mail_data in enumerate(mail_data_list, 1):
            try:
                # EMLファイルから直接emailオブジェクトを作成
                eml_file = reader.eml_files_dir / mail_data["file_name"]
                message = reader.read_eml_file(eml_file)

                # 基本的な互換性確認を実行
                if message.get("Subject") is None:
                    msg = "件名が取得できません"
                    _raise_validation_error(msg)
                if message.get("From") is None:
                    msg = "送信者が取得できません"
                    _raise_validation_error(msg)
                if message.get("Message-ID") is None:
                    msg = "Message-IDが取得できません"
                    _raise_validation_error(msg)

                logger.info("   メール %d (%s): OK", i, mail_data["file_name"])

            except Exception:
                logger.exception("メール %d (%s) でエラーが発生", i, mail_data["file_name"])
                raise

        logger.info("con_thunderbird.py互換性テスト完了!")

    except Exception:
        logger.exception("互換性テストでエラーが発生")
        raise


def main() -> None:
    """メイン処理."""
    logger.info("デモEMLファイル統合テスト開始!")

    try:
        # 基本的な生成・読み込みテスト
        test_eml_generation_and_reading()

        # con_thunderbird.py互換性テスト
        test_con_thunderbird_compatibility()

        logger.info("全てのテストが正常に完了しました!")
        logger.info("次のステップ: ベクトル化機能の実装に進めます。")

    except Exception:
        logger.exception("統合テストの実行中にエラーが発生")
        sys.exit(1)


if __name__ == "__main__":
    main()
