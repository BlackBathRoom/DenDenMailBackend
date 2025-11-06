from threading import Lock
from typing import Literal, Self

from langchain_openvino_genai import ChatOpenVINO, OpenVINOLLM
from langchain_openvino_genai.load_model import load_model as _load_model
from openvino import Core

from app_conf import AI_MODEL_PATH
from errors import ModelNotLoadedError
from services.ai.shared.ai_models import OpenVINOModels
from utils.logging import get_logger

logger = get_logger(__name__)

type ModelStatus = Literal["idle", "loading", "ready"]


class AIModel(ChatOpenVINO):
    status: ModelStatus = "idle"

    def switch_status(self, new_status: ModelStatus) -> None:
        self.status = new_status


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

    model: AIModel | None = None
    load_lock: Lock

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_lock = Lock()
        return cls._instance

    def load_model(self) -> AIModel:
        """Load the shared AI model if necessary and return it."""
        if self.model is not None and self.model.status != "idle":
            return self.model

        with self.load_lock:
            if self.model is not None and self.model.status == "ready":
                return self.model

            logger.info("Loading AI model.")
            model_path = _load_model(repo_id=OpenVINOModels.PHI_4_MINI_INSTRUCT.value, download_path=AI_MODEL_PATH)
            ov_llm = OpenVINOLLM.from_model_path(model_path, device=_resolve_device())
            loaded_model = AIModel(llm=ov_llm, verbose=True)
            self.model = loaded_model
            self.model.switch_status("ready")
        return self.model

    def get_model(self) -> AIModel:
        """Return a ready-to-use AI model, loading it on demand."""
        if self.model is None:
            msg = "Model is not loaded yet."
            raise ModelNotLoadedError(msg)
        return self.model


app_resources = AppResources()
