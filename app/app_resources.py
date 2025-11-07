from threading import Lock
from typing import Self

from langchain_openvino_genai import ChatOpenVINO, OpenVINOLLM
from langchain_openvino_genai.load_model import load_model as _load_model
from openvino import Core

from app_conf import AI_MODEL_PATH
from errors import ModelNotLoadedError
from services.ai.shared.ai_models import OpenVINOModels
from utils.logging import get_logger

logger = get_logger(__name__)


def _resolve_device() -> str:
    devices = Core().available_devices
    logger.info("Available devices: %s", devices)

    if "NPU" in devices:
        return "NPU"
    if "GPU" in devices:
        return "GPU"
    return "CPU"


class AppResources:
    _instance: Self | None = None

    model: OpenVINOLLM | None = None
    chat_model: ChatOpenVINO | None = None
    load_lock: Lock

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_lock = Lock()
        return cls._instance

    def load_model(self) -> None:
        """Load the shared AI model if necessary and return it."""
        if self.model is not None:
            return

        with self.load_lock:
            if self.model is not None:
                return

            logger.info("Loading AI model.")
            model_path = _load_model(repo_id=OpenVINOModels.QWEN3_8B.value, download_path=AI_MODEL_PATH)
            ov_llm = OpenVINOLLM.from_model_path(model_path, device=_resolve_device())
            loaded_model = ChatOpenVINO(llm=ov_llm)
            self.model = ov_llm
            self.chat_model = loaded_model

    def get_model(self) -> OpenVINOLLM:
        """Return a ready-to-use AI model, loading it on demand."""
        if self.model is None:
            msg = "Model is not loaded yet."
            raise ModelNotLoadedError(msg)
        return self.model

    def get_chat_model(self) -> ChatOpenVINO:
        if self.chat_model is None:
            self.chat_model = ChatOpenVINO(llm=self.model)
        return self.chat_model


app_resources = AppResources()
