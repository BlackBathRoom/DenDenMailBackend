from __future__ import annotations

from typing import TYPE_CHECKING

from openvino import Core
from optimum.intel.openvino import OVModelForCausalLM
from transformers import AutoTokenizer

from app_conf import AI_MODEL_PATH
from utils.logging import get_logger

if TYPE_CHECKING:
    from optimum.modeling_base import OptimizedModel
    from transformers.tokenization_utils import PreTrainedTokenizer
    from transformers.tokenization_utils_fast import PreTrainedTokenizerFast

    from services.ai.ai_models import OpenVINOModels


logger = get_logger(__name__)


def _convert_model_id_to_dir_name(model_id: str) -> str:
    return model_id.replace("/", "_")


def _resolve_device() -> str:
    devices = Core().available_devices
    logger.info("Available devices: %s", devices)

    if "NPU" in devices:
        return "NPU"
    if "GPU" in devices:
        return "GPU"
    return "CPU"


def load_ov_model(
    model_id: OpenVINOModels, ov_config: dict[str, str]
) -> tuple[OptimizedModel, PreTrainedTokenizer | PreTrainedTokenizerFast | None]:
    model_path = (AI_MODEL_PATH / _convert_model_id_to_dir_name(model_id.value)).resolve()
    is_downloaded = model_path.exists()
    device = _resolve_device()

    tokenizer = AutoTokenizer.from_pretrained(model_path if is_downloaded else model_id.value)
    ov_model = OVModelForCausalLM.from_pretrained(
        model_id=str(model_path) if is_downloaded else model_id.value,
        device=device,
        ov_config=ov_config,
    )

    if not is_downloaded:
        ov_model.save_pretrained(model_path)
        tokenizer.save_pretrained(model_path)

    return ov_model, tokenizer


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
    from transformers.pipelines import pipeline

    from services.ai.ai_models import OpenVINOModels

    model_id = OpenVINOModels.PHI_4_MINI_INSTRUCT
    ov_config = {"PERFORMANCE_HINT": "LATENCY", "NUM_STREAMS": "1", "CACHE_DIR": ""}

    ov_model, tokenizer = load_ov_model(model_id=model_id, ov_config=ov_config)

    ov_pipe = pipeline(
        task="text-generation",
        model=ov_model,  # type: ignore[arg-type]
        tokenizer=tokenizer,
        max_new_tokens=1024,
        do_sample=True,
    )
    ov_llm = HuggingFacePipeline(pipeline=ov_pipe)
    llm = ChatHuggingFace(llm=ov_llm).bind(skip_prompt=True)

    con = [
        SystemMessage(content="あなたは優秀なアシスタントです。"),
        HumanMessage(content="次の文章を敬体に書き換えてください。\n\n今日はいい天気ですね。"),
    ]
    for chunk in llm.stream(con):
        print(chunk.content, end="", flush=True)  # noqa: T201
