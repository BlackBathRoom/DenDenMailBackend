from typing import Literal

from pydantic import BaseModel, EmailStr

PriorityLevel = Literal[1, 2, 3]


class DictionaryDTO(BaseModel):
    id: str
    keyword: str
    priority: PriorityLevel


class DictionaryRuleDTO(BaseModel):
    id: str
    keyword: str
    priority: PriorityLevel


class AddressRuleDTO(BaseModel):
    id: str
    email: EmailStr
    name: str
    priority: PriorityLevel


class BaseRuleDTO(BaseModel):
    type: Literal["email", "dictionary"]


class DictionaryCreateDTO(BaseRuleDTO):
    keyword: str
    priority: PriorityLevel


class AddressRuleCreateDTO(BaseRuleDTO):
    email: EmailStr
    name: str | None = None
    priority: PriorityLevel


class DictionaryUpdateDTO(BaseModel):
    keyword: str | None = None
    priority: PriorityLevel | None = None


class AddressRuleUpdateDTO(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    priority: PriorityLevel | None = None
