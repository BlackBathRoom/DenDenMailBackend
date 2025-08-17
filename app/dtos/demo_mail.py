from __future__ import annotations

from datetime import UTC, datetime

from .mail_dto import AttachmentDTO, MailbodyDTO, MailDTO, MailReadUpdateDTO


def demo_mail_dto_value() -> MailDTO:
    """mail_dto.pyのMailDTOと同じ型でデモ値を返す."""
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
    """mail_dto.pyのAttachmentDTOと同じ型でデモ値を返す."""
    return AttachmentDTO(
        filename="meeting_schedule.pdf",
        content_type="application/pdf",
    )


def demo_mailbody_dto_value() -> MailbodyDTO:
    """mail_dto.pyのMailbodyDTOと同じ型でデモ値を返す."""
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
