"""メールのCRUD操作."""

from sqlalchemy import Engine

from models.mail import Mail, MailCreate, MailRead, MailUpdate
from services.database.base import BaseDBManager


class MailDBManager(BaseDBManager[Mail, MailCreate, MailRead, MailUpdate]):
    def __init__(self, model: type[Mail] = Mail) -> None:
        super().__init__(model)

    def read(self, engine: Engine, obj_id: int) -> MailRead | None:
        """IDでメールを読み取る.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 読み取り対象のメールID.

        Returns:
            MailRead | None: 読み取ったメールオブジェクト、見つからない場合はNone.
        """
        return self._read(engine, obj_id, factory=MailRead)
