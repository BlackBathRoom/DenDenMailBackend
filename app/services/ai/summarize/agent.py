from __future__ import annotations

from typing import TYPE_CHECKING, override

from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace
from langgraph.graph import END, START
from pydantic import BaseModel, Field

from services.ai.shared.ai_models import OpenVINOModels
from services.ai.shared.base import BaseGraph, BaseState
from services.ai.shared.base import OpenVINOLLM as BaseOV

if TYPE_CHECKING:
    from langchain_core.runnables import Runnable
    from langgraph.graph import StateGraph


class SummarizeAgentState(BaseState[str]):
    source_text: str


class ResponseFormatter(BaseModel):
    summary: str = Field(..., description="result of summarization")


class Phi4Mini(BaseOV):
    """設定をPhi-4-mini用に調整したクラス."""

    @property
    @override
    def llm(self) -> Runnable:
        return ChatHuggingFace(llm=self.ov_llm).bind(skip_prompt=True)


# TODO: パラメータは要検討 # noqa: FIX002
llm = Phi4Mini.from_model(
    OpenVINOModels.PHI_4_MINI_INSTRUCT,
    max_new_tokens=65536,
    do_sample=True,
    temperature=0.1,
).llm

system_message = """# Instruction
Please summarize the user message in its original language according to the following points.
You should output only the summary without any additional information.

## Key Points for Summarization

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

prompt = PromptTemplate(template=system_message, input_variables=["source_text"])


class SummarizeAgentGraph(BaseGraph[SummarizeAgentState, str]):
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
        formatted_message = prompt.format_prompt(source_text=state["source_text"])
        resp = llm.invoke([HumanMessage(content=formatted_message.to_string())])
        state["result"] = resp.content
        return {**state, "result": resp.content}


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

    graph = SummarizeAgentGraph()
    state = SummarizeAgentState(source_text=sample_mail)
    result = graph.invoke(state)
    print(result)  # noqa: T201
