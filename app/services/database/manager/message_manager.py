"""Message テーブル用DBマネージャ."""

from __future__ import annotations

from models.message import Message, MessageCreate, MessageUpdate
from services.database.manager.base import BaseDBManager


class MessageDBManager(BaseDBManager[Message, MessageCreate, MessageUpdate]):
    """Message 用 CRUD マネージャ."""

    def __init__(self, model: type[Message] = Message) -> None:
        super().__init__(model)
