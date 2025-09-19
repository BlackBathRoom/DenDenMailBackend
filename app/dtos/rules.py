from pydantic import BaseModel, Field

from .shared.base import BaseDTO


class _Priority(BaseModel):
    """優先度を持つクラス."""

    priority: int = Field(..., ge=1, le=3, description="優先度(1-3)")


class _BasePriorityDTO(BaseDTO, _Priority):
    """IDと優先度を持つ基底クラス."""


class DictionaryDTO(_BasePriorityDTO):
    keyword: str


class AddressDTO(_BasePriorityDTO):
    address: str
    name: str | None = None


class RegisterDictionaryRequestDTO(_Priority):
    keyword: str


class RegisterAddressRequestDTO(_Priority):
    address: str
