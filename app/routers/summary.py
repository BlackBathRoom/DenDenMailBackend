from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.engine import Engine

from dtos.summary import SummaryDTO
from services.database.engine import get_engine
from services.database.manager import SummaryDBManager
from usecases.errors import ConflictError, NotFoundError, PlainTextRequiredError, ValidationError
from usecases.summary import create_summary

router = APIRouter(
    prefix="/summary",
    tags=["summary"],
)


@router.get("/{message_id}", summary="サマリーテキスト取得")
def get_summary(message_id: int, engine: Annotated[Engine, Depends(get_engine)]) -> SummaryDTO:
    summary_manager = SummaryDBManager()
    summary = summary_manager.read(
        engine,
        conditions=[{"operator": "eq", "field": "message_id", "value": message_id}],
    )
    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    return SummaryDTO(content=summary[0].content)


@router.post("/{message_id}", summary="サマリーテキスト生成")
def create_summary_endpoint(message_id: int, engine: Annotated[Engine, Depends(get_engine)]) -> SummaryDTO:
    try:
        content = create_summary(message_id, engine=engine)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except (ValidationError, PlainTextRequiredError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return SummaryDTO(content=content)
