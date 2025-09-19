from __future__ import annotations

from typing import TYPE_CHECKING

from models.summary import Summary, SummaryCreate, SummaryUpdate
from services.database.manager.base import BaseDBManager

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


class SummaryDBManager(BaseDBManager[Summary, SummaryCreate, SummaryUpdate]):
    def __init__(self, model: type[Summary] = Summary) -> None:
        super().__init__(model)

    def add_summary(self, engine: Engine, message_id: int, content: str) -> Summary:
        summary_create = SummaryCreate(message_id=message_id, content=content)
        self.create(engine, summary_create)
        summary = self.read(engine, conditions=[{"operator": "eq", "field": "message_id", "value": message_id}])
        if summary is None:
            msg = "Failed to save summary"
            raise ValueError(msg)
        return summary[0]

    def is_generated(self, engine: Engine, message_id: int) -> bool:
        summary = self.read(engine, conditions=[{"operator": "eq", "field": "message_id", "value": message_id}])
        return summary is not None
