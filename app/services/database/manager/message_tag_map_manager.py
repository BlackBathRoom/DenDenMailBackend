"""MessageTagMap テーブル用DBマネージャ (更新なし)."""

from __future__ import annotations

from models.message_tag_map import MessageTagMap, MessageTagMapCreate
from services.database.manager.base import BaseDBManager


class MessageTagMapDBManager(BaseDBManager[MessageTagMap, MessageTagMapCreate, None]):
    """MessageTagMap 用 CRUD マネージャ."""

    def __init__(self, model: type[MessageTagMap] = MessageTagMap) -> None:
        super().__init__(model)
