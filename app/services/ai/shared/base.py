from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, NotRequired, Self, TypedDict, TypeVar, Unpack

from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langgraph.graph import StateGraph
from transformers.pipelines import pipeline

from app_conf import OV_CONFIG
from services.ai.shared.load_model import load_ov_model
from utils.check_implementation import check_implementation
from utils.logging import get_logger

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage
    from langchain_core.runnables import Runnable
    from langgraph.graph.state import CompiledStateGraph
    from optimum.modeling_base import OptimizedModel
    from pydantic import BaseModel
    from transformers.tokenization_utils import PreTrainedTokenizer
    from transformers.tokenization_utils_fast import PreTrainedTokenizerFast

    from services.ai.shared.ai_models import OpenVINOModels

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


# TODO: 各パラメータの詳細な型定義  # noqa: FIX002
class PipelineParams(TypedDict, total=False):
    max_new_tokens: int
    do_sample: bool
    top_k: int
    top_p: float
    temperature: float
    repetition_penalty: float


class OpenVINOLLM:
    def __init__(
        self,
        optimized_model: OptimizedModel,
        tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast,
        **kwargs: Unpack[PipelineParams],
    ) -> None:
        self.optimized_model = optimized_model
        self.tokenizer = tokenizer
        self.params = kwargs
        self.ov_llm = self._init_ov_llm()

    def _init_ov_llm(self) -> HuggingFacePipeline:
        return HuggingFacePipeline(
            pipeline=pipeline(
                task="text-generation",
                model=self.optimized_model,  # type: ignore[arg-type]
                tokenizer=self.tokenizer,
                **self.params,
            )
        )

    @property
    def llm(self) -> Runnable:
        return ChatHuggingFace(llm=self.ov_llm)

    @classmethod
    def from_model(cls, model: OpenVINOModels, **kwargs: Unpack[PipelineParams]) -> Self:
        return cls(*load_ov_model(model, OV_CONFIG), **kwargs)
