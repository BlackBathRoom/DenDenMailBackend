from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from models.common import BaseSQLModel

if TYPE_CHECKING:
    from models.message import Message


class BaseFolder(BaseModel):
    """FOLDERS ベースモデル."""

    name: str
    system_type: str | None = None  # 固定フォルダ(inbox, sent ...) はユニーク


class Folder(BaseFolder, BaseSQLModel, table=True):
    name: str = Field(unique=True, index=True)
    system_type: str | None = Field(default=None, unique=True, index=True)

    messages: list[Message] = Relationship(back_populates="folder")


class FolderCreate(BaseFolder):
    pass


class FolderRead(BaseFolder, BaseSQLModel):
    pass


class FolderUpdate(SQLModel):
    name: str | None = None  # 表示名のみ更新可
