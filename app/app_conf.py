import os
from enum import Enum
from pathlib import Path

from sqlmodel import create_engine


# type
class MailVender(str, Enum):
    """メールクライアントの列挙型."""

    OUTLOOK = "Outlook"


# database
DB_PATH = Path(__file__).parent.parent / "database" / "db.sqlite3"


connect_args = {"check_same_thread": False}
if os.name == "nt":  # Windows
    connect_args.update({
        "timeout": 20,  
        "isolation_level": None,  
    })

engine = create_engine(
    f"sqlite:///{DB_PATH}", 
    echo=True, 
    connect_args=connect_args,
    pool_pre_ping=True,  # 接続の健全性をチェック
)
