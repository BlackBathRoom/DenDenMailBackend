from sqlalchemy.engine import Engine

from app_conf import CANDIDATE_ENCODINGS
from services.ai.summarize import SummarizeAgentGraph, SummarizeAgentState
from services.database.engine import get_engine
from services.database.manager import MessagePartDBManager, SummaryDBManager
from usecases.errors import MessageNotFoundError, PlainTextRequiredError
from utils.logging import get_logger

logger = get_logger(__name__)


def _get_existing_summary_text(engine: Engine, message_id: int) -> str | None:
    summary_manager = SummaryDBManager()
    rows = summary_manager.read(
        engine,
        conditions=[{"operator": "eq", "field": "message_id", "value": message_id}],
        limit=1,
    )
    if rows:
        return rows[0].content
    return None


def _get_plain_text_body(engine: Engine, message_id: int) -> str | None:
    """Return decoded text/plain content of the message.

    Raises PlainTextRequiredError when no text/plain part exists.
    """
    part_manager = MessagePartDBManager()
    parts = part_manager.read(
        engine,
        conditions=[{"operator": "eq", "field": "message_id", "value": message_id}],
    )
    if not parts:
        msg = "Message parts not found"
        raise MessageNotFoundError(msg)

    # pick first non-attachment text/plain
    for p in parts:
        if not p.is_attachment and (p.mime_type, p.mime_subtype) == ("text", "plain"):
            content = p.content
            if content is None:
                continue
            try:
                return content.decode("utf-8")
            except UnicodeDecodeError:
                for enc in CANDIDATE_ENCODINGS:
                    try:
                        return content.decode(enc)
                    except UnicodeDecodeError:
                        continue
                # last resort
                return content.decode("utf-8", errors="replace")

    return None


def create_summary(message_id: int, *, engine: Engine | None = None) -> str:
    """Create or fetch a summary for a message and return its text.

    Behavior:
    1) If a summary already exists for the message_id, return it.
    2) Otherwise, generate a summary from the first text/plain body, save, and return it.
    3) If the message doesn't have a text/plain part, raise PlainTextRequiredError.
    """
    engine = engine or get_engine()

    existing = _get_existing_summary_text(engine, message_id)
    if existing is not None:
        logger.debug("Summary already exists for message_id=%s", message_id)
        return existing

    source_text = _get_plain_text_body(engine, message_id)
    if source_text is None:
        msg = "No text/plain body found for summarization"
        raise PlainTextRequiredError(msg)

    agent = SummarizeAgentGraph()
    state = SummarizeAgentState(source_text=source_text)
    result = agent.invoke(state)
    if result is None:
        msg = "Summarization returned no result"
        raise RuntimeError(msg)

    SummaryDBManager().add_summary(engine, message_id, result)
    logger.info("Summary created for message_id=%s", message_id)
    return result
