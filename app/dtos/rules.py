from pydantic import BaseModel, Field

from .shared.base import BaseDTO


class _Priority(BaseModel):
    """優先度を持つクラス."""

    priority: int = Field(..., ge=1, le=3, description="優先度(1-3)")


class _BasePriorityDTO(BaseDTO, _Priority):
    """IDと優先度を持つ基底クラス."""


class DictionaryDTO(_BasePriorityDTO):
    word: str


class AddressDTO(_BasePriorityDTO):
    address: str
    name: str | None = None


class UpdateDictionaryRequestBody(_Priority):
    pass


class UpdateAddressRequestBody(_Priority):
    pass


class CreateDictionaryRequestBody(_Priority):
    word: str


class CreateAddressRequestBody(_Priority):
    address_id: int
