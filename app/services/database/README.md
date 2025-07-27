# データベース操作関数

このモジュールは、DenDenMailBackendアプリケーションのデータベース操作を簡単に行うための関数群を提供します。

## 構成

```
app/services/database/
├── __init__.py          # エクスポート設定
├── base.py             # データベース基本機能
├── mail_crud.py        # メールのCRUD操作
├── summary_crud.py     # サマリのCRUD操作
├── database_service.py # 統合サービスクラス
└── helpers.py          # 便利関数群
```

## 使用方法

### 基本的な使い方

```python
from services.database import (
    create_mail,
    get_mail,
    list_mails,
    create_summary,
    initialize_database
)
from models.mail import MailCreate
from app_conf import MailVender

# データベースの初期化（テーブル作成）
initialize_database()

# メールの作成
mail_data = MailCreate(
    message_id="unique-message-id",
    subject="テストメール",
    received_at=datetime.now(),
    sender_name="送信者名",
    sender_address="sender@example.com",
    mail_folder="INBOX",
    is_read=False,
    vender=MailVender.OUTLOOK
)
new_mail = create_mail(mail_data)

# メールの取得
mail = get_mail(new_mail.id)

# メール一覧の取得
mails = list_mails(limit=10, is_read=False)

# メールを既読にする
mark_as_read(new_mail.id)
```

### 高度な使用方法（DatabaseServiceクラス）

```python
from services.database import DatabaseService
from models.mail import MailCreate, MailUpdate

# セッションを管理しながら複数の操作を実行
with DatabaseService() as db:
    # メールを作成
    mail = db.create_mail(mail_data)
    
    # サマリを作成
    summary_data = SummaryCreate(
        message_id=mail.message_id,
        content="メールの要約内容"
    )
    summary = db.create_summary(summary_data, mail.id)
    
    # メールを更新
    update_data = MailUpdate(is_read=True, mail_folder="読了")
    updated_mail = db.update_mail(mail.id, update_data)
```

## 主要な関数

### メール関連

- `create_mail(mail_data: MailCreate) -> Mail`: メールを作成
- `get_mail(mail_id: int) -> Optional[Mail]`: IDでメールを取得
- `find_mail_by_message_id(message_id: str) -> Optional[Mail]`: メッセージIDでメールを取得
- `list_mails(skip=0, limit=100, folder=None, is_read=None) -> list[Mail]`: メール一覧を取得
- `update_mail(mail_id: int, mail_data: MailUpdate) -> Optional[Mail]`: メールを更新
- `delete_mail(mail_id: int) -> bool`: メールを削除
- `mark_as_read(mail_id: int) -> Optional[Mail]`: メールを既読にする
- `mark_as_unread(mail_id: int) -> Optional[Mail]`: メールを未読にする
- `move_to_folder(mail_id: int, folder: str) -> Optional[Mail]`: メールをフォルダに移動
- `count_mails(folder=None, is_read=None) -> int`: メール件数を取得

### サマリ関連

- `create_summary(summary_data: SummaryCreate, mail_id: int) -> Summary`: サマリを作成
- `get_summary(summary_id: int) -> Optional[Summary]`: IDでサマリを取得
- `find_summary_by_mail_id(mail_id: int) -> Optional[Summary]`: メールIDでサマリを取得
- `find_summary_by_message_id(message_id: str) -> Optional[Summary]`: メッセージIDでサマリを取得
- `list_summaries(skip=0, limit=100) -> list[Summary]`: サマリ一覧を取得
- `update_summary(summary_id: int, summary_data: SummaryUpdate) -> Optional[Summary]`: サマリを更新
- `delete_summary(summary_id: int) -> bool`: サマリを削除
- `count_summaries() -> int`: サマリ件数を取得

### 複合操作

- `create_mail_with_summary(mail_data: MailCreate, summary_content: str) -> tuple[Mail, Summary]`: メールとサマリを同時に作成
- `delete_mail_with_summary(mail_id: int) -> bool`: メールとサマリを同時に削除
- `get_mail_with_summary(mail_id: int) -> Optional[tuple[Mail, Optional[Summary]]]`: メールとサマリを同時に取得

### データベース管理

- `initialize_database() -> None`: データベースを初期化（テーブル作成）

## FastAPIでの使用例

```python
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session
from services.database import get_session, MailCRUD
from models.mail import MailCreate, MailRead, MailUpdate

app = FastAPI()

@app.post("/mails/", response_model=MailRead)
def create_mail_endpoint(mail: MailCreate, session: Session = Depends(get_session)):
    return MailCRUD.create_mail(session, mail)

@app.get("/mails/{mail_id}", response_model=MailRead)
def get_mail_endpoint(mail_id: int, session: Session = Depends(get_session)):
    mail = MailCRUD.get_mail_by_id(session, mail_id)
    if mail is None:
        raise HTTPException(status_code=404, detail="Mail not found")
    return mail

@app.get("/mails/", response_model=list[MailRead])
def list_mails_endpoint(
    skip: int = 0,
    limit: int = 100,
    folder: str = None,
    is_read: bool = None,
    session: Session = Depends(get_session)
):
    return MailCRUD.get_mails(session, skip, limit, folder, is_read)
```

## エラーハンドリング

- 関数は適切に`Optional`型を返すため、`None`チェックが必要です
- データベース操作エラーはSQLModelが適切に例外を発生させます
- トランザクションは自動的に管理されますが、必要に応じて手動でセッション管理も可能です

## 注意事項

- すべての関数は内部でセッション管理を行うため、個別にセッションを渡す必要はありません
- 複数の操作を一つのトランザクションで実行したい場合は、`DatabaseService`クラスをコンテキストマネージャーとして使用してください
- データベースの初期化は、アプリケーション起動時に一度だけ実行してください
