from __future__ import annotations

from pydantic import BaseModel

from services.ai.shared.base import BaseGraph, BaseState


class Return(BaseModel):
    response: str
    message_ids: list[int]

class RAGAgentState(BaseState[Return]):
    pass

class RAGAgentGraph(BaseGraph[RAGAgentState, Return]):
    pass
