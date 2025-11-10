import json

from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from dtos.chat import ChatRequestBody
from usecases.chat import generate_chat_response
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post("/stream", summary="チャットストリーミング(SSE)")
async def chat_stream(body: ChatRequestBody) -> StreamingResponse:
    """チャットメッセージを送信し、SSEでストリーミング応答を受け取る.

    Args:
        body (ChatRequestBody): ユーザーからの質問とオプショナルなコンテキスト.

    Returns:
        StreamingResponse: text/event-stream形式のストリーミング応答.

    Events:
        - start: ストリーム開始
        - message: テキストチャンク (data: {"chunk": "...", "final": bool})
        - done: ストリーム完了
        - error: エラー発生 (data: {"detail": "..."})
    """

    async def event_generator() -> AsyncIterator[str]:
        """SSEイベントジェネレーター."""
        # 開始イベント
        yield "event: start\ndata: {}\n\n"

        try:
            # チャット応答生成
            full_response = []
            async for chunk in generate_chat_response(body.message, body.context):
                full_response.append(chunk)
                payload = {"chunk": chunk, "final": False}
                yield f"event: message\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

            # 最終チャンクを送信
            if full_response:
                final_payload = {"chunk": "", "final": True}
                yield f"event: message\ndata: {json.dumps(final_payload, ensure_ascii=False)}\n\n"

            # 完了イベント
            yield "event: done\ndata: {}\n\n"
            logger.info("Chat stream completed successfully")

        except ValueError as exc:
            # バリデーションエラー
            error_payload = {"detail": str(exc)}
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
            logger.warning("Chat validation error: %s", exc)
        except Exception:
            # 予期しないエラー
            error_payload = {"detail": "Internal server error"}
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"
            logger.exception("Unexpected error in chat stream")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/", summary="チャット送信(非ストリーミング)")
async def chat(body: ChatRequestBody) -> dict[str, str]:
    """チャットメッセージを送信し、完全な応答を受け取る.

    ストリーミングが不要な場合や、シンプルな実装用。

    Args:
        body (ChatRequestBody): ユーザーからの質問とオプショナルなコンテキスト.

    Returns:
        dict[str, str]: {"response": "生成された応答"}
    """
    try:
        # 応答を収集
        full_response = [chunk async for chunk in generate_chat_response(body.message, body.context)]
        response_text = "".join(full_response)
        logger.info("Chat response generated: %d characters", len(response_text))
    except ValueError as exc:
        logger.warning("Chat validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except Exception:
        logger.exception("Unexpected error in chat")
        raise HTTPException(status_code=500, detail="Internal server error") from None
    else:
        return {"response": response_text}
