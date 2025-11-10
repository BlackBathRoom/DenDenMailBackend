"""チャット機能のユースケース."""

import asyncio
import os
import random

from collections.abc import AsyncIterator

from utils.logging import get_logger

logger = get_logger(__name__)

# Mock mode: if env var USE_MOCK_CHAT=1, use mock responses
USE_MOCK_CHAT = os.getenv("USE_MOCK_CHAT", "1") == "1"


async def generate_chat_response(user_message: str, context: str | None = None) -> AsyncIterator[str]:
    """チャット応答を生成(ストリーミング).

    現在はモック実装。実際のLLM統合時に置き換え可能。

    Args:
        user_message (str): ユーザーからのメッセージ.
        context (str | None): オプショナルなコンテキスト情報.

    Yields:
        str: 生成されたテキストのチャンク.
    """
    if USE_MOCK_CHAT:
        logger.info("Using mock chat response for message: %s", user_message[:50])
        async for chunk in _generate_mock_response(user_message, context):
            yield chunk
    else:
        # 実際のLLM実装はここに追加
        logger.info("Using actual LLM for chat (not yet implemented)")
        async for chunk in _generate_mock_response(user_message, context):
            yield chunk


async def _generate_mock_response(user_message: str, context: str | None = None) -> AsyncIterator[str]:
    """モックチャット応答を生成.

    Args:
        user_message (str): ユーザーからのメッセージ.
        context (str | None): コンテキスト情報.

    Yields:
        str: 生成されたテキストのチャンク.
    """
    # ユーザーメッセージに応じた応答テンプレート
    responses = [
        f"ご質問ありがとうございます。「{user_message[:30]}」について回答します。",
        "この件について詳しく説明させていただきます。",
        "まず、基本的な情報からお伝えします。",
        "具体的には、以下のような点が重要です。",
        "また、追加の情報として、関連する内容もございます。",
        "何か他にご質問があればお気軽にお聞きください。",
    ]

    # コンテキストがある場合は言及
    if context:
        responses.insert(1, f"コンテキスト: {context} に基づいて回答します。")

    # 応答をランダムに選択して結合
    num_sentences = random.randint(3, len(responses))
    selected_responses = random.sample(responses, num_sentences)
    full_response = "".join(selected_responses)

    # 文字列を小さなチャンクに分割してストリーミング
    chunk_size = random.randint(10, 20)
    for i in range(0, len(full_response), chunk_size):
        chunk = full_response[i : i + chunk_size]
        yield chunk
        # ストリーミングをシミュレートするための遅延
        await asyncio.sleep(0.05)
