"""LangGraph-based summary flow (minimal, safe to import).

Provides a small, safe-to-import interface for summarization. If
``langgraph`` is available it will be used; otherwise a tiny fallback
extractive summarizer is used.
"""

from __future__ import annotations

import re
from typing import Any

try:
    # Optional import - fall back if not available.
    import langgraph

    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


def _fallback_summarize(text: str, max_sentences: int = 3) -> str:
    if not text:
        return ""
    sentences = re.split(r"(?<=[。.!?])\s*|\n+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return "\n".join(sentences[:max_sentences])


def summarize_text(text: str) -> str:
    """Return a short summary for the given ``text``.

    Uses LangGraph when available; otherwise a simple extractive
    fallback is returned.
    """
    if not text:
        return ""

    if HAS_LANGGRAPH:
        try:
            graph: Any = langgraph.Graph()
            prompt = f"以下のメール本文を3文程度で日本語で要約してください。\n---\n{text}\n---"
            node = graph.add_node("prompt", prompt=prompt)
            run = graph.run(node)
            return getattr(run, "text", str(run))
        except Exception:
            return _fallback_summarize(text)

    return _fallback_summarize(text)
