from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from .shared.base import BaseMailPriority


class MailDTO(BaseMailPriority):
    subject: str
    sender_email: EmailStr
    receiver_email: list[EmailStr]
    received_at: datetime
    your_role: Literal["to", "cc"]
    is_read: bool


class AttachmentDTO(BaseModel):
    filename: str
    content_type: str


class MailbodyDTO(BaseMailPriority):
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
