from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from .shared.base import BasePriority


class MailDTO(BasePriority):
    subject: str
    sender_email: EmailStr
    receiver_email: list[EmailStr]
    received_at: datetime
    your_role: Literal["to", "cc"]
    is_read: bool


class AttachmentDTO(BaseModel):
    filename: str
    content_type: str


class MailbodyDTO(BasePriority):
    subject: str
    sender_email: EmailStr
    receiver_email: list[EmailStr]
    your_role: Literal["to", "cc"]
    received_at: datetime
    is_read: bool
    body: str
    attachments: list[AttachmentDTO] = Field(default_factory=list)


class MailReadUpdateDTO(BaseModel):
    is_read: bool


# デモ値関数群
def demo_mail_dto_value() -> MailDTO:
    return MailDTO(
        id="demo-mail-001",
        subject="重要: プロジェクトミーティングの件",
        sender_email="manager@example.com",
        receiver_email=["user@example.com", "team@example.com"],
        received_at=datetime.now(UTC),
        your_role="to",
        priority=2,
        is_read=False,
    )


def demo_attachment_dto_value() -> AttachmentDTO:
    return AttachmentDTO(
        filename="meeting_schedule.pdf",
        content_type="application/pdf",
    )


def demo_mailbody_dto_value() -> MailbodyDTO:
    body_text = (
        "お疲れ様です。\n\n"
        "来週火曜日(8月20日)14:00より、プロジェクトの進捗確認ミーティングを開催いたします。\n\n"
        "議題:\n"
        "1. 現在の進捗状況\n"
        "2. 課題と解決策\n"
        "3. 今後のスケジュール\n\n"
        "よろしくお願いします。"
    )
    return MailbodyDTO(
        id="demo-mail-001",
        subject="重要: プロジェクトミーティングの件",
        sender_email="manager@example.com",
        receiver_email=["user@example.com", "team@example.com"],
        received_at=datetime.now(UTC),
        your_role="to",
        priority=2,
        is_read=False,
        body=body_text,
        attachments=[demo_attachment_dto_value()],
    )


def demo_mail_read_update_dto_value() -> MailReadUpdateDTO:
    """mail_dto.pyのMailReadUpdateDTOと同じ型でデモ値を返す."""
    return MailReadUpdateDTO(is_read=True)
