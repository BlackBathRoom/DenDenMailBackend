from pydantic import BaseModel, Field


class SummaryDTO(BaseModel):
    content: str = Field(..., description="要約テキスト")
