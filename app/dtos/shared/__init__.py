"""共通の型定義とバリデータ."""

from pydantic import BaseModel, Field

# 優先度フィールド用の共通定義
PriorityField = Field(..., ge=1, le=3, description="優先度(1-3)")
OptionalPriorityField = Field(None, ge=1, le=3, description="優先度(1-3)")

# 共通の型注釈
PriorityInt = int
OptionalPriorityInt = int | None


class BasePriority(BaseModel):
    """優先度を持つ基底クラス."""

    id: str
    priority: PriorityInt = PriorityField


class BaseMailPriority(BaseModel):
    """メール用の優先度を持つ基底クラス."""

    id: str
    priority: PriorityInt = PriorityField


class BasePriorityCreate(BaseModel):
    """作成用の優先度基底クラス."""

    priority: PriorityInt = PriorityField


class BasePriorityUpdate(BaseModel):
    """更新用の優先度基底クラス."""

    priority: OptionalPriorityInt = OptionalPriorityField
