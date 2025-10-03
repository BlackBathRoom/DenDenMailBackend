from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from dtos.rules import (
    AddressDTO,
    CreateAddressRequestBody,
    CreateDictionaryRequestBody,
    DictionaryDTO,
    UpdateAddressRequestBody,
    UpdateDictionaryRequestBody,
)
from models.priority_person import PriorityPersonCreate, PriorityPersonUpdate
from models.priority_word import PriorityWordCreate, PriorityWordUpdate
from services.database.engine import get_engine
from services.database.manager import AddressDBManager, PriorityPersonDBManager, PriorityWordDBManager
from usecases import get_list_obj, update_by_id
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/rules",
    tags=["rules"],
)


@router.get("/dictionaries", summary="登録済み辞書一覧取得")
def get_dictionaries(
    engine: Annotated[Engine, Depends(get_engine)],
) -> list[DictionaryDTO]:
    return get_list_obj(
        PriorityWordDBManager(),
        engine,
        DictionaryDTO,
    )


@router.post("/dictionaries", summary="辞書に新しい単語を登録")
def create_dictionary(
    body: CreateDictionaryRequestBody,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    manager = PriorityWordDBManager()
    try:
        manager.create(
            engine,
            PriorityWordCreate(word=body.word, priority=body.priority),
        )
    except SQLAlchemyError as exc:
        logger.exception("Failed to create dictionary entry")
        raise HTTPException(status_code=500, detail="Failed to create dictionary entry") from exc
    return Response(status_code=201, content="Created successfully")


@router.patch("/dictionaries/{dictionary_id}", summary="登録済み辞書の優先度レベルを更新")
def update_dictionary(
    dictionary_id: int,
    body: UpdateDictionaryRequestBody,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    return update_by_id(
        PriorityWordDBManager(),
        engine,
        dictionary_id,
        PriorityWordUpdate(priority=body.priority),
    )


@router.delete("/dictionaries/{dictionary_id}", summary="登録済み辞書の削除")
def delete_dictionary(
    dictionary_id: int,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    manager = PriorityWordDBManager()
    if not manager.exists(engine, dictionary_id):
        logger.warning("Dictionary ID %s is not registered", dictionary_id)
        raise HTTPException(status_code=400, detail=f"Dictionary ID {dictionary_id} is not registered") from None
    try:
        manager.delete_by_id(engine, dictionary_id)
    except SQLAlchemyError as exc:
        logger.exception("Failed to delete dictionary entry")
        raise HTTPException(status_code=500, detail="Failed to delete dictionary entry") from exc
    return Response(status_code=200, content="Deleted successfully")


@router.post("/addresses", summary="アドレスに新しい優先度設定を登録")
def create_address(
    body: CreateAddressRequestBody,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    if not AddressDBManager().exists(engine, body.address_id):
        raise HTTPException(status_code=400, detail=f"Address ID {body.address_id} is not registered") from None

    manager = PriorityPersonDBManager()

    if manager.is_registered(engine, body.address_id):
        raise HTTPException(
            status_code=400, detail=f"Address ID {body.address_id} is already registered priority"
        ) from None
    try:
        manager.create(
            engine,
            PriorityPersonCreate(address_id=body.address_id, priority=body.priority),
        )
    except SQLAlchemyError as exc:
        logger.exception("Failed to create address entry")
        raise HTTPException(status_code=500, detail="Failed to create address entry") from exc
    return Response(status_code=201, content="Created successfully")


@router.get("/addresses", summary="登録済みアドレス一覧取得")
def get_addresses(
    engine: Annotated[Engine, Depends(get_engine)],
) -> list[AddressDTO]:
    # Eager load address to avoid detached lazy load issues
    persons = PriorityPersonDBManager().read_with_address(engine)
    if persons is None:
        return []
    return [
        AddressDTO(
            id=cast("int", person.id),
            address=person.address.email_address,
            name=person.address.display_name,
            priority=person.priority,
        )
        for person in persons
    ]


@router.patch("/addresses/{address_id}", summary="登録済みアドレスの優先度レベルを更新")
def update_address(
    address_id: int,
    body: UpdateAddressRequestBody,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    if not AddressDBManager().exists(engine, address_id):
        raise HTTPException(status_code=400, detail=f"Address ID {address_id} is not registered") from None
    return update_by_id(
        PriorityPersonDBManager(),
        engine,
        address_id,
        PriorityPersonUpdate(priority=body.priority),
    )


@router.delete("/addresses/{address_id}", summary="登録済みアドレスの優先度設定を削除")
def delete_address(
    address_id: int,
    engine: Annotated[Engine, Depends(get_engine)],
) -> Response:
    manager = PriorityPersonDBManager()
    if not manager.is_registered(engine, address_id):
        logger.warning("Address ID %s is not registered as priority", address_id)
        raise HTTPException(status_code=400, detail=f"Address ID {address_id} is not registered as priority") from None
    try:
        manager.delete_by_id(engine, address_id)
    except SQLAlchemyError as exc:
        logger.exception("Failed to delete address entry")
        raise HTTPException(status_code=500, detail="Failed to delete address entry") from exc
    return Response(status_code=200, content="Deleted successfully")
