# https://zenn.dev/mook_jp/books/sqlmodel-tutorial

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, create_engine, Session, select


class BaseSQLModel(SQLModel):
    """db共通フィールド"""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


class BaseMail(BaseModel):
    """メールのフィールドマッピング"""

    name: str
    email: str
    age: int | None = None


class Mail(BaseMail, BaseSQLModel, table=True):
    """メールモデル

    Attributes:
        id (int): アプリ内メールID.
        name (str): 名前.
        email (str): メールアドレス.
        age (int | None): 年齢.オプション.
        created_at (datetime): 作成日時.
        updated_at (datetime): 更新日時.
    """


class MailCreate(BaseMail):
    """メール作成用モデル"""


class MailRead(BaseMail, BaseSQLModel):
    """メール読み取り用モデル"""


class MailUpdate(BaseModel):
    """メール更新用モデル"""

    name: str | None = None
    email: str | None = None
    age: int | None = None


sqlite_file_path = Path(__file__).parent.parent / "database" / "study.sqlite3"
""
sqlite_url = f"sqlite:///{sqlite_file_path}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def create_mails():
    mails = [
        MailCreate(name="Alice", email="alice@example.com", age=30),
        MailCreate(name="Bob", email="bob@example.com"),
        MailCreate(name="Charlie", email="charlie@example.com", age=25),
    ]

    # session = Session(engine)
    # for mail in mails:
    #     session.add(Mail(**mail.model_dump()))
    # # session.add_all(mails)
    # session.commit()
    with Session(engine) as session:
        mail_obj = [Mail(**mail.model_dump()) for mail in mails]
        session.add_all(mail_obj)
        session.commit()


def select_mails():
    with Session(engine) as session:
        statement = select(Mail)
        results = session.exec(statement)
        for mail in results:
            print(MailRead.model_validate(mail))


def update_mails():
    update_data = MailUpdate(age=20)

    with Session(engine) as session:
        stmt1 = select(Mail).where(Mail.name == "Alice")
        mail = session.exec(stmt1).one()
        print(f"Before update: {mail}")

        for key, val in update_data.model_dump(exclude_unset=True).items():
            setattr(mail, key, val)

        session.commit()
        session.refresh(mail)
        print(f"After update: {mail}")


def delete_mails():
    with Session(engine) as session:
        stmt = select(Mail).where(Mail.name == "Alice")
        mail = session.exec(stmt).one()
        session.delete(mail)
        session.commit()


if __name__ == "__main__":
    # create_db_and_tables()
    # create_mails()
    # select_mails()
    update_mails()
    # delete_mails()
