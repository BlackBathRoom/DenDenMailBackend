"""メールのCRUD操作."""

from collections.abc import Sequence

from sqlalchemy import Engine
from sqlmodel import Session, desc, select

from models.mail import Mail, MailCreate, MailRead, MailUpdate
from services.database.base import BaseDBManager


class MailDBManager(BaseDBManager[Mail, MailCreate, MailRead, MailUpdate]):
    def __init__(self, model: type[Mail] = Mail) -> None:
        super().__init__(model)

    def read(self, engine: Engine, obj_id: int) -> MailRead | None:
        """IDでメールを読み取り、MailRead型に変換する.

        Args:
            engine (Engine): SQLAlchemyエンジン.
            obj_id (int): 読み取り対象のメールID.

        Returns:
            MailRead | None: 読み取ったメールオブジェクト、見つからない場合はNone.
        """
        return self._read(engine, obj_id, factory=MailRead)


class MailCRUD:
    """メールのCRUD操作クラス."""

    @staticmethod
    def create_mail(session: Session, mail_data: MailCreate) -> Mail:
        """新しいメールを作成する.

        Args:
            session: データベースセッション
            mail_data: 作成するメールのデータ

        Returns:
            Mail: 作成されたメールオブジェクト
        """
        mail = Mail.model_validate(mail_data)
        session.add(mail)
        session.commit()
        session.refresh(mail)
        return mail

    @staticmethod
    def get_mail_by_id(session: Session, mail_id: int) -> Mail | None:
        """IDでメールを取得する.

        Args:
            session: データベースセッション
            mail_id: メールのID

        Returns:
            Mail | None: メールオブジェクト、見つからない場合はNone
        """
        statement = select(Mail).where(Mail.id == mail_id)
        return session.exec(statement).first()

    @staticmethod
    def get_mail_by_message_id(session: Session, message_id: str) -> Mail | None:
        """メッセージIDでメールを取得する.

        Args:
            session: データベースセッション
            message_id: メッセージID

        Returns:
            Mail | None: メールオブジェクト、見つからない場合はNone
        """
        statement = select(Mail).where(Mail.message_id == message_id)
        return session.exec(statement).first()

    @staticmethod
    def get_mails(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        folder: str | None = None,
        *,
        is_read: bool | None = None,
    ) -> Sequence[Mail]:
        """メール一覧を取得する.

        Args:
            session: データベースセッション
            skip: スキップする件数
            limit: 取得する最大件数
            folder: フィルタするフォルダ名
            is_read: 既読状態でフィルタ

        Returns:
            Sequence[Mail]: メールのリスト
        """
        statement = select(Mail)

        if folder is not None:
            statement = statement.where(Mail.mail_folder == folder)

        if is_read is not None:
            statement = statement.where(Mail.is_read == is_read)

        statement = statement.offset(skip).limit(limit).order_by(desc(Mail.received_at))
        return session.exec(statement).all()

    @staticmethod
    def update_mail(session: Session, mail_id: int, mail_data: MailUpdate) -> Mail | None:
        """メールを更新する.

        Args:
            session: データベースセッション
            mail_id: 更新するメールのID
            mail_data: 更新データ

        Returns:
            Mail | None: 更新されたメールオブジェクト、見つからない場合はNone
        """
        statement = select(Mail).where(Mail.id == mail_id)
        mail = session.exec(statement).first()

        if mail is None:
            return None

        mail_update_data = mail_data.model_dump(exclude_unset=True)
        for field, value in mail_update_data.items():
            setattr(mail, field, value)

        session.add(mail)
        session.commit()
        session.refresh(mail)
        return mail

    @staticmethod
    def delete_mail(session: Session, mail_id: int) -> bool:
        """メールを削除する.

        Args:
            session: データベースセッション
            mail_id: 削除するメールのID

        Returns:
            bool: 削除が成功した場合True、メールが見つからない場合False
        """
        statement = select(Mail).where(Mail.id == mail_id)
        mail = session.exec(statement).first()

        if mail is None:
            return False

        session.delete(mail)
        session.commit()
        return True

    @staticmethod
    def count_mails(
        session: Session,
        folder: str | None = None,
        *,
        is_read: bool | None = None,
    ) -> int:
        """メールの件数を取得する.

        Args:
            session: データベースセッション
            folder: フィルタするフォルダ名
            is_read: 既読状態でフィルタ

        Returns:
            int: メールの件数
        """
        statement = select(Mail)

        if folder is not None:
            statement = statement.where(Mail.mail_folder == folder)

        if is_read is not None:
            statement = statement.where(Mail.is_read == is_read)

        results = session.exec(statement).all()
        return len(results)

    @staticmethod
    def mark_as_read(session: Session, mail_id: int) -> Mail | None:
        """メールを既読にする.

        Args:
            session: データベースセッション
            mail_id: メールのID

        Returns:
            Mail | None: 更新されたメールオブジェクト、見つからない場合はNone
        """
        update_data = MailUpdate(is_read=True)
        return MailCRUD.update_mail(session, mail_id, update_data)

    @staticmethod
    def mark_as_unread(session: Session, mail_id: int) -> Mail | None:
        """メールを未読にする.

        Args:
            session: データベースセッション
            mail_id: メールのID

        Returns:
            Mail | None: 更新されたメールオブジェクト、見つからない場合はNone
        """
        update_data = MailUpdate(is_read=False)
        return MailCRUD.update_mail(session, mail_id, update_data)

    @staticmethod
    def move_to_folder(session: Session, mail_id: int, folder: str) -> Mail | None:
        """メールを指定フォルダに移動する.

        Args:
            session: データベースセッション
            mail_id: メールのID
            folder: 移動先フォルダ名

        Returns:
            Mail | None: 更新されたメールオブジェクト、見つからない場合はNone
        """
        update_data = MailUpdate(mail_folder=folder)
        return MailCRUD.update_mail(session, mail_id, update_data)
