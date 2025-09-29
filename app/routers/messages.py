from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app_conf import MailVendor
from dtos.messages import (
    AddressDTO,
    CreateVendorRequestBody,
    FolderDTO,
    MessageBodyDTO,
    MessageHeaderDTO,
    UpdateAddressRequestBody,
    VendorDTO,
)
from models.address import AddressUpdate
from services.database.engine import get_engine
from services.database.manager import (
    AddressDBManager,
    FolderDBManager,
    MessageDBManager,
    VendorDBManager,
)
from usecases import get_list_obj, update_by_id
from usecases.errors import ConflictError, NotFoundError, ValidationError
from usecases.message import connect_vendor, get_message_body, get_message_part_content, save_messages
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
        order_by=["-date_received"],
    )
    if messages is None:
        return []

    resp: list[MessageHeaderDTO] = []
    for m in messages:
        sender_address = ""
        if m.sender_address_id is not None:
            addr = AddressDBManager().read_by_id(engine, m.sender_address_id)
            if addr is not None:
                sender_address = addr.email_address
        resp.append(
            MessageHeaderDTO(
                id=cast("int", m.id),
                subject=m.subject,
                date_received=m.date_received,
                is_read=m.is_read,
                sender_address=sender_address,
            )
        )
    return resp


@router.get("/{vendor_id}/{folder_id}/{message_id}", summary="メッセージ本文(サニタイズ済み)と添付一覧を取得")
def get_message_body_endpoint(
    vendor_id: int,
    folder_id: int,
    message_id: int,
    engine: Annotated[Engine, Depends(get_engine)],
) -> MessageBodyDTO:
    try:
        body = get_message_body(
            message_id=message_id,
            engine=engine,
            vendor_id=vendor_id,
            folder_id=folder_id,
            content_url_builder=lambda part_id: f"/messages/{vendor_id}/{folder_id}/{message_id}/parts/{part_id}",
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return body


@router.get(
    "/{vendor_id}/{folder_id}/{message_id}/parts/{part_id}",
    summary="メッセージ添付ファイル、インライン画像等の実体取得",
)
def get_message_part(
    vendor_id: int,
    folder_id: int,
    message_id: int,
    part_id: int,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    try:
        content, media_type, headers = get_message_part_content(
            vendor_id=vendor_id,
            folder_id=folder_id,
            message_id=message_id,
            part_id=part_id,
            engine=engine,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None

    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/folders", summary="登録済みフォルダの一覧取得")
def get_registered_folders(
    engine: Annotated[Engine, Depends(get_engine)], vendor_id: int | None = None
) -> list[FolderDTO]:
    folders = FolderDBManager().read(engine)
    if folders is None:
        return []

    return [
        FolderDTO(
            id=cast("int", f.id),
            name=f.name,
            message_count=MessageDBManager().count(
                engine,
                conditions=[
                    {"operator": "eq", "field": "folder_id", "value": f.id},
                    *([{"operator": "eq", "field": "vendor_id", "value": vendor_id}] if vendor_id is not None else []),
                ],
            ),
        )
        for f in folders
    ]


@router.get("/vendors", summary="登録済みベンダーの一覧取得")
def get_registered_vendors(engine: Annotated[Engine, Depends(get_engine)]) -> list[VendorDTO]:
    return get_list_obj(VendorDBManager(), engine, VendorDTO)


@router.post("/vendors", summary="対応ベンダーの登録")
def register_vendor(vendor: CreateVendorRequestBody, engine: Annotated[Engine, Depends(get_engine)]) -> Response:
    normalized = vendor.vendor.lower().capitalize()
    try:
        v = MailVendor(normalized)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported vendor: {vendor}") from None

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

    return Response(content=f"Vendor {v.value} registered successfully", status_code=201)


@router.get("/addresses/", summary="登録済みアドレスの一覧取得")
def get_addresses(engine: Annotated[Engine, Depends(get_engine)]) -> list[AddressDTO]:
    return get_list_obj(AddressDBManager(), engine, AddressDTO)


@router.patch("/addresses/{address_id}", summary="登録済みアドレスの表示名更新")
def update_address_name(
    address_id: int,
    body: UpdateAddressRequestBody,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    return update_by_id(
        AddressDBManager(),
        engine,
        address_id,
        AddressUpdate(display_name=body.display_name),
    )
