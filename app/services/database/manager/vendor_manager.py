from models.vendor import Vendor, VendorCreate
from services.database.manager.base import BaseDBManager


class VendorDBManager(BaseDBManager[Vendor, VendorCreate, None]):
    """Vendor 用 CRUD マネージャ."""

    def __init__(self, model: type[Vendor] = Vendor) -> None:
        super().__init__(model)
