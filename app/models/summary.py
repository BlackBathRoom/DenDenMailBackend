from models.common import BaseSQLModel
from sqlmodel import Field, SQLModel


class BaseSummary(SQLModel):
    """サマリのベースモデル.

    Attributes:
        mail_id (int): メールID.
        content (str): サマリ内容.
    """

    mail_id: int = Field(foreign_key="mail.id", index=True)
    content: str


class Summary(BaseSummary, BaseSQLModel, table=True):
    """サマリモデル.

    Attributes:
        id (int): サマリID.
        mail_id (int): メールID.
        content (str): サマリ内容.
        created_at (datetime): 作成日時.
        updated_at (datetime): 更新日時.
    """


class SummaryCreate(BaseSummary):
    """サマリ作成用モデル.

    アプリ内にサマリを新規登録する際に使用されるモデル。

    Attributes:
        mail_id (int): メールID.
        content (str): サマリ内容.
    """


class SummaryRead(BaseSummary):
    """サマリ読み取り用モデル.

    アプリ内でサマリを読み取る際に使用されるモデル。

    Attributes:
        mail_id (int): メールID.
        content (str): サマリ内容.
    """


class SummaryUpdate(SQLModel):
    """サマリ更新用モデル.

    アプリ内でサマリを更新する際に使用されるモデル。

    Attributes:
        content (str): サマリ内容.
    """

    content: str
