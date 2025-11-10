"""ChromaDB データ管理."""

from typing import Any

from services.ai.rag.vectordatabase.chroma_client import get_chroma_client
from utils.logging import get_logger

logger = get_logger(__name__)


class ChromaVectorManager:
    """ChromaDBへのベクトルデータ操作を管理."""

    def __init__(self, collection_name: str = "documents") -> None:
        """初期化.

        Args:
            collection_name (str): 使用するコレクション名
        """
        self.collection_name = collection_name
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(collection_name)
        logger.info("ChromaVectorManager initialized with collection: %s", collection_name)

    def add_vectors(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """ベクトル化済みデータをChromaDBに追加.

        Args:
            ids (list[str]): ドキュメントの一意ID (例: ["msg_1", "msg_2"])
            embeddings (list[list[float]]): ベクトル化済みデータ
            documents (list[str] | None): 元のテキスト(省略可)
            metadatas (list[dict[str, Any]] | None): メタデータ(省略可)
        """
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info("Added %d vectors to collection '%s'", len(ids), self.collection_name)
        except Exception:
            logger.exception("Failed to add vectors")
            raise

    def query_vectors(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> Any:
        """ベクトル検索を実行.

        Args:
            query_embeddings (list[list[float]]): クエリのベクトル
            n_results (int): 取得する結果数
            where (dict[str, Any] | None): メタデータフィルタ(省略可)

        Returns:
            QueryResult: 検索結果 (ids, distances, documents, metadatas)
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
            )
        except Exception:
            logger.exception("Failed to query vectors")
            raise
        else:
            logger.info("Query returned %d results", len(results["ids"][0]))
            return results

    def delete_by_ids(self, ids: list[str]) -> None:
        """指定IDのベクトルを削除.

        Args:
            ids (list[str]): 削除するドキュメントID
        """
        try:
            self.collection.delete(ids=ids)
            logger.info("Deleted %d vectors from collection '%s'", len(ids), self.collection_name)
        except Exception:
            logger.exception("Failed to delete vectors")
            raise

    def get_collection_count(self) -> int:
        """コレクション内のドキュメント数を取得.

        Returns:
            int: ドキュメント数
        """
        return self.collection.count()

    def update_vectors(
        self,
        ids: list[str],
        embeddings: list[list[float]] | None = None,
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """既存のベクトルを更新.

        Args:
            ids (list[str]): 更新するドキュメントID
            embeddings (list[list[float]] | None): 新しいベクトル(省略可)
            documents (list[str] | None): 新しいテキスト(省略可)
            metadatas (list[dict[str, Any]] | None): 新しいメタデータ(省略可)
        """
        try:
            self.collection.update(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info("Updated %d vectors in collection '%s'", len(ids), self.collection_name)
        except Exception:
            logger.exception("Failed to update vectors")
            raise
