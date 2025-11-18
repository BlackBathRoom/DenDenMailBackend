from .langgraph_flow import summarize_text
from .langgraph_flow import summarize_text
from .langgraph_flow import summarize_text


def test_summarize_empty() -> None:
    assert summarize_text("") == ""


def test_summarize_fallback_short() -> None:
    text = "こんにちは。今日はいい天気ですね。明日も晴れるといいですね。さようなら。"
    summary = summarize_text(text)
    # フォールバックは最初の3文を返すはず
    assert "こんにちは。" in summary
    assert "今日はいい天気ですね。" in summary
    assert "明日も晴れるといいですね。" in summary


def test_summarize_preserves_newlines() -> None:
    text = "行1\n行2\n行3\n行4"
    summary = summarize_text(text)
    # フォールバックは最初の3行を返す
    assert "行1" in summary
    assert "行2" in summary
    assert "行3" in summary
    assert "行4" not in summary
