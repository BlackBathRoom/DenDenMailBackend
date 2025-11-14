# デモファイル

ベクトル化機能のテスト用デモEMLファイルを生成・管理するディレクトリです。

## ファイル構成

```
demo/
├── generator.py           # EMLファイル生成スクリプト
├── eml_files/            # 生成されたEMLファイル
│   ├── .gitkeep          # ディレクトリ保持用ファイル
│   ├── meeting_email.eml # 会議関連メール
│   ├── system_maintenance.eml # システムメンテナンスメール
│   └── feature_release.eml # 新機能リリースメール
└── README.md             # このファイル
```

## 使用方法

### EMLファイルの生成

```bash
# プロジェクトルートから実行
cd c:\Users\toran\DenDenMailBackend
python demo\generator.py
```

実行結果：
```
INFO:- デモEMLファイル生成開始!
INFO:- デモEMLファイルを 3 件生成: C:\Users\toran\DenDenMailBackend\demo\eml_files
INFO:- 生成完了:
INFO:-   - meeting_email: ...\meeting_email.eml (1017 bytes)
INFO:-   - system_maintenance: ...\system_maintenance.eml (1596 bytes)
INFO:-   - feature_release: ...\feature_release.eml (1984 bytes)
```

### EMLファイルの読み込みテスト

生成されたEMLファイルは、標準のemailモジュールで解析できます：

```python
import email
from pathlib import Path

# EMLファイル読み込み
eml_file = Path("demo/eml_files/meeting_email.eml")
with open(eml_file, 'r', encoding='utf-8') as f:
    message = email.message_from_string(f.read())

print(f"件名: {message['Subject']}")
print(f"送信者: {message['From']}")
print(f"受信者: {message['To']}")
print(f"日付: {message['Date']}")
print(f"Message-ID: {message['Message-ID']}")

# 本文取得
if message.is_multipart():
    for part in message.walk():
        if part.get_content_type() == "text/plain":
            print(f"本文: {part.get_payload(decode=True).decode('utf-8')}")
else:
    print(f"本文: {message.get_payload(decode=True).decode('utf-8')}")
```

### con_thunderbird.pyとの連携テスト

生成されたEMLファイルは、既存のcon_thunderbird.pyの機能と互換性があります：

```python
import sys
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent.parent))

from study.con_thunderbird import parse_single_eml

# EMLファイルを解析
eml_path = Path("demo/eml_files/meeting_email.eml")
parsed_mail = parse_single_eml(eml_path)

print(f"解析結果: {parsed_mail}")
```

## デモメール内容

### 1. meeting_email.eml
- **件名**: プロジェクト会議の件について
- **送信者**: manager@example.com
- **受信者**: team@example.com
- **内容**: プロジェクト会議の案内（議題、日時、場所）
- **サイズ**: 約1,017 bytes

**用途**: 会議・プロジェクト関連の検索テスト
- "会議" → meeting_email.eml がヒット
- "プロジェクト" → meeting_email.eml がヒット
- "議題" → meeting_email.eml がヒット

### 2. system_maintenance.eml
- **件名**: 重要:システムメンテナンスのお知らせ
- **送信者**: admin@example.com
- **受信者**: all@example.com
- **内容**: システムメンテナンスの詳細案内
- **サイズ**: 約1,596 bytes

**用途**: システム・メンテナンス関連の検索テスト
- "メンテナンス" → system_maintenance.eml がヒット
- "バックアップ" → system_maintenance.eml がヒット
- "システム" → system_maintenance.eml がヒット

### 3. feature_release.eml
- **件名**: 新機能リリースのお知らせ - メール管理がさらに便利に
- **送信者**: product@example.com
- **受信者**: users@example.com
- **内容**: 新機能の詳細説明（AI分類、優先度スコアリング、類似検索）
- **サイズ**: 約1,984 bytes

**用途**: 機能・リリース関連の検索テスト
- "新機能" → feature_release.eml がヒット
- "AI" → feature_release.eml がヒット
- "検索" → feature_release.eml がヒット
- "優先度" → feature_release.eml がヒット

## ベクトル化テストでの検索例

生成されたメールで以下のような検索クエリをテストできます：

### 基本的な検索テスト
```python
# LangChain + Chromaでのベクトル検索例
search_queries = [
    "会議の件について",           # → meeting_email.eml
    "システムメンテナンス",        # → system_maintenance.eml  
    "新機能のリリース",           # → feature_release.eml
    "プロジェクトの進捗",         # → meeting_email.eml
    "データベースの最適化",       # → system_maintenance.eml
    "AI による自動分類",          # → feature_release.eml
]

for query in search_queries:
    results = vectorstore.similarity_search(query, k=3)
    print(f"クエリ: {query}")
    for result in results:
        print(f"  → {result.metadata.get('message_id', 'unknown')}")
```

### 複合的な検索テスト
```python
# 複数のメールにヒットする可能性のあるクエリ
complex_queries = [
    "システム",                   # → system_maintenance.eml, feature_release.eml
    "設定",                      # → feature_release.eml
    "利用者への案内",             # → system_maintenance.eml, feature_release.eml
]
```

## 特徴

- **プレーンテキスト形式**: 全てのメールがtext/plainでシンプル
- **日本語コンテンツ**: 日本語でのベクトル化テストに最適
- **実用的な内容**: 実際のビジネスメールに近い内容
- **標準EML形式**: RFC 2822準拠のヘッダー構造
- **Base64エンコード**: 日本語文字の正確な保存・復元
- **異なるトピック**: 会議、システム、機能の3つの明確に区別できるトピック

## 次のステップ

1. **ベクトル化機能の実装**: LangChain v0.3 + Chromaのベクトル化機能を実装
2. **検索精度の検証**: 各デモメールが適切な検索クエリでヒットするか確認
3. **パフォーマンステスト**: 大量のメールデータでの検索性能を評価