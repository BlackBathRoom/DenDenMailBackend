from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict, TypeVar

from langgraph.graph import StateGraph

from utils.check_implementation import check_implementation
from utils.logging import get_logger

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage
    from langgraph.graph.state import CompiledStateGraph
    from pydantic import BaseModel

logger = get_logger(__name__)


type GraphReturn = BaseMessage | dict[str, Any] | BaseModel | str

R = TypeVar("R", bound=GraphReturn)


class BaseState[R: GraphReturn](TypedDict):
    result: NotRequired[R]


class BaseGraph[TState: BaseState[str], TReturn: GraphReturn](ABC):
    """エージェントの状態遷移グラフの基底クラス.

    Usage:

    ```python
    type MyReturn = str


    class MyState(BaseState[MyReturn]):
        user_input: str


    class MyGraph(BaseGraph[MyState, MyReturn]):
        def __init__(self):
            self.state_type = MyState
            super().__init__()

        def create_graph(self, builder: StateGraph[MyState]) -> StateGraph[MyState]:
            # グラフの構築ロジック
            return builder


    graph = MyGraph()
    result = graph.invoke(MyState(user_input="Hello"))
    print(result)  # 最終状態のレスポンス
    ```
    """

    state_type: type[TState]

    @abstractmethod
    def __init__(self) -> None:
        self.graph = self._compile_graph()

    @abstractmethod
    @check_implementation
    def create_graph(self, builder: StateGraph[TState]) -> StateGraph[TState]:
        """エージェントの状態遷移グラフを構築する.

        Args:
            builder (StateGraph): グラフビルダー.

        Returns:
            StateGraph: 構築したグラフ.
        """

    def _compile_graph(self) -> CompiledStateGraph[TState]:
        if not hasattr(self, "state_type"):
            msg = "state_type is not defined."
            raise NotImplementedError(msg)
        graph = self.create_graph(StateGraph(self.state_type))
        return graph.compile()

    def invoke(self, state: TState) -> TReturn | None:
        """状態遷移グラフを実行する.

        Args:
            state (TState): 初期状態.
            return_response (bool, optional): 最終状態のレスポンスを返すかどうか. Defaults to False.

        Returns:
            TReturn | None: 最終状態のレスポンスまたはNone.
        """
        logger.debug("Invoking graph with state: %s", state)
        resp = self.graph.invoke(state)
        logger.debug("Graph invocation completed with response: %s", resp)

        if isinstance(resp, dict) and "result" in resp:
            return resp["result"]
        logger.warning("No result found in the final state.")
        return None
