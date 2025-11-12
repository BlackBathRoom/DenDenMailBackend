from enum import Enum
from pathlib import Path

from huggingface_hub import snapshot_download
from langchain_huggingface import HuggingFaceEmbeddings
from optimum.intel import OVQuantizationConfig
from sentence_transformers import (
    SentenceTransformer,
    export_static_quantized_openvino_model,
)

from app.app_conf import AI_MODEL_PATH


class EmbeddingModels(Enum):
    RURI_V3_30M = "cl-nagoya/ruri-v3-30m"
    RURI_V3_130M = "cl-nagoya/ruri-v3-130m"


def _download_model(model: EmbeddingModels) -> Path:
    model_name = model.value
    return Path(snapshot_download(repo_id=model_name, local_dir=AI_MODEL_PATH / model_name.replace("/", "_")))


def _convert_model(path: Path) -> None:
    if (path / "openvino").exists():
        return

    model = SentenceTransformer(str(path), backend="openvino")
    quantization_config = OVQuantizationConfig()
    export_static_quantized_openvino_model(model, quantization_config, str(path))


def load_model(model: EmbeddingModels) -> HuggingFaceEmbeddings:
    path = _download_model(model)
    _convert_model(path)
    return HuggingFaceEmbeddings(
        model_name=str(path),
        model_kwargs={
            "backend": "openvino",
            "model_kwargs": {"file_name": "openvino/openvino_model_qint8_quantized.xml", "device": "AUTO"},
        },
    )


if __name__ == "__main__":
    load_model(EmbeddingModels.RURI_V3_30M)
