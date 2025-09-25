from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from utils.logging import get_logger

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sqlalchemy.engine import Engine

    from services.database.manager.base import BaseDBManager

logger = get_logger(__name__)


def get_list_obj[T: BaseModel](
    manager: BaseDBManager,
    engine: Engine,
    dto_obj: type[T],
) -> list[T]:
    """一覧取得の汎用ユースケース.

    Args:
        manager (BaseDBManager): DBマネージャークラス
        engine (Engine): SQLAlchemyのエンジン
        dto_obj (type[BaseModel]): DTOクラス

    Returns:
        list[BaseModel]: 取得したレコードのリスト
    """
    try:
        records = manager.read(engine)
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch records")
        raise HTTPException(status_code=500, detail="Failed to fetch records") from exc
    return [dto_obj(**r.model_dump()) for r in records] if records is not None else []
