from typing import Literal

from pydantic import BaseModel, EmailStr

from .shared import BasePriority, BasePriorityCreate, BasePriorityUpdate


class DictionaryDTO(BasePriority):
    keyword: str


class AddressRuleDTO(BasePriority):
    email: EmailStr
    name: str


class BaseRuleDTO(BaseModel):
    type: Literal["email", "dictionary"]


class DictionaryCreateDTO(BaseRuleDTO, BasePriorityCreate):
    keyword: str


class AddressRuleCreateDTO(BaseRuleDTO, BasePriorityCreate):
    email: EmailStr
    name: str | None = None


class DictionaryUpdateDTO(BasePriorityUpdate):
    keyword: str | None = None


class AddressRuleUpdateDTO(BasePriorityUpdate):
    email: EmailStr | None = None
    name: str | None = None
