"""PriorityPerson テーブル用DBマネージャ."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from models.priority_person import PriorityPerson, PriorityPersonCreate, PriorityPersonUpdate
from services.database.manager.base import BaseDBManager
from services.database.manager.condition import Condition, resolve_condition

if TYPE_CHECKING:
    from sqlalchemy import Engine


class PriorityPersonDBManager(BaseDBManager[PriorityPerson, PriorityPersonCreate, PriorityPersonUpdate]):
    """PriorityPerson 用 CRUD マネージャ."""

    def __init__(self, model: type[PriorityPerson] = PriorityPerson) -> None:
        super().__init__(model)

    def is_registered(self, engine: Engine, address_id: int) -> bool:
        """指定されたアドレスIDが登録されているかどうかを返す."""
        return (
            self.read(engine, conditions=[{"operator": "eq", "field": "address_id", "value": address_id}]) is not None
        )

    def read_with_address(
        self, engine: Engine, *, conditions: list[Condition] | None = None, order_by: list[str] | None = None
    ) -> list[PriorityPerson] | None:
        """Address リレーションを eager load して取得する.

        Detached オブジェクトで relationship アクセス時に追加クエリ発行 (lazy load) を避け、
        セッション外アクセスでの予期しない flush / None 値問題を防止する。
        """
        with Session(engine) as session:
            # mypy / pyright が Relationship 属性を型解決できずエラーになるため ignore
            stmt = select(PriorityPerson).options(selectinload(PriorityPerson.address))  # pyright: ignore[reportArgumentType]

            if conditions:
                for condition in conditions:
                    stmt = stmt.where(resolve_condition(self.model, condition))

            if order_by:
                for field in order_by:
                    col = getattr(self.model, field.lstrip("-"))
                    stmt = stmt.order_by(col.desc() if field.startswith("-") else col.asc())

            result = list(session.exec(stmt).all())
            return result or None
