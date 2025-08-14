---
applyTo: '**/*.py'
---

## フォーマットと静的解析

フォーマッタ、リンターは`Ruff`を使用する。設定は`[project_root]/.ruff.toml`に従うこと。
コードを変更、作成した場合は`uv run ruff format && uv run ruff check --fix`でフォーマットとチェックを実行し、警告やエラーを修正すること。

## 型ヒント

全ての関数・メソッドの引数と戻り値に型ヒントを付与すること。
typingモジュールのAny、castの使用は最小限に留めること。

## 命名規則

Pythonの命名規則に従うこと。

- 変数・関数: snake_case
- クラス: PascalCase
- 定数: UPPER_SNAKE_CASE

## プロジェクトディレクトリ構成:

`[project_root]/app`配下にアプリケーションのコードを配置

- dtos: データ転送オブジェクトを管理
- models: データモデルを管理
- routers: APIルーティングを管理
- services: ビジネスロジックを管理
- utils: ユーティリティ関数やロガーを管理
- websockets: WebSocket関連の機能を管理

## コメントとDocstring

全ての公開クラスと関数には、GoogleスタイルのDocstringを記述すること。
複雑なロジックには処理内容を説明するコメントを記述すること。

## エラーハンドリング

`try...except`ブロックでは具体的な例外を捕捉し、`except Exception`は避けること。
exceptionのメッセージは具体的で問題の特定に役立つ情報を含め、`logger.exception`を使用してログに記録すること。
レスポンス作成時にエラーが発生した場合は、HTTPステータスコードを適切に設定し、エラーメッセージを含むJSONレスポンスを返すこと。

## ロギング

ロギングには`utils/log_config`で定義されている`logger`を使用すること。

```python
from utils.log_config import get_logger

logger = get_logger(__name__)

# ログ出力例
logger.info("情報メッセージ")
```

DEBUG、INFO、WARNING、EXCEPTIONなどログレベルを適切に使い分け、デバッグや問題追跡に役立つ情報を出力すること。
