from datetime import datetime

from sqlmodel import Field, SQLModel


class BaseSQLModel(SQLModel):
    """ベースSQLモデル.

    Attributes:
        id (int): アプリ内ID.
        created_at (datetime): 作成日時.
        updated_at (datetime): 更新日時.
    """

    id: int = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})
