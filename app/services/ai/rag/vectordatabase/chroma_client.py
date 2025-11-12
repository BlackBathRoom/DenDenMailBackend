"""ChromaDB クライアント管理."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import chromadb

from chromadb.config import Settings

from app_conf import CHROMA_DB_PATH
from utils.logging import get_logger

if TYPE_CHECKING:
    from chromadb.api import ClientAPI

logger = get_logger(__name__)


class ChromaClient:
    """ChromaDB クライアントのシングルトン管理."""

    _instance: ChromaClient | None = None
    _client: ClientAPI | None = None

    def __new__(cls) -> Self:
        """シングルトンインスタンスを返す."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance  # type: ignore[return-value]

    def __init__(self) -> None:
        """クライアントを初期化."""
        if self._client is None:
            self._client = self._initialize_client()

    def _initialize_client(self) -> ClientAPI:
        """ChromaDBクライアントを初期化.

        Returns:
            ClientAPI: 初期化されたChromaDBクライアント
        """
        # データベースディレクトリを作成
        CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)

        logger.info("Initializing ChromaDB at: %s", CHROMA_DB_PATH)

        return chromadb.PersistentClient(
            path=str(CHROMA_DB_PATH),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

    @property
    def client(self) -> ClientAPI:
        """ChromaDBクライアントを取得.

        Returns:
            ClientAPI: ChromaDBクライアント
        """
        if self._client is None:
            self._client = self._initialize_client()
        return self._client

    def get_or_create_collection(self, name: str, metadata: dict[str, Any] | None = None) -> chromadb.Collection:
        """コレクションを取得または作成.

        Args:
            name (str): コレクション名
            metadata (dict | None): メタデータ(省略可)

        Returns:
            chromadb.Collection: コレクション
        """
        return self.client.get_or_create_collection(name=name, metadata=metadata or {})

    def delete_collection(self, name: str) -> None:
        """コレクションを削除.

        Args:
            name (str): コレクション名
        """
        try:
            self.client.delete_collection(name=name)
            logger.info("Collection '%s' deleted", name)
        except Exception:
            logger.exception("Failed to delete collection '%s'", name)


def get_chroma_client() -> ChromaClient:
    """ChromaDBクライアントのインスタンスを取得.

    Returns:
        ChromaClient: ChromaDBクライアント
    """
    return ChromaClient()
