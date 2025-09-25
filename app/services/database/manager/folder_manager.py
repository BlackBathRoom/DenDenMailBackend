"""Folder テーブル用DBマネージャ."""

from __future__ import annotations

from typing import TYPE_CHECKING

from models.folder import Folder, FolderCreate, FolderUpdate
from services.database.manager.base import BaseDBManager

if TYPE_CHECKING:
    from sqlalchemy import Engine


class FolderDBManager(BaseDBManager[Folder, FolderCreate, FolderUpdate]):
    """Folder 用 CRUD マネージャ."""

    def __init__(self, model: type[Folder] = Folder) -> None:
        super().__init__(model)

    def get_id(self, engine: Engine, folder_name: str) -> int | None:
        """指定されたフォルダ名のIDを取得する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            folder_name (str): フォルダ名.

        Returns:
            int | None: フォルダが存在すればそのID、そうでなければ None.
        """
        stmt = self.read(
            engine, conditions=[{"operator": "eq", "field": "system_type", "value": folder_name.lower()}], limit=1
        )
        return stmt[0].id if stmt else None
