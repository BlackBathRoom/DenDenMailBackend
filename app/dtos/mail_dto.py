from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr

PriorityLevel = Literal[1, 2, 3]


class MailDTO(BaseModel):
    id: str
    subject: str
    sender_email: EmailStr
    receiver_email: list[EmailStr]
    received_at: datetime
    your_role: Literal["to", "cc"]
    priority: PriorityLevel
    is_read: bool


class AttachmentDTO(BaseModel):
    filename: str
    content_type: str


class MailbodyDTO(BaseModel):
    id: str
    subject: str
    sender_email: EmailStr
    receiver_email: list[EmailStr]
    your_role: Literal["to", "cc"]
    received_at: datetime
    priority: Literal[1, 2, 3]
    is_read: bool
    body: str
    attachments: list[AttachmentDTO] = []


class MailReadUpdateDTO(BaseModel):
    is_read: bool
