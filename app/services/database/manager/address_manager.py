"""Address テーブル用DBマネージャ."""

from __future__ import annotations

from models.address import Address, AddressCreate, AddressUpdate
from services.database.manager.base import BaseDBManager


class AddressDBManager(BaseDBManager[Address, AddressCreate, AddressUpdate]):
    """Address 用 CRUD マネージャ."""

    def __init__(self, model: type[Address] = Address) -> None:
        super().__init__(model)
