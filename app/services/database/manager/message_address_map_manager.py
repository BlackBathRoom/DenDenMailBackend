"""MessageAddressMap テーブル用DBマネージャ (更新なし)."""

from models.message_address_map import MessageAddressMap, MessageAddressMapCreate
from services.database.manager.base import BaseDBManager


class MessageAddressMapDBManager(BaseDBManager[MessageAddressMap, MessageAddressMapCreate, None]):
    """MessageAddressMap 用 CRUD マネージャ."""

    def __init__(self, model: type[MessageAddressMap] = MessageAddressMap) -> None:
        super().__init__(model)
