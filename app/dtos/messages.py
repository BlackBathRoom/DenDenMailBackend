from datetime import datetime

from pydantic import BaseModel


class MessageHeaderDTO(BaseModel):
    """メッセージヘッダDTO.

    Attributes:
        message_id (str): アプリ内メッセージID.
        subject (str): 件名.
        date_received (datetime): 受信日時.
        is_read (bool): 既読フラグ.
    """

    message_id: str
    subject: str
    date_received: datetime
    is_read: bool = False


class RegisterVendorRequestBody(BaseModel):
    """ベンダー登録APIの成功レスポンスDTO.

    Attributes:
        vendor (str): 登録されたベンダー名.
    """

    vendor: str


class RegisteredFolderDTO(BaseModel):
    """登録済みフォルダDTO.

    Args:
        id (int): フォルダID.
        name (str): フォルダ名.
    """

    id: int
    name: str


class RegisteredVendorDTO(BaseModel):
    """登録済みベンダーDTO.

    Args:
        id (int): ベンダーID.
        name (str): ベンダー名.
    """

    id: int
    name: str
