from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# リポの app_conf.MailVender に寄せたいが、デモなので Literal で代用
MailVender = Literal["Thunderbird", "Outlook", "Other"]


class DemoMailDTO(BaseModel):
    id: str = Field(..., description="メッセージID(ユニーク)")
    subject: str = Field(..., description="件名")
    received_at: datetime = Field(..., description="受信日時(ISO8601)")
    sender_name: str = Field(..., description="送信者名")
    sender_address: EmailStr = Field(..., description="送信者メールアドレス")
    mail_folder: str = Field(..., description="フォルダ名(例: INBOX)")
    is_read: bool = Field(default=False, description="既読フラグ")
    vender: MailVender = Field(..., description="メールクライアント種別")


def demo_mail_value() -> DemoMailDTO:
    return DemoMailDTO(
        id="demo-20250816-0001",
        subject="[Demo] FastAPI sample mail",
        received_at=datetime.now(UTC),
        sender_name="DenDen Mail Bot",
        sender_address="bot@example.com",
        mail_folder="INBOX",
        is_read=False,
        vender="Thunderbird",
    )
