"""ベクトル検索機能."""

from typing import Any

from services.ai.rag.vectordatabase.chroma_manager import ChromaVectorManager
from utils.logging import get_logger

logger = get_logger(__name__)


def search_similar_vectors(
    query_embedding: list[float],
    top_k: int = 3,
    collection_name: str = "messages",
) -> list[dict[str, Any]]:
    """ベクトル類似検索を実行.

    Args:
        query_embedding (list[float]): クエリのベクトル値
        top_k (int): 取得する件数(デフォルト3)
        collection_name (str): 検索するコレクション名

    Returns:
        list[dict[str, Any]]: 検索結果のリスト
    """
    logger.info("Starting vector search with top_k=%d in collection '%s'", top_k, collection_name)

    try:
        # ChromaVectorManagerを使用して検索
        vector_manager = ChromaVectorManager(collection_name=collection_name)

        # ベクトル検索を実行
        results = vector_manager.query_vectors(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        # 結果を整形
        search_results = []
        for i in range(len(results["ids"][0])):
            result_item = {
                "id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                "document": results["documents"][0][i] if results.get("documents") else None,
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else None,
            }
            search_results.append(result_item)

    except Exception:
        logger.exception("Failed to perform vector search")
        raise
    else:
        logger.info("Vector search completed: found %d results", len(search_results))
        return search_results
