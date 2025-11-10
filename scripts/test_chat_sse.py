#!/usr/bin/env python3
"""チャットAPIのテストスクリプト."""

import http.client
import json
import sys


def test_chat_stream(message: str = "こんにちは", context: str | None = None) -> None:
    """SSEストリーミングチャットをテスト.

    Args:
        message (str): テストメッセージ.
        context (str | None): オプショナルなコンテキスト.
    """
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=30)

    try:
        print("🚀 Testing Chat SSE: POST /api/chat/stream\n")
        print(f"Message: {message}")
        if context:
            print(f"Context: {context}")
        print("=" * 60)

        # リクエストボディ
        body_data = {"message": message}
        if context:
            body_data["context"] = context

        body = json.dumps(body_data)
        headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}

        conn.request("POST", "/api/chat/stream", body, headers)
        resp = conn.getresponse()

        print(f"\nStatus: HTTP {resp.status} {resp.reason}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}\n")
        print("=" * 60)
        print("SSE EVENTS:")
        print("=" * 60)

        event_count = 0
        message_chunks = []

        while True:
            line = resp.readline()
            if not line:
                break
            decoded = line.decode("utf-8").rstrip()
            if decoded:
                print(decoded)
                if decoded.startswith("event:"):
                    event_count += 1
                elif decoded.startswith("data:") and "chunk" in decoded:
                    try:
                        data = json.loads(decoded[5:].strip())
                        chunk_text = data.get("chunk", "")
                        if chunk_text:
                            message_chunks.append(chunk_text)
                    except json.JSONDecodeError:
                        pass
            sys.stdout.flush()

        print("=" * 60)
        print(f"\n✅ Stream completed: {event_count} events received")
        if message_chunks:
            print(f"📝 Reconstructed response:\n{''.join(message_chunks)}")

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
    finally:
        conn.close()


def test_chat_non_stream(message: str = "こんにちは", context: str | None = None) -> None:
    """非ストリーミングチャットをテスト.

    Args:
        message (str): テストメッセージ.
        context (str | None): オプショナルなコンテキスト.
    """
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=30)

    try:
        print("\n🚀 Testing Chat Non-Stream: POST /api/chat/\n")
        print(f"Message: {message}")
        if context:
            print(f"Context: {context}")
        print("=" * 60)

        # リクエストボディ
        body_data = {"message": message}
        if context:
            body_data["context"] = context

        body = json.dumps(body_data)
        headers = {"Content-Type": "application/json"}

        conn.request("POST", "/api/chat/", body, headers)
        resp = conn.getresponse()

        print(f"\nStatus: HTTP {resp.status} {resp.reason}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}\n")

        response_data = resp.read().decode("utf-8")
        try:
            response_json = json.loads(response_data)
            print("=" * 60)
            print("RESPONSE:")
            print("=" * 60)
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("Raw response:", response_data)

        print("\n✅ Request completed successfully")

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    # SSEストリーミングテスト
    test_chat_stream("でんでんメールについて教えてください", "メール管理アプリ")

    # 非ストリーミングテスト
    test_chat_non_stream("このアプリの特徴は?")
