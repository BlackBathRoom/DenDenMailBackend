from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Response
from sqlalchemy.exc import SQLAlchemyError

from utils.logging import get_logger

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sqlalchemy.engine import Engine

    from services.database.manager.base import BaseDBManager

logger = get_logger(__name__)


def update_by_id(
    manager: BaseDBManager,
    engine: Engine,
    record_id: int,
    update_data: BaseModel,
) -> Response:
    """IDで指定したレコードを更新する汎用ユースケース.

    Args:
        manager (type[BaseDBManager]): DBマネージャークラス
        engine (Engine): SQLAlchemyのエンジン
        record_id (int): 更新対象のレコードID
        update_data (BaseModel): 更新データ

    Returns:
        Response: 空のレスポンスオブジェクト
    """
    try:
        manager.update_by_id(engine, record_id, update_data)
    except SQLAlchemyError as exc:
        logger.exception("Failed to update record %d", record_id)
        raise HTTPException(status_code=500, detail="Failed to update record") from exc
    return Response(status_code=204, content="Updated successfully")
