from enum import Enum
from pathlib import Path
from typing import Self


# type
class MailVendor(str, Enum):
    """メールクライアントの列挙型."""

    THUNDERBIRD = "Thunderbird"

    @classmethod
    def from_str(cls, value: str) -> Self:
        """大小/前後空白無視で name/value を解決する."""
        if isinstance(value, cls):
            return value
        s = value.strip()
        for m in cls:
            if m.value.lower() == s.lower() or m.name.lower() == s.lower():
                return m
        msg = f"Unsupported vender: {value}"
        raise ValueError(msg)

    @classmethod
    def _missing_(cls, value: object) -> Self | None:
        """Enum(value) 構築時の大小無視解決を有効化する."""
        if isinstance(value, str):
            s = value.strip()
            for m in cls:
                if m.value.lower() == s.lower() or m.name.lower() == s.lower():
                    return m
        return None


# path
BASE_DIR = Path(__file__).parent.parent
BASE_DIR.absolute()

# ai model
AI_MODEL_PATH = BASE_DIR / "ai_models"

# database
DB_PATH = BASE_DIR / "database" / "db.sqlite3"

# OpenVINO
OV_CONFIG = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}

# HTML sanitize (bleach) configuration
# - EXTRA_TAGS: bleach の既定タグに union して使用します
# - ALLOWED_ATTRS / ALLOWED_PROTOCOLS: そのまま使用します
CANDIDATE_ENCODINGS = ("utf-8", "cp932", "iso-2022-jp", "euc_jp", "latin-1")

HTML_SANITIZE_EXTRA_TAGS = {
    "p",
    "br",
    "img",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "td",
    "th",
    "span",
    "div",
    "pre",
    "code",
    "ul",
    "ol",
    "li",
    "blockquote",
    "hr",
}

HTML_SANITIZE_ALLOWED_ATTRS = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
    "table": ["border"],
}

HTML_SANITIZE_ALLOWED_PROTOCOLS = ("http", "https", "mailto")
