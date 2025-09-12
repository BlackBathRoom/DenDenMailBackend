"""MessagePart テーブル用DBマネージャ (Update モデルなし)."""

from models.message_part import MessagePart, MessagePartCreate
from services.database.manager.base import BaseDBManager


class MessagePartDBManager(BaseDBManager[MessagePart, MessagePartCreate, None]):
    """MessagePart 用 CRUD マネージャ.

    Update 操作は未サポートのため obj=None を渡すとベース側で弾かれる。
    """

    def __init__(self, model: type[MessagePart] = MessagePart) -> None:
        super().__init__(model)
