#!/usr/bin/env python3
"""LangChainの利用可能性をチェック."""

import sys

from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from langchain_core.documents import Document
except ImportError:
    Document = None

try:
    from app.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)


def main() -> None:
    """LangChainの利用可能性をチェック."""
    logger.info("LangChain利用可能性チェック開始")

    if Document is None:
        logger.exception("❌ LangChain not available")
        logger.info("💡 対処方法: uv add langchain-core を実行してください")
        sys.exit(1)

    try:
        logger.info("✅ LangChain Document利用可能")
        logger.info("Document class: %s", Document)

        # 簡単な動作テスト
        test_doc = Document(
            page_content="テストコンテンツ",
            metadata={"source": "test", "type": "demo"},
        )
        logger.info("✅ Document作成テスト成功")
        logger.info("  page_content: %s", test_doc.page_content)
        logger.info("  metadata: %s", test_doc.metadata)

    except (TypeError, ValueError):
        logger.exception("❌ Document作成エラー")
        sys.exit(1)

    logger.info("✅ LangChainチェック完了 - 正常に利用可能です")


if __name__ == "__main__":
    main()
