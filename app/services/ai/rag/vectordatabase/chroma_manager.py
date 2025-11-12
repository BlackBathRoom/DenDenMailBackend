"""ChromaDB データ管理."""

from __future__ import annotations

import uuid

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from collections.abc import Sequence

from services.ai.rag.vectordatabase.chroma_client import get_chroma_client
from utils.logging import get_logger


class VectorMetadata(TypedDict, total=False):
    """ベクトルデータに付与するメタデータの型定義.

    total=Falseにより、全てのフィールドがオプショナルになります。
    プロジェクトの要件に応じてフィールドを追加してください。
    """

    source: str  # データの出所 (例: "email", "document")
    timestamp: str  # タイムスタンプ (ISO 8601形式)
    category: str  # カテゴリ
    tags: list[str]  # タグのリスト


class QueryResult(TypedDict):
    """ChromaDB クエリ結果の型定義."""

    ids: list[list[str]]
    distances: list[list[float]] | None
    documents: list[list[str]] | None
    metadatas: list[list[dict[str, Any]]] | None
    embeddings: list[list[list[float]]] | None


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
        embeddings: list[Sequence[float]],
        documents: list[str] | None = None,
        metadatas: list[VectorMetadata | dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """ベクトル化済みデータをChromaDBに追加.

        Args:
            embeddings (list[Sequence[float]]): ベクトル化済みデータ
            documents (list[str] | None): 元のテキスト(省略可)
            metadatas (list[VectorMetadata | dict[str, Any]] | None): メタデータ(省略可)
                VectorMetadataを使用することで型安全性が向上します
            ids (list[str] | None): ドキュメントの一意ID。指定がない場合は自動生成されます

        Returns:
            list[str]: 追加されたドキュメントのIDリスト
        """
        # IDが指定されていない場合はUUIDで自動生成
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]
            logger.debug("Generated %d UUIDs for vector IDs", len(ids))

        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,  # type: ignore[arg-type]
                documents=documents,
                metadatas=metadatas,  # type: ignore[arg-type]
            )
        except Exception:
            logger.exception("Failed to add vectors")
            raise
        else:
            logger.info("Added %d vectors to collection '%s'", len(ids), self.collection_name)
            return ids

    def query_vectors(
        self,
        query_embeddings: list[Sequence[float]],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> QueryResult:
        """ベクトル検索を実行.

        Args:
            query_embeddings (list[Sequence[float]]): クエリのベクトル
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
            return results  # type: ignore[return-value]

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
        embeddings: list[Sequence[float]] | None = None,
        documents: list[str] | None = None,
        metadatas: list[VectorMetadata | dict[str, Any]] | None = None,
    ) -> None:
        """既存のベクトルを更新.

        Args:
            ids (list[str]): 更新するドキュメントID
            embeddings (list[Sequence[float]] | None): 新しいベクトル(省略可)
            documents (list[str] | None): 新しいテキスト(省略可)
            metadatas (list[VectorMetadata | dict[str, Any]] | None): 新しいメタデータ(省略可)
                VectorMetadataを使用することで型安全性が向上します
        """
        try:
            self.collection.update(
                ids=ids,
                embeddings=embeddings,  # type: ignore[arg-type]
                documents=documents,
                metadatas=metadatas,  # type: ignore[arg-type]
            )
            logger.info("Updated %d vectors in collection '%s'", len(ids), self.collection_name)
        except Exception:
            logger.exception("Failed to update vectors")
            raise
