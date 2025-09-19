from datetime import datetime

from pydantic import BaseModel, Field


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


class AttachmentDTO(BaseModel):
    """添付ファイルDTO.

    添付のメタデータのみを返す。実体は別エンドポイントで配信する想定。

    Attributes:
        part_id (int): メッセージパートID.
        filename (str | None): ファイル名.
        mime_type (str): MIMEタイプ (例: "image").
        mime_subtype (str): MIMEサブタイプ (例: "png").
        size_bytes (int | None): バイトサイズ.
        content_id (str | None): CID (インライン参照用).
        is_inline (bool): インライン表示用かどうか.
        content_url (str): 実体取得URL.
    """

    part_id: int
    filename: str | None = None
    mime_type: str
    mime_subtype: str
    size_bytes: int | None = None
    content_id: str | None = None
    is_inline: bool = False
    content_url: str


class MessageBodyDTO(BaseModel):
    """メッセージ本文DTO.

    Attributes:
        message_id (int): メッセージID.
        text (str | None): プレーンテキスト本文.
        html (str | None): HTML本文 (cid は URL にリライト済みを想定).
        encoding (str | None): デコードに用いた推定エンコーディング.
        attachments (list[AttachmentDTO]): 添付ファイル一覧 (is_inline=False を対象).
    """

    message_id: int
    text: str | None = None
    html: str | None = None
    encoding: str | None = None
    attachments: list[AttachmentDTO] = Field(default_factory=list)


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
