from enum import Enum
from pathlib import Path

from sqlmodel import create_engine


# type
class MailVender(str, Enum):
    """メールクライアントの列挙型."""

    OUTLOOK = "Outlook"
    THUNDERBIRD = "Thunderbird"


# path
BASE_DIR = Path(__file__).parent.parent

# ai model
AI_MODEL_PATH = BASE_DIR / "ai_models"

# database
DB_PATH = BASE_DIR / "database" / "db.sqlite3"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=True, connect_args={"check_same_thread": False})

# OpenVINO
OV_CONFIG = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}
