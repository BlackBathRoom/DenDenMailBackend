from __future__ import annotations

from typing import Callable, cast

try:
    from langgraph.graph import StateGraph, START, END  # type: ignore

    _HAS_LANGGRAPH = True
except Exception:
    # 軽量フォールバック（langgraph が無くても簡易ワークフローを実行可能にする）
    _HAS_LANGGRAPH = False
    START = "START"
    END = "END"

    class StateGraph:
        def __init__(self, state_type: type):
            self._nodes: dict[str, Callable] = {}
            self._start: str | None = None

        def add_node(self, name: str, fn: Callable) -> None:
            self._nodes[name] = fn

        def add_edge(self, a: str, b: str) -> None:
            # simple linear workflow: remember start node name
            if a == START:
                self._start = b

        def compile(self):
            nodes = self._nodes
            start = self._start

            class Compiled:
                def __init__(self, nodes: dict, start: str | None):
                    self._nodes = nodes
                    self._start = start

                def invoke(self, state):
                    if not self._start:
                        return state
                    fn = self._nodes.get(self._start)
                    if not fn:
                        return state
                    return fn(state)

            return Compiled(nodes, start)


from pydantic import BaseModel


# 状態定義
class MailState(BaseModel):
    source_text: str = ""
    summary: str = ""


# あなたの SummarizeAgent をノードとしてラップ
def summarize_node(state: MailState) -> MailState:
    """要約ノード。

    - まず `app.services.ai.summarize.agent.SummarizeAgentGraph` を使って要約を実行する。
    - それが利用できない場合は簡易フォールバックで最初の文を返す。
    """
    # LLM 要約対応ノード
    """from app.services.ai.summarize.agent import SummarizeAgentGraph
    agent = SummarizeAgentGraph()
    res = agent.invoke(cast(object, state))
    """
    try:
        from app.services.ai.summarize.agent import SummarizeAgentGraph  # type: ignore

        agent = SummarizeAgentGraph()
        # SummarizeAgentGraph.invoke は（元実装）最終要約文字列を返す想定
        res = None
        try:
            # 型が異なるためキャストして呼び出す（実行時は問題ない想定）
            res = agent.invoke(cast(object, state))
        except Exception:
            # 一部の実装では invoke が存在せず invoke_all になる可能性に対応
            if hasattr(agent, "invoke_all"):
                fn = getattr(agent, "invoke_all")
                out = fn(cast(object, state))
                # out could be dict-like
                if isinstance(out, dict):
                    # prefer key 'summarizer' or first value
                    res = next(iter(out.values()), None)
                else:
                    res = out
        state.summary = res or ""
        return state
    except Exception:
        # フォールバック要約（最初の文を抽出）
        import re

        txt = (state.source_text or "").strip()
        m = re.search(r"(.+?[。．.!?])", txt)
        if m:
            state.summary = m.group(1).strip()
        else:
            state.summary = txt[:300]
        return state


# グラフ構築
graph = StateGraph(MailState)
graph.add_node("summarize", summarize_node)
graph.add_edge(START, "summarize")
graph.add_edge("summarize", END)
workflow = graph.compile()

# 実行例
if __name__ == "__main__":
    init = MailState(
        source_text="営業部 foo様 いつも大変お世話になっております。Fuga株式会社のbarです。候補日は9月12日（木）14:00〜15:00です。"
    )
    result = workflow.invoke(init)
    print("要約結果:", result.summary)
