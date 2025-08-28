"""基底クラスの定義."""

from pydantic import BaseModel, Field


class BaseIdDTO(BaseModel):
    """IDを持つ基底クラス."""

    id: str


class Priority(BaseModel):
    """優先度を持つクラス."""

    priority: int = Field(..., ge=1, le=3, description="優先度(1-3)")


class BasePriority(BaseIdDTO, Priority):
    """IDと優先度を持つ基底クラス."""


class BasePriorityCreate(Priority):
    """作成用の優先度基底クラス(IDなし)."""


class BasePriorityUpdate(BaseModel):
    """更新用の優先度基底クラス."""

    priority: int | None = Field(None, ge=1, le=3, description="優先度(1-3)")
