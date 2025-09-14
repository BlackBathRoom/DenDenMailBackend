from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app_conf import MailVendor
from services.database.engine import get_engine
from services.database.manager.vendor_manager import VendorDBManager
from usecases.mail import connect_vendor, save_mails
from utils.logging import get_logger

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)

logger = get_logger(__name__)


# messages/{vender}/{folder}/mail であるべきでは?
@router.get("/{vendor}", summary="対応ベンダーからメールの一覧取得。bodyは無し。")
async def get_mails(vendor: str) -> dict:
    return {"vender": vendor, "mails": []}


@router.post("/register/{vendor}", summary="対応ベンダーの登録")
async def register_vendor(vendor: str, engine: Annotated[Engine, Depends(get_engine)]) -> dict:
    normalized = vendor.lower().capitalize()
    try:
        v = MailVendor(normalized)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported vender: {vendor}") from None

    vendor_manager = VendorDBManager()
    vendor_manager.register(engine, v)

    client = connect_vendor(v)
    try:
        mails = client.get_mails(-1)
    finally:
        client.disconnect()

    # DBへ保存
    try:
        save_mails(mails, engine)
    except (RuntimeError, SQLAlchemyError):
        # 登録自体は成功しているためHTTPは成功を返し、詳細はログへ
        logger.exception("Failed to save mails for vendor %s", v.value)

    return {"message": f"Registered vender: {normalized}", "fetched": len(mails)}
