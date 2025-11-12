"""統合RAGサービス - load_model.pyシステムを活用したベクトル化とクエリ抽出."""

from typing import TYPE_CHECKING

from app.utils.logging import get_logger

# 統合サービス用インポート
if TYPE_CHECKING:
    from app.services.ai.rag.embedding.openvino_ruri_v3_embedding import EnhancedEmbeddingService
    from app.services.ai.rag.query.query_extraction import QueryExtractionService

# ランタイムでのインポート
try:
    from app.services.ai.rag.embedding.openvino_ruri_v3_embedding import (
        EnhancedEmbeddingService as _EnhancedEmbeddingService,
    )
    from app.services.ai.rag.query.query_extraction import (
        QueryExtractionService as _QueryExtractionService,
    )

    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    _EnhancedEmbeddingService = None
    _QueryExtractionService = None

logger = get_logger(__name__)


class EnhancedRAGService:
    """load_model.pyシステムを活用した統合RAGサービス.

    クエリ抽出、ドキュメント・クエリのベクトル化を統合的に提供します。
    YAGNIに従い、コア機能のみ実装しています。
    """

    def __init__(self, model_type: str = "RURI_V3_30M") -> None:
        """サービスを初期化します.

        Args:
            model_type: 使用するモデルタイプ("RURI_V3_30M" または "RURI_V3_130M")
        """
        if not SERVICES_AVAILABLE or _EnhancedEmbeddingService is None or _QueryExtractionService is None:
            msg = "必要なサービスクラスが利用できません"
            raise ImportError(msg)

        self.embedding_service: EnhancedEmbeddingService = _EnhancedEmbeddingService(model_type)
        self.query_service: QueryExtractionService = _QueryExtractionService()
        self.logger = get_logger(__name__)

        self.logger.info("EnhancedRAGService初期化完了 (モデル: %s)", model_type)

    def extract_keywords(self, text: str, max_keywords: int = 10) -> list[str]:
        """テキストからキーワードを抽出します.

        Args:
            text: キーワード抽出対象のテキスト
            max_keywords: 最大キーワード数

        Returns:
            抽出されたキーワードのリスト
        """
        return self.query_service.extract_keywords(text, max_keywords)

    def generate_search_query(self, text: str, max_keywords: int = 5) -> str:
        """テキストから検索クエリを生成します.

        Args:
            text: 検索クエリ生成対象のテキスト
            max_keywords: 使用する最大キーワード数

        Returns:
            生成された検索クエリ
        """
        return self.query_service.generate_search_query(text, max_keywords)

    def embed_query(self, query: str) -> list[float]:
        """クエリをベクトル化します.

        Args:
            query: ベクトル化するクエリ文字列

        Returns:
            埋め込みベクトル(リスト形式)
        """
        return self.embedding_service.embed_query(query)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """複数のドキュメントをベクトル化します.

        Args:
            documents: ベクトル化するドキュメントのリスト

        Returns:
            埋め込みベクトルのリスト
        """
        return self.embedding_service.embed_documents(documents)

    def process_query_and_embed(self, raw_query: str) -> tuple[str, list[float]]:
        """クエリを処理してベクトル化まで実行します.

        Args:
            raw_query: 生のクエリテキスト

        Returns:
            (処理済みクエリ, ベクトル)のタプル
        """
        processed_query = self.generate_search_query(raw_query)
        query_vector = self.embed_query(processed_query)
        return processed_query, query_vector


if __name__ == "__main__":
    # EnhancedRAGServiceのデモ
    if SERVICES_AVAILABLE:
        try:
            logger.info("EnhancedRAGServiceデモ開始")

            # サービス初期化
            rag_service = EnhancedRAGService("RURI_V3_30M")

            # テストデータ
            test_text = "重要な会議の案内です。明日の午後2時から会議室Aで開催します。"
            test_documents = ["重要な会議の案内です", "システムメンテナンスのお知らせ", "新機能リリースについて"]

            # キーワード抽出
            logger.info("キーワード抽出テスト")
            keywords = rag_service.extract_keywords(test_text)
            logger.info("抽出キーワード: %s", keywords)

            # 検索クエリ生成
            search_query = rag_service.generate_search_query(test_text)
            logger.info("生成検索クエリ: %s", search_query)

            # クエリベクトル化
            query_vector = rag_service.embed_query(search_query)
            logger.info("クエリベクトル次元: %d", len(query_vector))

            # ドキュメントベクトル化
            doc_vectors = rag_service.embed_documents(test_documents)
            logger.info("ドキュメント数: %d, ベクトル次元: %d", len(doc_vectors), len(doc_vectors[0]))

            # 統合処理
            processed_query, processed_vector = rag_service.process_query_and_embed(test_text)
            logger.info("統合処理結果 - クエリ: %s, ベクトル次元: %d", processed_query, len(processed_vector))

            logger.info("EnhancedRAGServiceデモ完了!")

        except Exception:
            logger.exception("デモ実行エラー")
    else:
        logger.info("必要なサービスが利用できないため、デモをスキップします")
