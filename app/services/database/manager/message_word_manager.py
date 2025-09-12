"""MessageWord テーブル用DBマネージャ (更新なし)."""

from models.message_word import MessageWord, MessageWordCreate
from services.database.manager.base import BaseDBManager


class MessageWordDBManager(BaseDBManager[MessageWord, MessageWordCreate, None]):
    """MessageWord 用 CRUD マネージャ."""

    def __init__(self, model: type[MessageWord] = MessageWord) -> None:
        super().__init__(model)
