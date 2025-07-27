"""データベース操作の便利関数群."""

from typing import Optional

from models.mail import Mail, MailCreate, MailUpdate
from models.summary import Summary, SummaryCreate, SummaryUpdate
from services.database.database_service import DatabaseService



def create_mail(mail_data: MailCreate) -> Mail:
    """メールを作成する."""
    with DatabaseService() as db:
        return db.create_mail(mail_data)


def get_mail(mail_id: int) -> Optional[Mail]:
    """IDでメールを取得する."""
    with DatabaseService() as db:
        return db.get_mail_by_id(mail_id)


def find_mail_by_message_id(message_id: str) -> Optional[Mail]:
    """メッセージIDでメールを取得する."""
    with DatabaseService() as db:
        return db.get_mail_by_message_id(message_id)


def list_mails(
    skip: int = 0,
    limit: int = 100,
    folder: Optional[str] = None,
    is_read: Optional[bool] = None,
) -> list[Mail]:
    """メール一覧を取得する."""
    with DatabaseService() as db:
        return db.get_mails(skip, limit, folder, is_read)


def update_mail(mail_id: int, mail_data: MailUpdate) -> Optional[Mail]:
    """メールを更新する."""
    with DatabaseService() as db:
        return db.update_mail(mail_id, mail_data)


def delete_mail(mail_id: int) -> bool:
    """メールを削除する."""
    with DatabaseService() as db:
        return db.delete_mail(mail_id)


def mark_as_read(mail_id: int) -> Optional[Mail]:
    """メールを既読にする."""
    with DatabaseService() as db:
        return db.mark_mail_as_read(mail_id)


def mark_as_unread(mail_id: int) -> Optional[Mail]:
    """メールを未読にする."""
    with DatabaseService() as db:
        return db.mark_mail_as_unread(mail_id)


def move_to_folder(mail_id: int, folder: str) -> Optional[Mail]:
    """メールを指定フォルダに移動する."""
    with DatabaseService() as db:
        return db.move_mail_to_folder(mail_id, folder)


def count_mails(
    folder: Optional[str] = None,
    is_read: Optional[bool] = None,
) -> int:
    """メールの件数を取得する."""
    with DatabaseService() as db:
        return db.count_mails(folder, is_read)



def create_summary(summary_data: SummaryCreate, mail_id: int) -> Summary:
    """サマリを作成する."""
    with DatabaseService() as db:
        return db.create_summary(summary_data, mail_id)


def get_summary(summary_id: int) -> Optional[Summary]:
    """IDでサマリを取得する."""
    with DatabaseService() as db:
        return db.get_summary_by_id(summary_id)


def find_summary_by_mail_id(mail_id: int) -> Optional[Summary]:
    """メールIDでサマリを取得する."""
    with DatabaseService() as db:
        return db.get_summary_by_mail_id(mail_id)


def find_summary_by_message_id(message_id: str) -> Optional[Summary]:
    """メッセージIDでサマリを取得する."""
    with DatabaseService() as db:
        return db.get_summary_by_message_id(message_id)


def list_summaries(skip: int = 0, limit: int = 100) -> list[Summary]:
    """サマリ一覧を取得する."""
    with DatabaseService() as db:
        return db.get_summaries(skip, limit)


def update_summary(summary_id: int, summary_data: SummaryUpdate) -> Optional[Summary]:
    """サマリを更新する."""
    with DatabaseService() as db:
        return db.update_summary(summary_id, summary_data)


def delete_summary(summary_id: int) -> bool:
    """サマリを削除する."""
    with DatabaseService() as db:
        return db.delete_summary(summary_id)


def count_summaries() -> int:
    """サマリの件数を取得する."""
    with DatabaseService() as db:
        return db.count_summaries()


def create_mail_with_summary(mail_data: MailCreate, summary_content: str) -> tuple[Mail, Summary]:
    """メールとサマリを同時に作成する."""
    with DatabaseService() as db:
        return db.create_mail_with_summary(mail_data, summary_content)


def delete_mail_with_summary(mail_id: int) -> bool:
    """メールとそのサマリを削除する."""
    with DatabaseService() as db:
        return db.delete_mail_with_summary(mail_id)


def get_mail_with_summary(mail_id: int) -> Optional[tuple[Mail, Optional[Summary]]]:
    """メールとそのサマリを取得する."""
    with DatabaseService() as db:
        return db.get_mail_with_summary(mail_id)


# データベース初期化
def initialize_database() -> None:
    """データベースを初期化する（テーブル作成）."""
    from services.database.base import create_tables
    create_tables()
