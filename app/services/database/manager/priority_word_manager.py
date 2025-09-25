"""PriorityWord テーブル用DBマネージャ."""

from __future__ import annotations

from models.priority_word import PriorityWord, PriorityWordCreate, PriorityWordUpdate
from services.database.manager.base import BaseDBManager


class PriorityWordDBManager(BaseDBManager[PriorityWord, PriorityWordCreate, PriorityWordUpdate]):
    """PriorityWord 用 CRUD マネージャ."""

    def __init__(self, model: type[PriorityWord] = PriorityWord) -> None:
        super().__init__(model)
