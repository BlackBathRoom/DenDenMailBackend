from pydantic import BaseModel, Field


class SummaryDTO(BaseModel):
    id: str = Field(..., description="対象メールのメッセージID")
    content: str = Field(..., description="要約テキスト")
    score: float = Field(ge=0, le=1, description="要約スコア(0-1)")


class DemoSummaryDTO(BaseModel):
    """デモ用のサマリーDTO."""

    id: str = Field(..., description="対象メールのメッセージID")
    content: str = Field(..., description="要約テキスト")
    score: float = Field(ge=0, le=1, description="要約スコア(0-1のダミー)")


def demo_summary_value() -> DemoSummaryDTO:
    """デモ用のサマリー値を生成する."""
    return DemoSummaryDTO(
        id="demo-20250816-0001",
        content="これはデモ用のサマリです。",
        score=0.87,
    )
