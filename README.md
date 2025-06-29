# AI App Backend Template

以下は生成AIを使用し作成しています。

このプロジェクトは、FastAPIアプリケーションのテンプレートです。以下の手順に従ってセットアップしてください。

---

## 必要条件
- **Python**: バージョン 3.12
- **Windows**: 開発環境として Windows を想定しています

---

## セットアップ手順

### 0. リポジトリの作成、クローン
このテンプレートを基にリポジトリを作成してください

#### sshキーの登録
sshキーを取得していない場合は[こちら](https://zenn.dev/aoikoala/articles/388eb861249780#3.-ssh%E3%82%AD%E3%83%BC%E3%81%AE%E7%94%9F%E6%88%90)を参考に取得してください

#### リポジトリのクローン
```bash
git clone git@github.com:Your_name_or_Organization/your_repository.git
```

### 1. UV のインストール
まず、PowerShell を使用して `uv` をインストールします。以下のコマンド、または[公式](https://docs.astral.sh/uv/getting-started/installation/)を参考にインストールしてください。

```powershell
PS> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
PS> $env:Path = "C:\Users\your_name\.local\bin;$env:Path"
```

### 2. プロジェクトの依存関係をインストール
プロジェクトのルートディレクトリに移動し、以下のコマンドを実行して依存関係をインストールします。

```bash
uv sync
uv run pre-commit install
```

### 3. 開発サーバーの起動
FastAPI の開発サーバーを起動するには、`app`直下に移動し以下のコマンドを実行してください。

```bash
uv run uvicorn app.main:main --reload
```

`main.py`を実行しても開発サーバを起動できます。

```bash
uv run python main.py
```

---

## コードの品質チェック
コードの品質チェックには `ruff` と `pyright` を使用しています。

### Ruff の実行
コードの静的解析を行うには以下を実行してください。

```bash
uv run ruff check ./app
```

自動修正を行う場合は以下を実行します。

```bash
uv run ruff --fix ./app
```

### Pyright の実行
型チェックを行うには以下を実行してください。

```bash
uv run pyright app
```

---

## ディレクトリ構成（一部抜粋）

以下はこのプロジェクトのディレクトリ構成の一部です。

```
├── app/
│   ├── dtos/          # データ転送オブジェクトを管理
│   ├── models/        # データモデルを管理
│   ├── routers/       # APIルーティングを管理
│   ├── services/      # ビジネスロジックを管理
│   ├── utils/         # ユーティリティ関数やロガーを管理
│   ├── websockets/    # WebSocket関連の機能を管理
├── tests/             # テストコードを管理
├── pyproject.toml     # Pythonプロジェクトの設定ファイル
```

各ディレクトリの役割を理解して、必要に応じてカスタマイズしてください。

---

## 注意事項
- このプロジェクトはテンプレートディレクトリとして設計されています。必要に応じてカスタマイズして使用してください。
- Windows 環境を想定しています。他のプラットフォームでは動作が異なる場合があります。

---

これでセットアップは完了です！🎉 必要に応じてカスタマイズして使ってね！
