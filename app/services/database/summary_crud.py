from sqlalchemy import Engine

from models.summary import Summary, SummaryCreate, SummaryRead, SummaryUpdate
from services.database.base import BaseDBManager


class SummaryDBManager(BaseDBManager[Summary, SummaryCreate, SummaryRead, SummaryUpdate]):
    def __init__(self, model: type[Summary] = Summary) -> None:
        super().__init__(model)

    def read(self, engine: Engine, obj_id: int) -> SummaryRead | None:
        """IDで要約を読み取る.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 読み取り対象の要約ID.

        Returns:
            SummaryRead | None: 読み取った要約オブジェクト、見つからない場合はNone.
        """
        return self._read(engine, obj_id, factory=SummaryRead)
