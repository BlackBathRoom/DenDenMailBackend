"""検索APIのDTO定義."""

from pydantic import BaseModel, Field


class VectorSearchRequest(BaseModel):
    """ベクトル検索リクエスト.

    Attributes:
        query_embedding (list[float]): クエリのベクトル値
        top_k (int): 取得する件数(デフォルト3件)
    """

    query_embedding: list[float] = Field(..., description="クエリのベクトル値")
    top_k: int = Field(default=3, ge=1, le=10, description="取得件数(1-10)")


class VectorSearchResultItem(BaseModel):
    """検索結果の1件分.

    Attributes:
        id (str): ドキュメントID
        distance (float): 類似度距離(小さいほど似ている)
        document (str | None): ドキュメントのテキスト
        metadata (dict | None): メタデータ
    """

    id: str
    distance: float
    document: str | None = None
    metadata: dict | None = None


class VectorSearchResponse(BaseModel):
    """ベクトル検索レスポンス.

    Attributes:
        results (list[VectorSearchResultItem]): 検索結果リスト
    """

    results: list[VectorSearchResultItem]
