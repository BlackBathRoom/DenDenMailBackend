"""Tag テーブル用DBマネージャ."""

from __future__ import annotations

from models.tag import Tag, TagCreate, TagUpdate
from services.database.manager.base import BaseDBManager


class TagDBManager(BaseDBManager[Tag, TagCreate, TagUpdate]):
    """Tag 用 CRUD マネージャ."""

    def __init__(self, model: type[Tag] = Tag) -> None:
        super().__init__(model)
