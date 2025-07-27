"""データベース操作関連のモジュール."""


from .helpers import (
    create_mail,
    get_mail,
    find_mail_by_message_id,
    list_mails,
    update_mail,
    delete_mail,
    mark_as_read,
    mark_as_unread,
    move_to_folder,
    count_mails,
    

    create_summary,
    get_summary,
    find_summary_by_mail_id,
    find_summary_by_message_id,
    list_summaries,
    update_summary,
    delete_summary,
    count_summaries,
    
    create_mail_with_summary,
    delete_mail_with_summary,
    get_mail_with_summary,
    
    initialize_database,
)

from .database_service import DatabaseService
from .mail_crud import MailCRUD
from .summary_crud import SummaryCRUD
from .base import get_session, create_tables

__all__ = [
    "create_mail",
    "get_mail", 
    "find_mail_by_message_id",
    "list_mails",
    "update_mail",
    "delete_mail",
    "mark_as_read",
    "mark_as_unread",
    "move_to_folder",
    "count_mails",
    "create_summary",
    "get_summary",
    "find_summary_by_mail_id",
    "find_summary_by_message_id",
    "list_summaries",
    "update_summary",
    "delete_summary",
    "count_summaries",
    "create_mail_with_summary",
    "delete_mail_with_summary",
    "get_mail_with_summary",
    "initialize_database",
    
    "DatabaseService",
    "MailCRUD",
    "SummaryCRUD",
    "get_session",
    "create_tables",
]