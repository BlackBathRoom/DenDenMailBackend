from __future__ import annotations

from typing import TYPE_CHECKING, NotRequired

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START
from pydantic import BaseModel

from app_resources import app_resources
from services.ai.rag.chroma_manager import ChromaManager
from services.ai.rag.vector_message import VectorMessage
from services.ai.shared.base import BaseGraph, BaseState
from utils.logging import get_logger

if TYPE_CHECKING:
    from langgraph.graph import StateGraph


logger = get_logger(__name__)


class Return(BaseModel):
    response: str
    message_ids: list[int]


class RAGAgentState(BaseState[Return]):
    user_input: str
    messages: NotRequired[list[VectorMessage]]


MESSAGE_THRESHOLD = 0.5
TOP_K = 3


class RAGAgentGraph(BaseGraph[RAGAgentState, Return]):
    def __init__(self) -> None:
        self.state_type = RAGAgentState
        super().__init__()

    def create_graph(self, builder: StateGraph[RAGAgentState]) -> StateGraph[RAGAgentState]:
        builder.add_node("query", self._query_vector_store)
        builder.add_node("response", self._response)

        builder.add_edge(START, "query")
        builder.add_edge("query", "response")
        builder.add_edge("response", END)

        return builder

    def _query_vector_store(self, state: RAGAgentState) -> dict[str, list[VectorMessage]]:
        manager = ChromaManager()
        query = state["user_input"]
        results = manager.similarity_search(query, top_k=TOP_K)
        return {
            "messages": [
                VectorMessage(message=res.message, message_id=res.message_id, section_id=res.section_id)
                for res in results
                if res.score > MESSAGE_THRESHOLD
            ]
        }

    def _gen_docs_prompt(self, messages: list[VectorMessage]) -> str:
        prompt = "文書:\n"
        docs = [f"ID {m.message_id}: {m.message}" for m in messages]
        prompt += "\n".join(docs)
        return prompt

    def _response(self, state: RAGAgentState) -> dict[str, str]:
        if (messages := state.get("messages")) is None:
            msg = "No messages found"
            raise ValueError(msg)

        model = app_resources.get_chat_model()
        messages = [
            SystemMessage(content="ユーザーの質問に与える文書を用いて回答を行ってください。"),
            SystemMessage(content=self._gen_docs_prompt(messages)),
            HumanMessage(content=state["user_input"]),
        ]
        resp = model.invoke(messages)
        if not isinstance(resp.content, str):
            msg = "Unexpected response type"
            raise TypeError(msg)
        return {"response": resp.content}


if __name__ == "__main__":
    app_resources.load_model()

    cm = ChromaManager()

    def add_documents() -> None:
        cm.add_documents(
            [
                VectorMessage(
                    message="新商品プロモーションに関するミーティングを火曜日午後２時から開催します。",
                    message_id="msg1",
                    section_id="sec1",
                ),
                VectorMessage(
                    message="Hoge社と新しい製品の開発に協力するための契約を締結しました。この契約により、双方は新しい製品の開発に協力し、共同開発の成果を共有することになりました。",
                    message_id="msg2",
                    section_id="sec2",
                ),
                VectorMessage(
                    message="Zoom上で開催します。参加者はfugaに資料の共有を、月曜の午前中に行ってください。",
                    message_id="msg3",
                    section_id="sec3",
                ),
            ]
        )

    add_documents()

    agent = RAGAgentGraph()
    user_input = "hoge社との契約の内容は?"
    res = agent.invoke({"user_input": user_input})
    logger.info("result: %s", res)
