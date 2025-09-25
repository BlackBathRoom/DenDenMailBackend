"""基底クラスの定義."""

from pydantic import BaseModel


class BaseDTO(BaseModel):
    """IDを持つ基底クラス."""

    id: int
