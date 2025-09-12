"""Folder テーブル用DBマネージャ."""

from models.folder import Folder, FolderCreate, FolderUpdate
from services.database.manager.base import BaseDBManager


class FolderDBManager(BaseDBManager[Folder, FolderCreate, FolderUpdate]):
    """Folder 用 CRUD マネージャ."""

    def __init__(self, model: type[Folder] = Folder) -> None:
        super().__init__(model)
