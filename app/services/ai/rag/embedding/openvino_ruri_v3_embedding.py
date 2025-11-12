"""load_model.pyを活用したシンプルな埋め込みサービス."""

from typing import TYPE_CHECKING, Any, cast

from app.utils.logging import get_logger

if TYPE_CHECKING:
    from app.services.ai.rag.load_model import EmbeddingModels

# load_model.py統合用インポート
try:
    from app.services.ai.rag.load_model import EmbeddingModels, load_model

    LOAD_MODEL_AVAILABLE = True
except ImportError:
    LOAD_MODEL_AVAILABLE = False
    EmbeddingModels = None
    load_model = None


class EnhancedEmbeddingService:
    """load_model.pyを活用したシンプルな埋め込みサービス.

    クエリ抽出、ドキュメント・クエリのベクトル化のみを提供します。
    YAGNIに従い、最小限の機能のみ実装しています。
    """

    def __init__(self, model_type: str = "RURI_V3_30M") -> None:
        """サービスを初期化します.

        Args:
            model_type: 使用するモデルタイプ("RURI_V3_30M" または "RURI_V3_130M")
        """
        self.logger = get_logger(__name__)
        self.model_type = model_type
        self._embedding_model: Any = None

        if not LOAD_MODEL_AVAILABLE:
            msg = "load_model.pyが利用できません。必要な依存関係をインストールしてください"
            raise ImportError(msg)

        # モデルタイプの検証
        if not hasattr(EmbeddingModels, model_type):
            msg = f"サポートされていないモデルタイプ: {model_type}"
            raise ValueError(msg)

    def _get_embedding_model(self) -> Any:  # noqa: ANN401
        """埋め込みモデルを遅延初期化で取得します."""
        if self._embedding_model is None:
            if load_model is None:
                msg = "load_model関数が利用できません"
                raise RuntimeError(msg)

            self.logger.info("埋め込みモデルを初期化中: %s", self.model_type)
            model_enum = getattr(EmbeddingModels, self.model_type)
            self._embedding_model = load_model(model_enum)
            self.logger.info("埋め込みモデル初期化完了")
        return self._embedding_model

    def embed_query(self, query: str) -> list[float]:
        """クエリをベクトル化します.

        Args:
            query: ベクトル化するクエリ文字列

        Returns:
            埋め込みベクトル(リスト形式)
        """
        model = self._get_embedding_model()
        embeddings = model.embed_query(query)
        if hasattr(embeddings, "tolist"):
            return cast("Any", embeddings).tolist()
        return list(embeddings)

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """複数のドキュメントをベクトル化します.

        Args:
            documents: ベクトル化するドキュメントのリスト

        Returns:
            埋め込みベクトルのリスト
        """
        model = self._get_embedding_model()
        embeddings = model.embed_documents(documents)
        result = []
        for emb in embeddings:
            if hasattr(emb, "tolist"):
                result.append(cast("Any", emb).tolist())
            else:
                result.append(list(emb))
        return result

    def embed_document(self, document: str) -> list[float]:
        """単一のドキュメントをベクトル化します.

        Args:
            document: ベクトル化するドキュメント文字列

        Returns:
            埋め込みベクトル(リスト形式)
        """
        return self.embed_documents([document])[0]


def create_enhanced_embedding_service(
    model_type: str = "RURI_V3_30M",
) -> EnhancedEmbeddingService:
    """拡張埋め込みサービスファクトリー.

    Args:
        model_type: 使用するモデルタイプ

    Returns:
        EnhancedEmbeddingServiceインスタンス
    """
    return EnhancedEmbeddingService(model_type=model_type)


if __name__ == "__main__":
    # EnhancedEmbeddingServiceのデモ
    logger = get_logger(__name__)

    if LOAD_MODEL_AVAILABLE:
        try:
            logger.info("EnhancedEmbeddingServiceデモ開始")

            # サービス初期化
            service = EnhancedEmbeddingService("RURI_V3_30M")

            # テストデータ
            test_query = "メール検索"
            test_documents = ["重要な会議の案内です", "システムメンテナンスのお知らせ", "新機能リリースについて"]

            # クエリベクトル化
            logger.info("クエリベクトル化テスト")
            query_embedding = service.embed_query(test_query)
            logger.info("クエリ '%s' -> ベクトル次元: %d", test_query, len(query_embedding))

            # ドキュメントベクトル化
            logger.info("ドキュメントベクトル化テスト")
            doc_embeddings = service.embed_documents(test_documents)
            logger.info("ドキュメント数: %d, ベクトル次元: %d", len(doc_embeddings), len(doc_embeddings[0]))

            logger.info("EnhancedEmbeddingServiceデモ完了!")

        except Exception:
            logger.exception("デモ実行エラー")
    else:
        logger.info("load_model.pyが利用できないため、デモをスキップします")
