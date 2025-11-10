"""OpenVINO最適化RURI_v3埋め込みサービス."""

import sys
import time
import warnings

from pathlib import Path
from typing import Any, cast

from app.utils.logging import get_logger

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import openvino as ov
except ImportError:
    ov = None

try:
    import torch

    from optimum.intel import OVModelForFeatureExtraction
    from transformers import AutoTokenizer
except ImportError as e:
    msg = "必要なライブラリをインストールしてください: uv add openvino transformers torch optimum[openvino]"
    raise ImportError(msg) from e

logger = get_logger(__name__)

# 警告を抑制
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class OpenVINORURIv3EmbeddingService:
    """OpenVINO最適化されたRURI_v3埋め込みサービス."""

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        device: str = "CPU",
        cache_dir: Path | None = None,
        ov_config: dict[str, Any] | None = None,
    ) -> None:
        """初期化.

        Args:
            model_name: 使用する多言語埋め込みモデル名
            device: OpenVINOデバイス (CPU, GPU, AUTO)
            cache_dir: モデルキャッシュディレクトリ
            ov_config: OpenVINO設定
        """
        try:
            self.model_name = model_name
            self.device = device.upper()
            self.cache_dir = cache_dir or Path("./ov_model_cache")
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # OpenVINO設定のデフォルト値 - CPUプラグイン互換設定
            self.ov_config = ov_config or {
                "PERFORMANCE_HINT": "LATENCY",
                "NUM_STREAMS": "1",
                # AFFINITYはCPUプラグインでサポートされていないため削除
            }

            # モデルとトークナイザーの初期化
            self._initialize_model()

            # モデル情報を取得
            self.embedding_dimension = self._get_embedding_dimension()
            self.max_seq_length = getattr(self.tokenizer, "model_max_length", 512)

            logger.info(
                "OpenVINO RURI_v3埋め込みサービス初期化完了: model=%s, device=%s, dim=%d",
                model_name,
                self.device,
                self.embedding_dimension,
            )

        except Exception as e:
            logger.exception("OpenVINO RURI_v3埋め込みサービス初期化エラー")
            msg = f"OpenVINO RURI_v3サービスの初期化に失敗: {e}"
            raise ValueError(msg) from e

    def _initialize_model(self) -> None:
        """モデルとトークナイザーを初期化."""
        try:
            # トークナイザーの初期化
            logger.info("トークナイザーを初期化中...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, cache_dir=str(self.cache_dir), trust_remote_code=True
            )

            # OpenVINOモデルファイルのパス
            ov_model_path = self.cache_dir / f"{self.model_name.replace('/', '_')}_openvino"

            if ov_model_path.exists() and (ov_model_path / "openvino_model.xml").exists():
                # 既存のOpenVINOモデルをロード
                logger.info("既存のOpenVINOモデルをロード中...")
                self.model = OVModelForFeatureExtraction.from_pretrained(
                    str(ov_model_path), device=self.device, ov_config=self.ov_config
                )
            else:
                # Hugging Faceモデルを変換してロード
                logger.info("Hugging FaceモデルをOpenVINOに変換中...")
                self.model = OVModelForFeatureExtraction.from_pretrained(
                    self.model_name,
                    export=True,
                    device=self.device,
                    ov_config=self.ov_config,
                    cache_dir=str(self.cache_dir),
                )

                # 変換したモデルを保存
                logger.info("変換したOpenVINOモデルを保存中...")
                self.model.save_pretrained(str(ov_model_path))

            logger.info("OpenVINOモデル初期化完了")

        except Exception as e:
            logger.exception("OpenVINOモデル初期化エラー")
            msg = f"モデル初期化に失敗しました: {e}"
            raise ValueError(msg) from e

    def _get_embedding_dimension(self) -> int:
        """埋め込み次元数を取得."""
        try:
            # ダミー入力でテスト
            test_input = self.tokenizer("test", return_tensors="pt", padding=True, truncation=True, max_length=8)

            with torch.no_grad():
                outputs = self.model(**test_input)
                embeddings = self._mean_pooling(outputs, test_input["attention_mask"])
                return embeddings.shape[1]

        except (AttributeError, KeyError, RuntimeError) as e:
            logger.warning("埋め込み次元数の自動取得に失敗、デフォルト値を使用: %s", e)
            return 768  # multilingual-e5-baseのデフォルト次元数

    def _mean_pooling(
        self,
        model_output: dict[str, torch.Tensor] | tuple | list | torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Mean pooling処理."""
        try:
            # Retrieve token embeddings from model output
            token_embeddings: torch.Tensor
            if hasattr(model_output, "last_hidden_state"):
                token_embeddings = model_output.last_hidden_state  # type: ignore[attr-defined]
            elif isinstance(model_output, dict) and "last_hidden_state" in model_output:
                token_embeddings = model_output["last_hidden_state"]
            elif isinstance(model_output, (tuple, list)) and len(model_output) > 0:
                token_embeddings = cast("torch.Tensor", model_output[0])
            else:
                token_embeddings = cast("torch.Tensor", model_output)

            # Expand attention mask to match token embeddings dimensions
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()

            # Apply mask and sum
            masked_embeddings = token_embeddings * input_mask_expanded
            summed = torch.sum(masked_embeddings, 1)

            # Calculate mean (avoiding division by zero)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)

            return summed / sum_mask

        except (AttributeError, TypeError, RuntimeError) as e:
            logger.exception("Mean pooling処理エラー")
            msg = f"Mean pooling処理に失敗しました: {e}"
            raise ValueError(msg) from e

    def _preprocess_text(self, text: str) -> str:
        """テキストの前処理."""
        if not text:
            return ""

        # 基本的な前処理
        processed = text.strip()
        processed = " ".join(processed.split())

        # 最大長制限
        if len(processed) > self.max_seq_length * 4:
            processed = processed[: self.max_seq_length * 4]
            logger.debug("テキスト長を制限: %d文字", len(processed))

        return processed

    def embed_document(self, document: str) -> list[float]:
        """単一ドキュメントをベクトル化.

        Args:
            document: ベクトル化するドキュメント文字列

        Returns:
            ドキュメントベクトル

        Raises:
            ValueError: ベクトル化に失敗した場合
        """
        try:
            if not document or not document.strip():
                logger.warning("空のドキュメントが渡されました")
                return [0.0] * self.embedding_dimension

            # テキスト前処理
            processed_doc = self._preprocess_text(document)

            # トークン化
            inputs = self.tokenizer(
                processed_doc,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_seq_length,
            )

            # OpenVINO推論実行
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = self._mean_pooling(outputs, inputs["attention_mask"])

                # 正規化
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

                # numpy配列をリストに変換
                embedding_list = embeddings.squeeze().cpu().numpy().tolist()

            logger.debug("ドキュメントベクトル化完了: length=%d, dim=%d", len(document), len(embedding_list))

        except Exception as e:
            logger.exception("ドキュメントベクトル化エラー")
            msg = f"ドキュメントのベクトル化に失敗: {e}"
            raise ValueError(msg) from e
        else:
            return embedding_list

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """複数ドキュメントの一括ベクトル化.

        Args:
            documents: ベクトル化するドキュメントのリスト

        Returns:
            ドキュメントベクトルのリスト

        Raises:
            ValueError: ベクトル化に失敗した場合
        """
        try:
            if not documents:
                logger.warning("空のドキュメントリストが渡されました")
                return []

            # テキスト前処理
            processed_docs = [self._preprocess_text(doc) for doc in documents]

            # 空ドキュメントのインデックスを記録
            valid_docs = []
            empty_indices = []

            for i, doc in enumerate(processed_docs):
                if doc and doc.strip():
                    valid_docs.append(doc)
                else:
                    empty_indices.append(i)

            if not valid_docs:
                logger.warning("すべてのドキュメントが空でした")
                return [[0.0] * self.embedding_dimension] * len(documents)

            # バッチ処理用にトークン化
            inputs = self.tokenizer(
                valid_docs,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_seq_length,
            )

            # OpenVINO推論実行
            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = self._mean_pooling(outputs, inputs["attention_mask"])

                # 正規化
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

                # numpy配列に変換
                embeddings_array = embeddings.cpu().numpy()

            # 結果リストを構築
            embeddings_list = embeddings_array.tolist()
            final_embeddings = []
            valid_idx = 0

            for i in range(len(documents)):
                if i in empty_indices:
                    final_embeddings.append([0.0] * self.embedding_dimension)
                else:
                    final_embeddings.append(embeddings_list[valid_idx])
                    valid_idx += 1

            logger.debug("複数ドキュメントベクトル化完了: total=%d, valid=%d", len(documents), len(valid_docs))

        except Exception as e:
            logger.exception("複数ドキュメントベクトル化エラー")
            msg = f"複数ドキュメントのベクトル化に失敗: {e}"
            raise ValueError(msg) from e
        else:
            return final_embeddings

    def get_model_info(self) -> dict[str, Any]:
        """モデル情報を取得.

        Returns:
            モデル情報の辞書
        """
        try:
            return {
                "model_name": self.model_name,
                "device": self.device,
                "embedding_dimension": self.embedding_dimension,
                "max_seq_length": self.max_seq_length,
                "model_type": "RURI_v3",
                "backend": "OpenVINO",
                "cache_dir": str(self.cache_dir),
                "ov_config": self.ov_config,
                "normalization": True,
                "supports_batch": True,
            }

        except Exception as e:
            logger.exception("モデル情報取得エラー")
            msg = f"モデル情報の取得に失敗: {e}"
            raise ValueError(msg) from e

    def benchmark_performance(
        self, sample_documents: list[str], batch_sizes: list[int] | None = None
    ) -> dict[str, Any]:
        """埋め込み性能をベンチマーク.

        Args:
            sample_documents: ベンチマーク用ドキュメントのリスト
            batch_sizes: テストするバッチサイズのリスト

        Returns:
            性能測定結果
        """
        try:
            if not sample_documents:
                return {"error": "ベンチマーク用ドキュメントが空です"}

            if batch_sizes is None:
                batch_sizes = [1, 4, 8, 16, 32]

            results = {
                "model_info": self.get_model_info(),
                "test_document_count": len(sample_documents),
                "batch_performance": {},
            }

            # 単一ドキュメント処理のベンチマーク
            start_time = time.time()
            for doc in sample_documents[:5]:  # 最大5件でテスト
                self.embed_document(doc)
            single_time = time.time() - start_time

            results["single_processing"] = {
                "total_time": single_time,
                "throughput": (min(5, len(sample_documents)) / single_time if single_time > 0 else 0),
            }

            # バッチサイズ別ベンチマーク
            for batch_size in batch_sizes:
                if batch_size > len(sample_documents):
                    continue

                test_docs = sample_documents[:batch_size]

                start_time = time.time()
                self.embed_documents(test_docs)
                batch_time = time.time() - start_time

                results["batch_performance"][batch_size] = {
                    "total_time": batch_time,
                    "throughput": len(test_docs) / batch_time if batch_time > 0 else 0,
                    "avg_time_per_doc": batch_time / len(test_docs) if test_docs else 0,
                }

            logger.info("OpenVINO RURI_v3性能ベンチマーク完了")

        except Exception as e:
            logger.exception("性能ベンチマークエラー")
            msg = f"性能ベンチマークに失敗: {e}"
            raise ValueError(msg) from e
        else:
            return results

    def cleanup(self) -> None:
        """リソースをクリーンアップ."""
        try:
            if hasattr(self, "model") and self.model:
                # OpenVINOリソースの解放
                del self.model

            if hasattr(self, "tokenizer") and self.tokenizer:
                del self.tokenizer

            logger.info("OpenVINO RURI_v3リソースをクリーンアップ完了")

        except (AttributeError, RuntimeError) as e:
            logger.warning("リソースクリーンアップ中にエラー: %s", e)

    def __del__(self) -> None:
        """デストラクタでリソースクリーンアップ."""
        self.cleanup()


def create_openvino_embedding_service(
    model_name: str = "intfloat/multilingual-e5-base",
    device: str = "CPU",
    cache_dir: Path | None = None,
    ov_config: dict[str, Any] | None = None,
) -> OpenVINORURIv3EmbeddingService:
    """OpenVINO埋め込みサービスインスタンスを作成.

    Args:
        model_name: 使用する多言語埋め込みモデル名
        device: OpenVINOデバイス
        cache_dir: モデルキャッシュディレクトリ
        ov_config: OpenVINO設定

    Returns:
        OpenVINORURIv3EmbeddingServiceインスタンス

    Raises:
        ValueError: サービス作成に失敗した場合
    """
    try:
        logger.info("OpenVINO埋め込みサービス作成開始")

        # デバイス設定の最適化
        if device.upper() == "AUTO":
            try:
                if ov is not None:
                    core = ov.Core()
                    available_devices = core.available_devices
                    device = "GPU" if "GPU" in available_devices else "CPU"
                    logger.info("自動デバイス選択: %s", device)
                else:
                    device = "CPU"
                    logger.info("OpenVINO未利用のため、CPUを使用")
            except (ImportError, RuntimeError):
                device = "CPU"
                logger.info("デバイス自動選択失敗、CPUを使用")

        service = OpenVINORURIv3EmbeddingService(
            model_name=model_name, device=device, cache_dir=cache_dir, ov_config=ov_config
        )

        logger.info("OpenVINO埋め込みサービス作成完了")

    except Exception as e:
        logger.exception("OpenVINO埋め込みサービス作成エラー")
        msg = f"サービスの作成に失敗しました: {e}"
        raise ValueError(msg) from e
    else:
        return service


def main() -> None:
    """デモとテスト実行."""
    service = None
    try:
        logger.info("OpenVINO RURI_v3埋め込みサービスデモ開始")

        # サービス初期化
        service = create_openvino_embedding_service()

        # モデル情報表示
        model_info = service.get_model_info()
        logger.info("モデル情報:")
        for key, value in model_info.items():
            logger.info("  %s: %s", key, value)

        # テスト用ドキュメント
        test_documents = [
            """
            件名: システム更新のお知らせ
            送信者: admin@company.com

            本日、システムの定期更新を実施いたします。
            更新内容:
            - セキュリティパッチの適用
            - 新機能の追加
            - 性能改善

            作業時間: 23:00-02:00
            """,
            """
            件名: プロジェクト進捗会議
            送信者: manager@company.com

            来週のプロジェクト進捗会議についてご連絡します。

            日時: 2024年1月20日 14:00-16:00
            場所: 会議室A
            議題:
            - 第1四半期の進捗確認
            - 課題と対応策の検討
            - 次四半期の計画
            """,
        ]

        # 単一ドキュメントベクトル化テスト
        logger.info("\n=== 単一ドキュメントベクトル化テスト ===")
        doc_vector = service.embed_document(test_documents[0])
        logger.info("ベクトル次元: %d", len(doc_vector))
        logger.info(
            "ベクトル値サンプル: [%.4f, %.4f, %.4f, ...]",
            doc_vector[0],
            doc_vector[1],
            doc_vector[2],
        )

        # 複数ドキュメント一括ベクトル化テスト
        logger.info("\n=== 複数ドキュメント一括ベクトル化テスト ===")
        batch_vectors = service.embed_documents(test_documents)
        logger.info("処理したドキュメント数: %d", len(batch_vectors))

        # 性能ベンチマーク
        logger.info("\n=== 性能ベンチマーク ===")
        benchmark_result = service.benchmark_performance(test_documents)

        logger.info("単一処理性能:")
        single_perf = benchmark_result["single_processing"]
        logger.info("  処理時間: %.4f秒", single_perf["total_time"])
        logger.info("  スループット: %.2f docs/sec", single_perf["throughput"])

        logger.info("バッチ処理性能:")
        for batch_size, perf in benchmark_result["batch_performance"].items():
            logger.info("  バッチサイズ %d: %.2f docs/sec", batch_size, perf["throughput"])

        logger.info("OpenVINO RURI_v3埋め込みサービスデモ完了!")

    except Exception:
        logger.exception("デモ実行エラー")
        raise
    finally:
        # リソースクリーンアップ
        if service is not None:
            service.cleanup()


if __name__ == "__main__":
    main()
