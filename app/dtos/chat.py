"""チャットAPIのDTO定義."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequestBody(BaseModel):
    """チャットリクエストボディ.

    Attributes:
        message (str): ユーザーからの質問メッセージ.
        context (str | None): オプショナルなコンテキスト情報(メールIDなど).
    """

    message: str = Field(..., description="ユーザーからの質問メッセージ", min_length=1)
    context: str | None = Field(None, description="オプショナルなコンテキスト情報")


class ChatMessageDTO(BaseModel):
    """チャットメッセージDTO.

    Attributes:
        role (Literal["user", "assistant"]): メッセージの送信者.
        content (str): メッセージ内容.
    """

    role: Literal["user", "assistant"]
    content: str


class ChatStreamChunkDTO(BaseModel):
    """SSEストリームのチャンクDTO.

    Attributes:
        chunk (str): 生成されたテキストのチャンク.
        final (bool): 最後のチャンクかどうか.
    """

    chunk: str
    final: bool = False
