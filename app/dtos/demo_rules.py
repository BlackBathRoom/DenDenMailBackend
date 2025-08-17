from __future__ import annotations

from .rules_dto import (
    AddressRuleCreateDTO,
    AddressRuleDTO,
    AddressRuleUpdateDTO,
    BaseRuleDTO,
    DictionaryCreateDTO,
    DictionaryDTO,
    DictionaryUpdateDTO,
)


def demo_dictionary_dto_value() -> DictionaryDTO:
    return DictionaryDTO(
        id="1",
        keyword="至急",
        priority=3,
    )


def demo_address_rule_dto_value() -> AddressRuleDTO:
    return AddressRuleDTO(
        id="1",
        email="boss@example.com",
        name="上司",
        priority=3,
    )


def demo_base_rule_dto_dictionary_value() -> BaseRuleDTO:
    return BaseRuleDTO(type="dictionary")


def demo_base_rule_dto_email_value() -> BaseRuleDTO:
    return BaseRuleDTO(type="email")


def demo_dictionary_create_dto_value() -> DictionaryCreateDTO:
    return DictionaryCreateDTO(
        type="dictionary",
        keyword="緊急",
        priority=3,
    )


def demo_address_rule_create_dto_value() -> AddressRuleCreateDTO:
    return AddressRuleCreateDTO(
        type="email",
        email="manager@example.com",
        name="マネージャー",
        priority=2,
    )


def demo_dictionary_update_dto_value() -> DictionaryUpdateDTO:
    return DictionaryUpdateDTO(
        keyword="最優先",
        priority=3,
    )


def demo_address_rule_update_dto_value() -> AddressRuleUpdateDTO:
    return AddressRuleUpdateDTO(
        email="ceo@example.com",
        name="代表取締役",
        priority=3,
    )


# 複数のデモ値を返すリスト用の関数
def demo_dictionary_dto_list() -> list[DictionaryDTO]:
    return [
        DictionaryDTO(id="1", keyword="至急", priority=3),
        DictionaryDTO(id="2", keyword="重要", priority=2),
        DictionaryDTO(id="3", keyword="確認", priority=1),
    ]


def demo_address_rule_dto_list() -> list[AddressRuleDTO]:
    return [
        AddressRuleDTO(id="1", email="boss@example.com", name="上司", priority=3),
        AddressRuleDTO(id="2", email="manager@example.com", name="マネージャー", priority=2),
        AddressRuleDTO(id="3", email="team@example.com", name="チーム", priority=1),
    ]
