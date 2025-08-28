from fastapi import APIRouter

from dtos.mail_dto import (
    MailbodyDTO,
    MailDTO,
    MailReadUpdateDTO,
    demo_mail_dto_value,
    demo_mail_read_update_dto_value,
    demo_mailbody_dto_value,
)

router = APIRouter(
    prefix="/demo/mails",
    tags=["demo-mail"],
)


@router.get("/", summary="メール一覧取得のデモ値を返す")
async def get_demo_mails(*, is_read: bool | None = None) -> list[MailDTO]:
    # is_readパラメータに関係なくデモ値を返す
    _ = is_read
    return [demo_mail_dto_value()]


@router.get("/{mail_id}", summary="本文取得のデモ値を返す")
async def get_demo_mail_body(mail_id: str) -> MailbodyDTO:
    _ = mail_id  # パラメータを使用したことにする
    return demo_mailbody_dto_value()


@router.put("/{mail_id}", summary="既読操作のデモ値を返す")
async def update_mail_read_status(mail_id: str, update_dto: MailReadUpdateDTO) -> MailReadUpdateDTO:
    _ = mail_id, update_dto  # パラメータを使用したことにする
    return demo_mail_read_update_dto_value()
