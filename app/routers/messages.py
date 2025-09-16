from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app_conf import MailVendor
from dtos.messages import MessageHeaderDTO, RegisteredFolderDTO, RegisteredVendorDTO, RegisterVendorRequestBody
from services.database.engine import get_engine
from services.database.manager import FolderDBManager, MessageDBManager, VendorDBManager
from usecases.message import connect_vendor, save_messages
from utils.logging import get_logger

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)

logger = get_logger(__name__)


@router.get("/{vendor_id}/{folder_id}", summary="対応ベンダーからメールの一覧取得。bodyは無し。")
def get_messages(
    vendor_id: int,
    folder_id: int,
    engine: Annotated[Engine, Depends(get_engine)],
    offset: int = 0,
    limit: int = 50,
    is_read: bool | None = None,  # noqa: FBT001
) -> list[MessageHeaderDTO]:
    message_manager = MessageDBManager()
    messages = message_manager.read(
        engine,
        conditions=[
            {"operator": "eq", "field": "vendor_id", "value": vendor_id},
            {"operator": "eq", "field": "folder_id", "value": folder_id},
            *([{"operator": "eq", "field": "is_read", "value": is_read}] if is_read is not None else []),
        ],
        offset=offset,
        limit=limit,
    )
    return (
        [
            MessageHeaderDTO(
                message_id=str(m.id),
                subject=m.subject,
                date_received=m.date_received,
                is_read=m.is_read,
            )
            for m in messages
        ]
        if messages
        else []
    )


@router.get("/folders", summary="登録済みフォルダの一覧取得")
def get_registered_folders(engine: Annotated[Engine, Depends(get_engine)]) -> list[RegisteredFolderDTO]:
    folder_manager = FolderDBManager()
    folders = folder_manager.read(engine)
    return [RegisteredFolderDTO(id=cast("int", f.id), name=f.name) for f in folders] if folders else []


@router.get("/vendors", summary="登録済みベンダーの一覧取得")
def get_registered_vendors(engine: Annotated[Engine, Depends(get_engine)]) -> list[RegisteredVendorDTO]:
    vendor_manager = VendorDBManager()
    vendors = vendor_manager.read(engine)
    return [RegisteredVendorDTO(id=cast("int", v.id), name=v.name) for v in vendors] if vendors else []


@router.post("/register", summary="対応ベンダーの登録")
def register_vendor(vendor: RegisterVendorRequestBody, engine: Annotated[Engine, Depends(get_engine)]) -> dict:
    normalized = vendor.vendor.lower().capitalize()
    try:
        v = MailVendor(normalized)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported vender: {vendor}") from None

    vendor_manager = VendorDBManager()
    vendor_manager.register(engine, v)

    client = connect_vendor(v)
    try:
        mails = client.get_mails(count=100)
    finally:
        client.disconnect()

    # DBへ保存
    try:
        save_messages(mails, engine)
    except (RuntimeError, SQLAlchemyError):
        # 登録自体は成功しているためHTTPは成功を返し、詳細はログへ
        logger.exception("Failed to save mails for vendor %s", v.value)

    return {"message": f"Registered vender: {normalized}", "fetched": len(mails)}
