"""データベース関連のサービス層."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from pydantic import BaseModel, ValidationError
from sqlmodel import Session, SQLModel, select

from services.database.manager.condition import resolve_condition
from utils.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from services.database.manager.condition import Condition

logger = get_logger(__name__)


class BaseDBManager[TBaseModel: SQLModel, TCreate: BaseModel, TUpdate: (BaseModel, None)]:
    """データベース操作のベースマネージャー.

    Attributes:
        model (SQLModel): 操作対象のSQLModelクラス.
    """

    def __init__(self, model: type[TBaseModel]) -> None:
        self.model = model

    @overload
    def _convert_model(self, obj: SQLModel | BaseModel, *, factory: None = None) -> TBaseModel:
        pass

    @overload
    def _convert_model[T: BaseModel](self, obj: SQLModel | BaseModel, *, factory: type[T]) -> T:
        pass

    def _convert_model[T: BaseModel](
        self,
        obj: SQLModel | BaseModel,
        *,
        factory: type[T] | None = None,
    ) -> TBaseModel | T:
        """SQLModelまたはBaseModelをTBaseModelに変換する.

        Args:
            obj (SQLModel | BaseModel): 変換対象のオブジェクト.
            factory (T | None): 変換対象.

        Returns:
            TBaseModel: 変換後のオブジェクト.
        """
        try:
            model = self.model if factory is None else factory
            converted_obj = model.model_validate(obj)
        except ValidationError:
            logger.exception("Validation error during model conversion: %s")
            raise
        return converted_obj

    def create(self, engine: Engine, obj: TCreate) -> TBaseModel:
        """新しいレコードを作成する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj (TCreate): 作成するオブジェクト.
        """
        with Session(engine) as session:
            create_obj = self._convert_model(obj)
            session.add(create_obj)
            session.commit()

            session.refresh(create_obj)
        return create_obj

    def read(
        self,
        engine: Engine,
        *,
        conditions: list[Condition] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: list[str] | None = None,
    ) -> list[TBaseModel] | None:
        """レコードを読み取る.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            conditions (list[Condition]): 検索条件のリスト.
            limit (int | None): 取得するレコードの最大数. Noneの場合は制限なし.
            offset (int | None): 取得を開始するレコードのオフセット. Noneの場合は0.
            order_by (list[str] | None): ソートするフィールドのリスト. フィールド名の前に'-'を付けると降順.

        Returns:
            list[TBaseModel] | None: 読み取ったオブジェクトのリスト.存在しない場合はNone.
        """
        with Session(engine) as session:
            stmt = select(self.model)

            if conditions is not None:
                for c in conditions:
                    stmt = stmt.where(resolve_condition(self.model, c))

            if order_by:
                for field in order_by:
                    col = getattr(self.model, field.lstrip("-"))
                    stmt = stmt.order_by(col.desc() if field.startswith("-") else col.asc())

            if limit is not None:
                stmt = stmt.limit(limit)

            if offset is not None:
                stmt = stmt.offset(offset)

            result = session.exec(stmt).all()
            if result:
                return [self._convert_model(r, factory=self.model) for r in result]
        return None

    def read_by_id(self, engine: Engine, obj_id: int) -> TBaseModel | None:
        """IDでレコードを読み取る.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 読み取るオブジェクトのID.

        Returns:
            TBaseModel | None: 読み取ったオブジェクト.存在しない場合はNone.
        """
        with Session(engine) as session:
            return session.get(self.model, obj_id)

    def update(
        self,
        engine: Engine,
        obj: TUpdate = None,
        *,
        conditions: list[Condition] | None = None,
    ) -> None:
        """レコードを更新する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj (TUpdate): 更新するオブジェクト.
            conditions (list[Condition] | None): 更新対象を特定するための条件リスト.
        """
        if obj is None:
            logger.error("This table does not support updates.")
            return

        with Session(engine) as session:
            db_obj = self.read(engine, conditions=conditions)

            if db_obj is None:
                logger.warning("No records found for update with conditions: %s", conditions)
                return

            for record in db_obj:
                update_data = obj.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(record, key, value)
                session.add(record)

            session.commit()

    def update_by_id(self, engine: Engine, obj_id: int, obj: TUpdate = None) -> None:
        """IDでレコードを更新する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 更新するオブジェクトのID.
            obj (TUpdate): 更新するオブジェクト.
        """
        if obj is None:
            logger.error("This table does not support updates.")
            return

        with Session(engine) as session:
            db_obj = self.read_by_id(engine, obj_id)
            if db_obj is None:
                logger.warning("No record found for update with ID: %s", obj_id)
                return

            update_data = obj.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_obj, key, value)
            session.add(db_obj)
            session.commit()

    def delete(self, engine: Engine, *, conditions: list[Condition] | None = None) -> None:
        """レコードを削除する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            conditions (list[Condition] | None): 削除対象を特定するための条件リスト.
        """
        with Session(engine) as session:
            db_obj = self.read(engine, conditions=conditions)
            if db_obj is None:
                logger.warning("No records found for deletion with conditions: %s", conditions)
                return

            for record in db_obj:
                session.delete(record)

            session.commit()

    def delete_by_id(self, engine: Engine, obj_id: int) -> None:
        """IDでレコードを削除する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 削除するオブジェクトのID.
        """
        with Session(engine) as session:
            db_obj = self.read_by_id(engine, obj_id)
            if db_obj is None:
                logger.warning("No record found for deletion with ID: %s", obj_id)
                return

            session.delete(db_obj)
            session.commit()

    def exists(self, engine: Engine, obj_id: int) -> bool:
        """指定したIDのレコードが存在するか確認する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 確認するオブジェクトのID.

        Returns:
            bool: レコードが存在する場合はTrue、存在しない場合はFalse.
        """
        return self.read_by_id(engine, obj_id) is not None
