"""OpenVINO RURI_v3埋め込みサービス基本テスト."""

import logging
import sys

from pathlib import Path

from app.services.ai.rag.embedding.openvino_ruri_v3_embedding import (
    create_openvino_embedding_service,
)

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)


def test_openvino_basic_embedding() -> bool:
    """基本的なOpenVINO埋め込みテスト."""
    logger.info("OpenVINO基本埋め込みテスト開始")

    service = None
    try:
        # サービス初期化
        service = create_openvino_embedding_service()

        # テストドキュメント
        test_doc = """
        件名: OpenVINO最適化テスト
        送信者: test@example.com

        このドキュメントはOpenVINO最適化されたRURI_v3モデルの
        ベクトル化性能をテストするためのサンプルです。
        """

        # ベクトル化実行
        vector = service.embed_document(test_doc)

        logger.info("✅ 基本埋め込み成功: %d次元", len(vector))
        logger.info("ベクトル値サンプル: [%.4f, %.4f, %.4f]", vector[0], vector[1], vector[2])

    except (ValueError, RuntimeError, ImportError):
        logger.exception("❌ 基本テスト失敗")
        return False
    else:
        return True
    finally:
        if service:
            service.cleanup()


def test_openvino_batch_processing() -> bool:
    """バッチ処理テスト."""
    logger.info("OpenVINOバッチ処理テスト開始")

    service = None
    try:
        service = create_openvino_embedding_service()

        # 複数ドキュメント
        documents = [
            "件名: テスト1\n本文: 最初のテストドキュメントです。",
            "件名: テスト2\n本文: 2番目のテストドキュメントです。",
            "件名: テスト3\n本文: 3番目のテストドキュメントです。",
        ]

        # バッチベクトル化
        vectors = service.embed_documents(documents)

        logger.info("✅ バッチ処理成功: %d件処理", len(vectors))
        for i, vec in enumerate(vectors):
            logger.info("  ドキュメント%d: %d次元", i + 1, len(vec))

    except (ValueError, RuntimeError, ImportError):
        logger.exception("❌ バッチテスト失敗")
        return False
    else:
        return True
    finally:
        if service:
            service.cleanup()


def test_openvino_performance_benchmark() -> bool:
    """性能ベンチマークテスト."""
    logger.info("OpenVINO性能ベンチマークテスト開始")

    service = None
    try:
        service = create_openvino_embedding_service()

        # 性能ベンチマーク実行
        test_docs = [
            "テストドキュメント1: 性能測定用のサンプルテキストです。",
            "テストドキュメント2: ベンチマーク用のテストデータです。",
        ]
        benchmark_result = service.benchmark_performance(sample_documents=test_docs)

        logger.info("✅ 性能ベンチマーク成功")
        logger.info("  単一処理: %.2f docs/sec", benchmark_result["single_processing"]["throughput"])
        for batch_size, perf in benchmark_result["batch_performance"].items():
            logger.info("  バッチサイズ %d: %.2f docs/sec", batch_size, perf["throughput"])

    except (ValueError, RuntimeError, ImportError):
        logger.exception("❌ 性能ベンチマークテスト失敗")
        return False
    else:
        return True
    finally:
        if service:
            service.cleanup()


def run_all_tests() -> None:
    """全テストを実行."""
    logger.info("=== OpenVINO RURI_v3埋め込みサービステスト開始 ===")

    tests = [
        ("基本埋め込みテスト", test_openvino_basic_embedding),
        ("バッチ処理テスト", test_openvino_batch_processing),
        ("性能ベンチマークテスト", test_openvino_performance_benchmark),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info("\n--- %s ---", test_name)
        if test_func():
            passed += 1

    logger.info("\n=== テスト結果 ===")
    logger.info("合格: %d/%d", passed, total)

    if passed == total:
        logger.info("🎉 すべてのテストが成功しました!")
    else:
        logger.warning("⚠️ 一部のテストが失敗しました")


if __name__ == "__main__":
    run_all_tests()
