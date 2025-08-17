from fastapi import APIRouter

from dtos.demo import Demo
from dtos.demo_mail import (
    demo_mail_dto_value,
    demo_mail_read_update_dto_value,
    demo_mailbody_dto_value,
)
from dtos.demo_rules import (
    demo_address_rule_dto_list,
    demo_address_rule_dto_value,
    demo_dictionary_dto_list,
    demo_dictionary_dto_value,
)
from dtos.mail_dto import MailbodyDTO, MailDTO, MailReadUpdateDTO
from dtos.rules_dto import (
    AddressRuleCreateDTO,
    AddressRuleDTO,
    AddressRuleUpdateDTO,
    DictionaryCreateDTO,
    DictionaryDTO,
    DictionaryUpdateDTO,
)

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
)


@router.get("/")
async def demo() -> Demo:
    return Demo(message="Hello, FastAPI!")


# ▼ 追加: メール一覧取得のデモ値(クエリパラメータ対応)
@router.get("/mails", summary="メール一覧取得のデモ値を返す")
async def get_demo_mails(*, is_read: bool | None = None) -> list[MailDTO]:
    # is_readパラメータに関係なくデモ値を返す
    _ = is_read
    return [demo_mail_dto_value()]


# ▼ 追加: 本文取得のデモ値
@router.get("/mails/{mail_id}", summary="本文取得のデモ値を返す")
async def get_demo_mail_body(mail_id: str) -> MailbodyDTO:
    _ = mail_id  # パラメータを使用したことにする
    return demo_mailbody_dto_value()


# ▼ 追加: 既読操作のデモ値
@router.put("/mails/{mail_id}", summary="既読操作のデモ値を返す")
async def update_mail_read_status(mail_id: str, update_dto: MailReadUpdateDTO) -> MailReadUpdateDTO:
    _ = mail_id, update_dto  # パラメータを使用したことにする
    return demo_mail_read_update_dto_value()


# ▼ 追加: メールルール取得のデモ値
@router.get("/rules/email", summary="メールアドレスルール取得のデモ値を返す")
async def get_demo_email_rules() -> dict:
    return {
        "address_rules": demo_address_rule_dto_list(),
    }


# ▼ 追加: 辞書ルール取得のデモ値
@router.get("/rules/dictionary", summary="辞書ルール取得のデモ値を返す")
async def get_demo_dictionary_rules() -> list[DictionaryDTO]:
    return demo_dictionary_dto_list()


# ▼ 追加: ルールの追加のデモ値
@router.post("/rules", summary="ルールの追加のデモ値を返す")
async def create_rule(create_dto: DictionaryCreateDTO | AddressRuleCreateDTO) -> DictionaryDTO | AddressRuleDTO:
    if hasattr(create_dto, "keyword"):
        return demo_dictionary_dto_value()
    return demo_address_rule_dto_value()


# ▼ 追加: 辞書ルール削除のデモ値(単体)
@router.delete("/rules/dictionary/{dict_id}", summary="辞書ルール削除のデモ値を返す")
async def delete_dictionary_rule(dict_id: str) -> dict:
    return {"message": f"Dictionary rule {dict_id} deleted successfully"}


# ▼ 追加: 辞書ルール削除のデモ値(一括)
@router.delete("/rules/dictionary", summary="辞書ルール一括削除のデモ値を返す")
async def delete_dictionary_rules_bulk(ids: list[str]) -> dict:
    return {"message": f"Dictionary rules {', '.join(ids)} deleted successfully"}


# ▼ 追加: アドレスルール削除のデモ値
@router.delete("/rules/email/{email_id}", summary="アドレスルール削除のデモ値を返す")
async def delete_email_rule(email_id: str) -> dict:
    return {"message": f"Email rule {email_id} deleted successfully"}


# ▼ 追加: 辞書ルール変更のデモ値
@router.patch("/rules/dictionary/{dict_id}", summary="辞書ルール変更のデモ値を返す")
async def update_dictionary_rule(dict_id: str, update_dto: DictionaryUpdateDTO) -> DictionaryDTO:
    _ = dict_id  # パラメータを使用したことにする
    _ = update_dto
    return demo_dictionary_dto_value()


# ▼ 追加: アドレスルール変更のデモ値
@router.patch("/rules/email/{email_id}", summary="アドレスルール変更のデモ値を返す")
async def update_email_rule(email_id: str, update_dto: AddressRuleUpdateDTO) -> AddressRuleDTO:
    _ = email_id  # パラメータを使用したことにする
    _ = update_dto
    return demo_address_rule_dto_value()
