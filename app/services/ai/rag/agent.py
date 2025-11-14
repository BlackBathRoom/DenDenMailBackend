from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable

try:
    from langgraph.graph import END, START, StateGraph  # type: ignore[import]

    _HAS_LANGGRAPH = True
except (ImportError, ModuleNotFoundError):
    # langgraph が無い場合にフォールバック
    _HAS_LANGGRAPH = False
    START = "START"
    END = "END"

    class StateGraph:
        def __init__(self, _state_type: type) -> None:
            self._nodes: dict[str, Callable] = {}
            self._start: str | None = None

        def add_node(self, name: str, fn: Callable) -> None:
            self._nodes[name] = fn

        def add_edge(self, a: str, b: str) -> None:
            # simple linear workflow: remember start node name
            if a == START:
                self._start = b

        def compile(self) -> object:
            nodes = self._nodes
            start = self._start

            class Compiled:
                def __init__(self, nodes: dict, start: str | None) -> None:
                    self._nodes = nodes
                    self._start = start

                def invoke(self, state: MailState) -> MailState:
                    if not self._start:
                        return state
                    fn = self._nodes.get(self._start)
                    if not fn:
                        return state
                    return fn(state)

            return Compiled(nodes, start)


import re

from pydantic import BaseModel

from app.utils.logging._get_logger import get_logger

logger = get_logger(__name__)


# 状態定義
class MailState(BaseModel):
    source_text: str = ""
    summary: str = ""


# SummarizeAgentGraph が利用可能かをトップレベルで判定する
try:
    from app.services.ai.summarize.agent import SummarizeAgentGraph  # type: ignore[import]
except (ImportError, ModuleNotFoundError):
    SummarizeAgentGraph = None  # type: ignore[assignment]


# あなたの SummarizeAgent をノードとしてラップ
def summarize_node(state: MailState) -> MailState:
    """要約ノード.

    - まず `app.services.ai.summarize.agent.SummarizeAgentGraph` を使って要約を実行する。
    - それが利用できない場合は簡易フォールバックで最初の文を返す。
    """
    # LLM 要約対応ノード (トップレベルで import の可否を判定)
    if SummarizeAgentGraph is None:
        txt = (state.source_text or "").strip()
        m = re.search(r"(.+?[。.!?])", txt)
        if m:
            state.summary = m.group(1).strip()
        else:
            state.summary = txt[:300]
        return state

    agent = SummarizeAgentGraph()
    # SummarizeAgentGraph.invoke は (元実装) 最終要約文字列を返す想定
    res = None
    try:
        res = agent.invoke(state)
    except (ConnectionError, TimeoutError):
        logger.exception("LLM接続エラー")
        state.summary = "(要約処理中にエラーが発生しました)"

    # 一部の実装では invoke が存在せず invoke_all になる可能性に対応
    if hasattr(agent, "invoke_all"):
        fn = agent.invoke
        out = fn(cast("object", state))
        # out could be dict-like
        # prefer key 'summarizer' or first value when dict-like
        res = next(iter(out.values()), None) if isinstance(out, dict) else out

    state.summary = res or ""
    return state


# グラフ構築
graph = StateGraph(MailState)
graph.add_node("summarize", summarize_node)
graph.add_edge(START, "summarize")
graph.add_edge("summarize", END)
workflow = cast("Any", graph.compile())

# 実行例
if __name__ == "__main__":
    init = MailState(
        source_text=(
            "営業部 foo様 いつも大変お世話になっております。Fuga株式会社のbarです。"
            "候補日は9月12日(木)14:00〜15:00です。"
        )
    )
    result = workflow.invoke(init)
    logger.info("要約結果: %s", result.summary)
