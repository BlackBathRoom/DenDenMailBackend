from enum import Enum
from pathlib import Path


# type
class MailVender(str, Enum):
    """メールクライアントの列挙型."""

    OUTLOOK = "Outlook"
    THUNDERBIRD = "Thunderbird"


# path
BASE_DIR = Path(__file__).parent.parent
BASE_DIR.absolute()

# ai model
AI_MODEL_PATH = BASE_DIR / "ai_models"

# database
DB_PATH = BASE_DIR / "database" / "db.sqlite3"

# OpenVINO
OV_CONFIG = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}
