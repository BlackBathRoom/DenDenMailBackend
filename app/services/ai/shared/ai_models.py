from enum import Enum


class OpenVINOModels(Enum):
    """OpenVINOで使用するモデルの列挙型."""

    QWEN3_8B = "OpenVINO/Qwen3-8B-int4-cw-ov"
