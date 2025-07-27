# Windows環境での実行ガイド

## 前提条件

- Python 3.12以上
- uv（推奨）またはpip

## インストール手順

### 1. uvを使用する場合（推奨）

```cmd
# uvのインストール（未インストールの場合）
pip install uv

# プロジェクトディレクトリに移動
cd DenDenMailBackend

# 依存関係のインストール
uv sync

# テスト実行
uv run python test_windows.py
```

### 2. pipを使用する場合

```cmd
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
venv\Scripts\activate

# 依存関係のインストール
pip install fastapi pydantic sqlmodel uvicorn

# テスト実行
python test_windows.py
```

### 3. バッチファイルを使用する場合

```cmd
# バッチファイルを実行
run_test_windows.bat
```

## Windows環境での動作確認

データベース操作関数は以下の点でWindows環境に最適化されています：

### ✅ 対応済み項目

1. **パス処理**: `pathlib.Path`使用でWindows/Linux両対応
2. **SQLite設定**: Windows環境での接続最適化
3. **文字エンコーディング**: UTF-8対応
4. **ファイルロック**: SQLiteの適切な設定

### 🔧 Windows固有の設定

```python
# app_conf.pyでのWindows最適化
connect_args = {"check_same_thread": False}
if os.name == "nt":  # Windows
    connect_args.update({
        "timeout": 20,
        "isolation_level": None,
    })
```

## 使用例（Windows環境）

```python
# データベース操作
from services.database import (
    create_mail, 
    get_mail, 
    initialize_database
)

# データベース初期化
initialize_database()

# メール作成
mail = create_mail(mail_data)
print(f"作成されたメールID: {mail.id}")
```

## トラブルシューティング

### SQLiteエラーが発生する場合

1. **ファイルパーミッション**: データベースファイルの書き込み権限を確認
2. **ディスク容量**: 十分な空き容量があることを確認
3. **ウイルス対策ソフト**: SQLiteファイルが除外されていることを確認

### パスエラーが発生する場合

```python
# 絶対パスでの確認
from app.app_conf import DB_PATH
print(f"データベースパス: {DB_PATH.absolute()}")
```

### 依存関係エラーが発生する場合

```cmd
# パッケージの再インストール
uv sync --force
# または
pip install --force-reinstall -r requirements.txt
```

## パフォーマンス

Windows環境でのSQLite性能：
- 小規模データ（〜10万件）: 高速動作
- 中規模データ（〜100万件）: 良好
- 大規模データ（100万件〜）: インデックス最適化推奨

## セキュリティ

Windows環境での推奨設定：
- データベースファイルの適切な権限設定
- バックアップの定期実行
- ログファイルのローテーション
