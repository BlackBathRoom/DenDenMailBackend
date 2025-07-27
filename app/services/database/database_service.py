"""データベース操作の統合クラス."""

from typing import Optional

from models.mail import Mail, MailCreate, MailUpdate
from models.summary import Summary, SummaryCreate, SummaryUpdate
from services.database.base import get_db_session
from services.database.mail_crud import MailCRUD
from services.database.summary_crud import SummaryCRUD
from sqlmodel import Session


class DatabaseService:
    """データベース操作の統合サービス."""

    def __init__(self, session: Optional[Session] = None):
        """初期化.
        
        Args:
            session: データベースセッション。指定しない場合は新規作成。
        """
        self.session = session or get_db_session()
        self._own_session = session is None

    def __enter__(self):
        """コンテキストマネージャー開始."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了."""
        if self._own_session:
            self.session.close()

    # メール関連操作
    def create_mail(self, mail_data: MailCreate) -> Mail:
        """メールを作成する."""
        return MailCRUD.create_mail(self.session, mail_data)

    def get_mail_by_id(self, mail_id: int) -> Optional[Mail]:
        """IDでメールを取得する."""
        return MailCRUD.get_mail_by_id(self.session, mail_id)

    def get_mail_by_message_id(self, message_id: str) -> Optional[Mail]:
        """メッセージIDでメールを取得する."""
        return MailCRUD.get_mail_by_message_id(self.session, message_id)

    def get_mails(
        self,
        skip: int = 0,
        limit: int = 100,
        folder: Optional[str] = None,
        is_read: Optional[bool] = None,
    ) -> list[Mail]:
        """メール一覧を取得する."""
        return list(MailCRUD.get_mails(self.session, skip, limit, folder, is_read))

    def update_mail(self, mail_id: int, mail_data: MailUpdate) -> Optional[Mail]:
        """メールを更新する."""
        return MailCRUD.update_mail(self.session, mail_id, mail_data)

    def delete_mail(self, mail_id: int) -> bool:
        """メールを削除する."""
        return MailCRUD.delete_mail(self.session, mail_id)

    def mark_mail_as_read(self, mail_id: int) -> Optional[Mail]:
        """メールを既読にする."""
        return MailCRUD.mark_as_read(self.session, mail_id)

    def mark_mail_as_unread(self, mail_id: int) -> Optional[Mail]:
        """メールを未読にする."""
        return MailCRUD.mark_as_unread(self.session, mail_id)

    def move_mail_to_folder(self, mail_id: int, folder: str) -> Optional[Mail]:
        """メールを指定フォルダに移動する."""
        return MailCRUD.move_to_folder(self.session, mail_id, folder)

    def count_mails(
        self,
        folder: Optional[str] = None,
        is_read: Optional[bool] = None,
    ) -> int:
        """メールの件数を取得する."""
        return MailCRUD.count_mails(self.session, folder, is_read)

    # サマリ関連操作
    def create_summary(self, summary_data: SummaryCreate, mail_id: int) -> Summary:
        """サマリを作成する."""
        return SummaryCRUD.create_summary(self.session, summary_data, mail_id)

    def get_summary_by_id(self, summary_id: int) -> Optional[Summary]:
        """IDでサマリを取得する."""
        return SummaryCRUD.get_summary_by_id(self.session, summary_id)

    def get_summary_by_mail_id(self, mail_id: int) -> Optional[Summary]:
        """メールIDでサマリを取得する."""
        return SummaryCRUD.get_summary_by_mail_id(self.session, mail_id)

    def get_summary_by_message_id(self, message_id: str) -> Optional[Summary]:
        """メッセージIDでサマリを取得する."""
        return SummaryCRUD.get_summary_by_message_id(self.session, message_id)

    def get_summaries(self, skip: int = 0, limit: int = 100) -> list[Summary]:
        """サマリ一覧を取得する."""
        return list(SummaryCRUD.get_summaries(self.session, skip, limit))

    def update_summary(self, summary_id: int, summary_data: SummaryUpdate) -> Optional[Summary]:
        """サマリを更新する."""
        return SummaryCRUD.update_summary(self.session, summary_id, summary_data)

    def delete_summary(self, summary_id: int) -> bool:
        """サマリを削除する."""
        return SummaryCRUD.delete_summary(self.session, summary_id)

    def delete_summary_by_mail_id(self, mail_id: int) -> bool:
        """メールIDでサマリを削除する."""
        return SummaryCRUD.delete_summary_by_mail_id(self.session, mail_id)

    def count_summaries(self) -> int:
        """サマリの件数を取得する."""
        return SummaryCRUD.count_summaries(self.session)

    # 複合操作
    def create_mail_with_summary(self, mail_data: MailCreate, summary_content: str) -> tuple[Mail, Summary]:
        """メールとサマリを同時に作成する.
        
        Args:
            mail_data: メールデータ
            summary_content: サマリ内容
            
        Returns:
            tuple[Mail, Summary]: 作成されたメールとサマリのタプル
            
        Raises:
            ValueError: メールの作成に失敗した場合
        """
        mail = self.create_mail(mail_data)
        if mail.id is None:
            raise ValueError("メールの作成に失敗しました")
        
        summary_data = SummaryCreate(
            message_id=mail_data.message_id,
            content=summary_content
        )
        summary = self.create_summary(summary_data, mail.id)
        return mail, summary

    def delete_mail_with_summary(self, mail_id: int) -> bool:
        """メールとそのサマリを削除する.
        
        Args:
            mail_id: メールのID
            
        Returns:
            bool: 削除が成功した場合True
        """
        # サマリを先に削除
        self.delete_summary_by_mail_id(mail_id)
        # メールを削除
        return self.delete_mail(mail_id)

    def get_mail_with_summary(self, mail_id: int) -> Optional[tuple[Mail, Optional[Summary]]]:
        """メールとそのサマリを取得する.
        
        Args:
            mail_id: メールのID
            
        Returns:
            tuple[Mail, Optional[Summary]] | None: メールとサマリのタプル、メールが見つからない場合はNone
        """
        mail = self.get_mail_by_id(mail_id)
        if mail is None:
            return None
        
        summary = self.get_summary_by_mail_id(mail_id)
        return mail, summary
