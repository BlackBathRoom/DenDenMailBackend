"""データベース関連のサービス層."""

from abc import ABC, abstractmethod
from typing import overload

from pydantic import BaseModel, ValidationError
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel

from utils.check_implementation import check_implementation
from utils.log_config import get_logger

logger = get_logger(__name__)


class BaseDBManager[TBaseModel: SQLModel, TCreate: BaseModel, TRead: SQLModel, TUpdate: BaseModel](ABC):
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

    def create(self, engine: Engine, obj: TCreate) -> None:
        """新しいレコードを作成する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj (TCreate): 作成するオブジェクト.
        """
        with Session(engine) as session:
            create_obj = self._convert_model(obj)
            session.add(create_obj)
            session.commit()

    def _read(self, engine: Engine, obj_id: int, factory: type[TRead]) -> TRead | None:
        """IDでレコードを読み取る.

        readメソッドの内部で使用.

        ```python
        def read(self, engine: Engine, obj_id: int) -> TRead | None:
            # factoryに読み取りモデルを指定して呼び出す
            return self._read(engine, obj_id, factory=HogeRead)
        ```

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 読み取り対象のオブジェクトID.
            factory (type[TRead]): 読み取りモデル.

        Returns:
            TBaseModel | None: 読み取ったオブジェクト.存在しない場合はNone.
        """
        with Session(engine) as session:
            obj = session.get(self.model, obj_id)
            if obj:
                return self._convert_model(obj, factory=factory)
            return None

    @abstractmethod
    @check_implementation
    def read(self, engine: Engine, obj_id: int) -> TRead | None:
        """IDでレコードを読み取り、読み取りモデルで返却.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 読み取り対象のオブジェクトID.

        Returns:
            TRead | None: 読み取ったオブジェクト.存在しない場合はNone.
        """

    def update(self, engine: Engine, obj_id: int, obj: TUpdate) -> None:
        """IDでレコードを更新する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 更新対象のオブジェクトID.
            obj (TUpdate): 更新するオブジェクト.
        """
        with Session(engine) as session:
            existing_obj = session.get(self.model, obj_id)
            if existing_obj:
                for key, value in obj.model_dump().items():
                    setattr(existing_obj, key, value)
                session.commit()
            else:
                logger.warning("Object with ID %s not found for update.", obj_id)

    def delete(self, engine: Engine, obj_id: int) -> None:
        """IDでレコードを削除する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 削除対象のオブジェクトID.
        """
        with Session(engine) as session:
            obj = session.get(self.model, obj_id)
            if obj:
                session.delete(obj)
                session.commit()
            else:
                logger.warning("Object with ID %s not found for deletion.", obj_id)
