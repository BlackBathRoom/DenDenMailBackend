from __future__ import annotations

import re

from collections.abc import Callable
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.utils.logging._get_logger import get_logger

logger = get_logger(__name__)

# summary length limit constant
SUMMARY_MAX_LENGTH = 300


def _raise_type_error(msg: str) -> None:
    """Helper to raise a TypeError from a common point.

    Extracted to module-level to keep raise statements out of nested scopes
    and satisfy static analysis rules.
    """
    raise TypeError(msg)


# `override` decorator: prefer stdlib, fall back to typing_extensions or noop
try:
    from typing import override  # type: ignore[import]
except (ImportError, ModuleNotFoundError):
    try:
        from typing import override  # type: ignore[import]
    except (ImportError, ModuleNotFoundError):

        def override(func: Callable) -> Callable:
            return func


# PromptTemplate: optional dependency (langchain_core)
try:
    from langchain_core.prompts import PromptTemplate  # type: ignore[import]

    _HAS_PROMPT_TEMPLATE = True
except (ImportError, ModuleNotFoundError):
    _HAS_PROMPT_TEMPLATE = False

    class PromptTemplate:  # minimal fallback
        def __init__(self, template: str, input_variables: list[str] | None = None) -> None:
            self.template = template
            # store input_variables for API compatibility
            self.input_variables = input_variables

        def format(self, **kwargs: object) -> str:
            try:
                return self.template.format(**{k: str(v) for k, v in kwargs.items()})
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                logger.debug("PromptTemplate.format primary format failed: %s", exc)
                try:
                    if "source_text" in kwargs:
                        return self.template.replace("{source_text}", str(kwargs.get("source_text")))
                except (AttributeError, TypeError) as exc2:
                    logger.debug("PromptTemplate.format fallback replace failed: %s", exc2)
                return self.template

        def format_prompt(self, **kwargs: object) -> str:
            return self.format(**kwargs)


# langgraph END/START are optional at runtime
try:
    from langgraph.graph import END, START

    _HAS_LANGGRAPH = True
except (ImportError, ModuleNotFoundError):
    END = "END"
    START = "START"
    _HAS_LANGGRAPH = False


# Avoid importing services.ai.shared.base at module import time because it may
# import langgraph; use TYPE_CHECKING for typing and simple runtime stubs.
if TYPE_CHECKING:
    from collections.abc import Callable

    from langgraph.graph import StateGraph

    from services.ai.shared.base import BaseGraph, BaseState
else:

    class BaseState(dict):
        pass

    class BaseGraph:  # runtime stub
        def invoke(self, state: object) -> object:
            raise NotImplementedError


class SummarizeAgentState(BaseState):
    source_text: str


class ResponseFormatter(BaseModel):
    summary: str = Field(..., description="result of summarization", min_length=1, max_length=SUMMARY_MAX_LENGTH)


system_message = """# Instruction
Please summarize the Source Text in its original language according to the following Key Points.
You should output only the summary without any additional information.
The preferred length for summaries is 1 to 300 characters.

## Key Points

1. Capture the overall picture
- Purpose (what the document is for)
- Conclusion (the main message)
- Important figures/facts (deadlines, costs, results, etc.)

2. Keep only what the reader needs and the structure simple
- Retain only information necessary for the reader to make a "decision" or "take action"
- Organize in the order: "Conclusion → Reason → Supplement"

3. Parts that can be omitted
- Overly polite phrasing
- Repetitive expressions
- Auxiliary background explanations

## Source Text
{source_text}"""

prompt_template = PromptTemplate(template=system_message, input_variables=["source_text"])


def summarize_text_sample(text: str) -> str:
    """簡易要約フォールバック。最初の文を抽出して最大300文字に切り詰める."""
    if not text:
        return ""

    m = re.search(r"(.+?[。.!?])", text.strip())
    s = m.group(1).strip() if m else text.strip()
    return s if len(s) <= SUMMARY_MAX_LENGTH else s[: SUMMARY_MAX_LENGTH - 3] + "..."


class SummarizeAgentGraph(BaseGraph):
    @override
    def __init__(self) -> None:
        self.state_type = SummarizeAgentState
        super().__init__()

    @override
    def create_graph(self, builder: StateGraph[SummarizeAgentState]) -> StateGraph[SummarizeAgentState]:
        builder.add_node("summarize", self._summarize)

        builder.add_edge(START, "summarize")
        builder.add_edge("summarize", END)

        return builder

    def _summarize(self, state: SummarizeAgentState) -> SummarizeAgentState:
        # LLM/model backend を遅延インポートして実行。失敗したらフォールバック要約を返す。
        result = None
        try:
            from app_resources import app_resources  # noqa: PLC0415

            model = app_resources.get_model().with_structured_output(ResponseFormatter)
            prompt = prompt_template.format_prompt(source_text=state["source_text"])
            resp = model.invoke(prompt)

            if isinstance(resp, ResponseFormatter):
                result = resp.summary
            elif isinstance(resp, dict) and (r := resp.get("summary")) is not None and isinstance(r, str):
                result = r
            else:
                _msg = "Unexpected response format from the model."
                _raise_type_error(_msg)
        except Exception:  # noqa: BLE001
            result = summarize_text_sample(state["source_text"])

        return {**state, "result": result}


if __name__ == "__main__":
    sample_mail = """株式会社Hoge
営業部 foo様

いつも大変お世話になっております。Fuga株式会社のbarです。

先日の打ち合わせでは貴重なお時間をいただき、誠にありがとうございました。
ご相談していた新商品の共同プロモーションの件ですが、次回の詳細打ち合わせを以下の日程で実施できればと考えております。

候補日: 9月12日（木）14:00〜15:00、または 9月13日（金）10:00〜11:00

開催方法: オンライン（Zoom予定）

また、当日議論をスムーズに進めるため、御社側でご検討いただいた施策案がありましたら、9月10日（火）までにご共有いただけますと幸いです。

なお、弊社からは参考資料を別途添付しておりますので、ご確認ください。

どうぞよろしくお願いいたします。

―――――――――――
Fuga株式会社　bar
"""  # noqa: RUF001
    try:
        from app_resources import app_resources

        app_resources.load_model()
    except (ImportError, ModuleNotFoundError) as exc:
        logger.debug("app_resources not available during sample run: %s", exc)
    graph = SummarizeAgentGraph()
    state = SummarizeAgentState(source_text=sample_mail)
    result = graph.invoke(state)
    logger.info("%s", result)
