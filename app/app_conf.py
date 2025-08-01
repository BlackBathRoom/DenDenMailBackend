from enum import Enum
from pathlib import Path

from sqlmodel import create_engine


# type
class MailVender(str, Enum):
    """メールクライアントの列挙型."""

    OUTLOOK = "Outlook"


# database
DB_PATH = Path(__file__).parent.parent / "database" / "db.sqlite3"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=True, connect_args={"check_same_thread": False})
