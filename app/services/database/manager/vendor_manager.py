from __future__ import annotations

from typing import TYPE_CHECKING

from models.vendor import Vendor, VendorCreate
from services.database.manager.base import BaseDBManager
from services.database.manager.condition import FieldCondition
from utils.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from app_conf import MailVendor

logger = get_logger(__name__)


class VendorDBManager(BaseDBManager[Vendor, VendorCreate, None]):
    """Vendor 用 CRUD マネージャ."""

    def __init__(self, model: type[Vendor] = Vendor) -> None:
        super().__init__(model)

    def get_id(self, engine: Engine, vendor: MailVendor) -> int | None:
        """指定されたベンダーのIDを取得する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            vendor (MailVendor): ベンダー.

        Returns:
            int | None: ベンダーが存在すればそのID、そうでなければ None.
        """
        stmt = self.read(engine, conditions=[FieldCondition(operator="eq", field="name", value=vendor.value)])
        return stmt[0].id if stmt else None

    def is_registered(self, engine: Engine, vendor: MailVendor) -> bool:
        """指定されたベンダーが登録されているか確認する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            vendor (MailVendor): 確認するベンダー.

        Returns:
            bool: 登録されていれば True、そうでなければ False.
        """
        stmt = self.read(engine, conditions=[FieldCondition(operator="eq", field="name", value=vendor.value)])
        return stmt is not None

    def register(self, engine: Engine, vendor: MailVendor) -> None:
        """指定されたベンダーを登録する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            vendor (MailVendor): 登録するベンダー.
        """
        if self.is_registered(engine, vendor):
            logger.info("Vendor %s is already registered.", vendor.value)
            return
        create_obj = VendorCreate(name=vendor)
        self.create(engine, create_obj)
        logger.info("Vendor %s registered successfully.", vendor.value)
