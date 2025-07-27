"""データベース関連のサービス層."""

from typing import Generator

from app_conf import engine
from sqlmodel import Session, SQLModel


def create_tables() -> None:
    """全てのテーブルを作成する."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """データベースセッションを取得する.
    
    依存性注入で使用される関数。
    
    Yields:
        Session: SQLModelデータベースセッション
    """
    with Session(engine) as session:
        yield session


def get_db_session() -> Session:
    """直接データベースセッションを取得する.
    
    Returns:
        Session: SQLModelデータベースセッション
    """
    return Session(engine)
