"""埋め込みサービスパッケージ."""

from .openvino_ruri_v3_embedding import (
    OpenVINORURIv3EmbeddingService,
    create_openvino_embedding_service,
)

__all__ = [
    "OpenVINORURIv3EmbeddingService",
    "create_openvino_embedding_service",
]
