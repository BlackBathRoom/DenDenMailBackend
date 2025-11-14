from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from langchain_chroma import Chroma

from app_conf import CHROMA_DB_PATH
from app_resources import app_resources
from services.ai.rag.vectordatabase.vector_message import (
    VectorMessage,
)
from utils.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "main_collection"


@dataclass
class QueryResultVectorMessage:
    message: str
    score: float
    message_id: str | None = None
    section_id: str | None = None


class ChromaManager:
    def __init__(self) -> None:
        self._db: Chroma = Chroma(
            COLLECTION_NAME,
            embedding_function=app_resources.get_embedding_model(),
            persist_directory=str(CHROMA_DB_PATH),
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaManager initialized with collection: %s", COLLECTION_NAME)

    def add_documents(
        self,
        documents: list[VectorMessage],
    ) -> list[str]:
        """ドキュメントを追加する.

        Args:
            documents: 追加するドキュメントのリスト。

        Returns:
            作成したドキュメントIDのリスト。
        """
        logger.info("Adding %d documents to ChromaDB", len(documents))
        ids = [str(uuid4()) for _ in range(len(documents))]
        self._db.add_documents([d.to_ruri_retrieved_format() for d in documents], ids=ids)
        return ids

    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[QueryResultVectorMessage]:
        """類似度検索を行う.

        Returns:
            スコア付きの検索結果。
        """
        logger.info("Performing similarity search for query: %s", query)
        results = self._db.similarity_search_with_relevance_scores(
            self._format_ruri_query(query),
            k=top_k,
        )
        return [
            QueryResultVectorMessage(
                message=doc.page_content,
                score=score,
                message_id=doc.metadata.get("message_id"),
                section_id=doc.metadata.get("section_id"),
            )
            for doc, score in results
        ]

    def _format_ruri_query(self, query: str) -> str:
        """Ruri のクエリ用フォーマットに変換する."""
        return f"検索クエリ: {query}"


if __name__ == "__main__":
    app_resources.load_model()

    cm = ChromaManager()

    def add_documents() -> None:
        cm.add_documents(
            [
                VectorMessage(
                    message="重力とは、質量を持つ物体同士が引き合う力のことである。",
                    message_id="msg1",
                    section_id="sec1",
                ),
                VectorMessage(
                    message="週末の打ち合わせにつきましては、土曜日の午後2時からを予定しております。",
                    message_id="msg2",
                    section_id="sec2",
                ),
                VectorMessage(
                    message="Pythonは、1991年にグイド・ヴァンロッサムによって開発された高水準のプログラミング言語である。",
                    message_id="msg3",
                    section_id="sec3",
                ),
            ]
        )

    # ドキュメント追加のスモークを行いたい場合は `add_documents()` を呼び出してください。

    search_results = cm.similarity_search("ミーティング 時間", top_k=3)
    for res in search_results:
        logger.info(
            "Similarity: %.4f, Message: %s",
            res.score,
            res.message,
        )
