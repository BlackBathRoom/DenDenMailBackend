"""ChromaDB データ管理."""

from __future__ import annotations

import uuid

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict

from services.ai.rag.vectordatabase.chroma_client import get_chroma_client
from utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Sequence


class VectorMetadata(TypedDict):
    """ベクトルデータに付与するメタデータの型定義 (固定フィールド)."""

    message_id: str  # メッセージID (必須)
    section_number: int  # セクション番号 (必須)


@dataclass
class VectorDocument:
    """ベクトルデータベースに格納する単一ドキュメント.

    embedding、message_id、section_numberは必須です。
    IDは自動生成されますが、明示的に指定することも可能です。
    """

    embedding: Sequence[float]  # ベクトル (必須)
    message_id: str  # メッセージID (必須)
    section_number: int  # セクション番号 (必須)
    document: str | None = None  # テキスト内容 (オプション)
    id: str = ""  # ドキュメントID (空文字列の場合は自動生成)

    def __post_init__(self) -> None:
        """初期化後の処理でIDを自動生成."""
        if not self.id:
            self.id = str(uuid.uuid4())

    @property
    def metadata(self) -> VectorMetadata:
        """メタデータを返す."""
        return {
            "message_id": self.message_id,
            "section_number": self.section_number,
        }


@dataclass
class SearchResultItem:
    """検索結果の単一アイテム."""

    id: str
    distance: float
    document: str | None
    message_id: str
    section_number: int
    embedding: list[float] | None = None

    @classmethod
    def from_query_result(cls, query_result: QueryResult, index: int) -> SearchResultItem:
        """QueryResultの指定インデックスから生成.

        Args:
            query_result: ChromaDBからのクエリ結果
            index: 結果リスト内のインデックス

        Returns:
            SearchResultItem: 検索結果アイテム
        """
        metadata = query_result["metadatas"][0][index] if query_result["metadatas"] else {}
        return cls(
            id=query_result["ids"][0][index],
            distance=query_result["distances"][0][index] if query_result["distances"] else 0.0,
            document=query_result["documents"][0][index] if query_result["documents"] else None,
            message_id=str(metadata.get("message_id", "")),
            section_number=int(metadata.get("section_number", 0)),
            embedding=query_result["embeddings"][0][index] if query_result["embeddings"] else None,
        )


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

    def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """VectorDocumentのリストを一括追加 (推奨メソッド).

        このメソッドを使用することで、ID、embedding、document、metadataが
        常に対応していることが保証されます。

        Args:
            documents (list[VectorDocument]): 追加するドキュメントのリスト

        Returns:
            list[str]: 追加されたドキュメントのIDリスト

        Example:
            >>> doc1 = VectorDocument(
            ...     embedding=[0.1, 0.2, 0.3], message_id="msg_001", section_number=1, document="サンプルテキスト"
            ... )
            >>> doc2 = VectorDocument(embedding=[0.4, 0.5, 0.6], message_id="msg_001", section_number=2)
            >>> manager = ChromaVectorManager()
            >>> ids = manager.add_documents([doc1, doc2])
        """
        ids = [doc.id for doc in documents]
        embeddings = [doc.embedding for doc in documents]
        texts = [doc.document for doc in documents] if any(doc.document for doc in documents) else None
        metadatas: list[VectorMetadata | dict[str, Any]] = [doc.metadata for doc in documents]

        return self.add_vectors(
            embeddings=embeddings,
            documents=texts,  # type: ignore[arg-type]
            metadatas=metadatas,
            ids=ids,
        )

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

    def query_documents(
        self,
        query_embedding: Sequence[float],
        n_results: int = 10,
        message_id: str | None = None,
    ) -> list[SearchResultItem]:
        """ベクトル検索を実行し、結果をSearchResultItemのリストで返す (推奨メソッド).

        Args:
            query_embedding (Sequence[float]): クエリのベクトル
            n_results (int): 取得する結果数 (デフォルト: 10)
            message_id (str | None): 特定のメッセージIDでフィルタ (省略可)

        Returns:
            list[SearchResultItem]: 検索結果のリスト

        Example:
            >>> manager = ChromaVectorManager()
            >>> results = manager.query_documents(query_embedding=[0.1, 0.2, 0.3], n_results=5, message_id="msg_001")
            >>> for result in results:
            ...     print(f"ID: {result.id}, Distance: {result.distance}")
            ...     print(f"Message: {result.message_id}, Section: {result.section_number}")
        """
        where = {"message_id": message_id} if message_id else None

        query_result = self.query_vectors(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

        # QueryResultをSearchResultItemのリストに変換
        return [SearchResultItem.from_query_result(query_result, i) for i in range(len(query_result["ids"][0]))]

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
