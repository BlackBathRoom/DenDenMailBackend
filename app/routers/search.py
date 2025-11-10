"""検索APIのルーター."""

from fastapi import APIRouter, HTTPException

from dtos.search import VectorSearchRequest, VectorSearchResponse, VectorSearchResultItem
from services.database.vector_search import search_similar_vectors
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/search",
    tags=["search"],
)


@router.post("/vector", summary="ベクトル類似検索")
def vector_search(request: VectorSearchRequest) -> VectorSearchResponse:
    """ベクトル類似度で検索.

    Args:
        request (VectorSearchRequest): 検索リクエスト(ベクトル値と取得件数)

    Returns:
        VectorSearchResponse: 類似アイテム上位N件
    """
    try:
        # ChromaDBから検索
        results = search_similar_vectors(
            query_embedding=request.query_embedding,
            top_k=request.top_k,
            collection_name="messages",
        )

        # 結果を整形
        items = [VectorSearchResultItem(**result) for result in results]

        return VectorSearchResponse(results=items)

    except Exception:
        logger.exception("Vector search failed")
        raise HTTPException(status_code=500, detail="Vector search failed") from None
