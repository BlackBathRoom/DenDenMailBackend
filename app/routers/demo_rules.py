from fastapi import APIRouter

from dtos.rules import (
    AddressRuleCreateDTO,
    AddressRuleDTO,
    AddressRuleUpdateDTO,
    DictionaryCreateDTO,
    DictionaryDTO,
    DictionaryUpdateDTO,
    demo_address_rule_dto_list,
    demo_address_rule_dto_value,
    demo_dictionary_dto_list,
    demo_dictionary_dto_value,
)

router = APIRouter(
    prefix="/demo/rules",
    tags=["demo-rules"],
)


@router.get("/email", summary="メールアドレスルール取得のデモ値を返す")
async def get_demo_email_rules() -> dict:
    return {
        "address_rules": demo_address_rule_dto_list(),
    }


@router.get("/dictionary", summary="辞書ルール取得のデモ値を返す")
async def get_demo_dictionary_rules() -> list[DictionaryDTO]:
    return demo_dictionary_dto_list()


@router.post("/", summary="ルールの追加のデモ値を返す")
async def create_rule(create_dto: DictionaryCreateDTO | AddressRuleCreateDTO) -> DictionaryDTO | AddressRuleDTO:
    if hasattr(create_dto, "keyword"):
        return demo_dictionary_dto_value()
    return demo_address_rule_dto_value()


@router.delete("/dictionary/{dict_id}", summary="辞書ルール削除のデモ値を返す")
async def delete_dictionary_rule(dict_id: str) -> dict:
    return {"message": f"Dictionary rule {dict_id} deleted successfully"}


@router.delete("/dictionary", summary="辞書ルール一括削除のデモ値を返す")
async def delete_dictionary_rules_bulk(ids: list[str]) -> dict:
    return {"message": f"Dictionary rules {', '.join(ids)} deleted successfully"}


@router.delete("/email/{email_id}", summary="アドレスルール削除のデモ値を返す")
async def delete_email_rule(email_id: str) -> dict:
    return {"message": f"Email rule {email_id} deleted successfully"}


@router.patch("/dictionary/{dict_id}", summary="辞書ルール変更のデモ値を返す")
async def update_dictionary_rule(dict_id: str, update_dto: DictionaryUpdateDTO) -> DictionaryDTO:
    _ = dict_id  # パラメータを使用したことにする
    _ = update_dto
    return demo_dictionary_dto_value()


@router.patch("/email/{email_id}", summary="アドレスルール変更のデモ値を返す")
async def update_email_rule(email_id: str, update_dto: AddressRuleUpdateDTO) -> AddressRuleDTO:
    _ = email_id  # パラメータを使用したことにする
    _ = update_dto
    return demo_address_rule_dto_value()
