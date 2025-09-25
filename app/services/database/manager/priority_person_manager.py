"""PriorityPerson テーブル用DBマネージャ."""

from __future__ import annotations

from models.priority_person import PriorityPerson, PriorityPersonCreate, PriorityPersonUpdate
from services.database.manager.base import BaseDBManager


class PriorityPersonDBManager(BaseDBManager[PriorityPerson, PriorityPersonCreate, PriorityPersonUpdate]):
    """PriorityPerson 用 CRUD マネージャ."""

    def __init__(self, model: type[PriorityPerson] = PriorityPerson) -> None:
        super().__init__(model)
