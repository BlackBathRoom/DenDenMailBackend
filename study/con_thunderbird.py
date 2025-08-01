import os
import mailbox
import email
import email.header
import email.utils
import email.message
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import platform


def find_thunderbird_profile() -> Path | None:
    """Thunderbirdのプロファイルディレクトリを検索する.

    Returns:
        Path | None: プロファイルディレクトリのパス、見つからない場合はNone
    """
    system = platform.system()

    if system == "Windows":
        # Windows の場合 - 複数のパターンを試す
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")

        # 候補パスリスト
        thunderbird_candidates = [
            # 通常のインストール
            Path(appdata) / "Thunderbird" / "Profiles",
            # ポータブル版やその他
            Path(appdata) / "Mozilla" / "Thunderbird" / "Profiles",
        ]

        # Microsoft Store版を動的に検索
        packages_dir = Path(localappdata) / "Packages"
        if packages_dir.exists():
            for package_dir in packages_dir.iterdir():
                if package_dir.is_dir() and "thunderbird" in package_dir.name.lower():
                    profiles_path = package_dir / "LocalCache" / "Roaming" / "Thunderbird" / "Profiles"
                    if profiles_path.exists():
                        thunderbird_candidates.append(profiles_path)
                        print(f"🔍 Microsoft Store版発見: {package_dir.name}")

        thunderbird_dir = None
        for candidate in thunderbird_candidates:
            print(f"🔍 候補パス確認中: {candidate}")
            if candidate.exists():
                thunderbird_dir = candidate
                print(f"✅ Thunderbirdディレクトリ発見: {thunderbird_dir}")
                break

        if not thunderbird_dir:
            print("❌ Thunderbirdディレクトリが見つからないよ〜")
            return None

    elif system == "Darwin":  # macOS
        home = Path.home()
        thunderbird_dir = home / "Library" / "Thunderbird" / "Profiles"
    else:  # Linux
        home = Path.home()
        thunderbird_dir = home / ".thunderbird"

    print(f"🔍 Thunderbirdディレクトリ検索中: {thunderbird_dir}")

    if not thunderbird_dir.exists():
        print(f"❌ Thunderbirdディレクトリが見つからないよ〜: {thunderbird_dir}")
        return None

    # 見つかったプロファイル一覧を表示
    print("📁 見つかったディレクトリ一覧:")
    potential_profiles = []
    for item in thunderbird_dir.iterdir():
        if item.is_dir():
            # プロファイルの中身をチェック
            mail_dirs = [item / "ImapMail", item / "Mail"]
            has_mail_data = any(
                mail_dir.exists() and any(mail_dir.iterdir()) for mail_dir in mail_dirs if mail_dir.exists()
            )

            print(f"  - {item.name} {'(メールデータあり)' if has_mail_data else '(メールデータなし)'}")
            if has_mail_data:
                potential_profiles.append(item)

    # メールデータがあるプロファイルを優先
    if potential_profiles:
        print(f"\n✅ メールデータありのプロファイルを使用: {potential_profiles[0]}")
        return potential_profiles[0]

    # プロファイルフォルダを検索（従来の方法）
    for profile_dir in thunderbird_dir.iterdir():
        if profile_dir.is_dir():
            profile_name = profile_dir.name.lower()
            # より柔軟な検索条件にする
            is_profile = (
                "default" in profile_name
                or profile_name.endswith("-usr")
                or profile_name.endswith("-esr")
                or profile_name.endswith("-release")
                or len(profile_dir.name) > 8  # 長いランダム文字列のプロファイル
            )
            if is_profile:
                print(f"✅ プロファイル発見: {profile_dir}")
                return profile_dir

    print(f"❌ プロファイルが見つからないよ〜")
    return None


def find_inbox_file(profile_dir: Path) -> Path | None:
    """受信トレイファイルを検索する.

    Args:
        profile_dir: Thunderbirdプロファイルディレクトリ

    Returns:
        Path | None: 受信トレイファイルのパス、見つからない場合はNone
    """
    # 通常は ImapMail/アカウント名/INBOX または Mail/Local Folders/Inbox
    mail_dirs = [
        profile_dir / "ImapMail",
        profile_dir / "Mail",
    ]

    for mail_dir in mail_dirs:
        if not mail_dir.exists():
            print(f"❌ メールディレクトリが存在しない: {mail_dir}")
            continue

        print(f"🔍 メールディレクトリ検索中: {mail_dir}")

        # アカウントフォルダの一覧表示
        print(f"📁 {mail_dir.name} 内のアカウント一覧:")
        account_dirs = []
        for item in mail_dir.iterdir():
            if item.is_dir():
                print(f"  - {item.name}")
                account_dirs.append(item)

        # アカウントフォルダを検索
        for account_dir in account_dirs:
            print(f"🔍 アカウントディレクトリ検索中: {account_dir}")

            # そのディレクトリの中身を表示
            print(f"📁 {account_dir.name} 内のファイル:")
            for item in account_dir.iterdir():
                print(f"  - {item.name} {'(ファイル)' if item.is_file() else '(ディレクトリ)'}")

            # INBOX ファイルを検索
            inbox_candidates = [
                account_dir / "INBOX",
                account_dir / "Inbox",
                account_dir / "inbox",
            ]

            for inbox_file in inbox_candidates:
                if inbox_file.exists() and inbox_file.is_file():
                    # ファイルサイズもチェック
                    file_size = inbox_file.stat().st_size
                    print(f"✅ 受信トレイ発見: {inbox_file} (サイズ: {file_size} bytes)")
                    if file_size > 0:  # 空でないファイルを優先
                        return inbox_file

    print("❌ 受信トレイファイルが見つからないよ〜")
    return None


def parse_mail_data(message: email.message.Message, truncate: bool = False) -> Dict[str, Any]:
    """メールメッセージをパースしてデータ構造に変換する.

    Args:
        message: emailメッセージオブジェクト
        truncate: 本文を切り詰めるかどうか

    Returns:
        Dict[str, Any]: パースされたメールデータ
    """
    # 件名取得
    subject = message.get("Subject", "件名なし")
    if subject:
        # デコード処理
        try:
            decoded_header = email.header.decode_header(subject)
            subject = ""
            for part, encoding in decoded_header:
                if isinstance(part, bytes):
                    subject += part.decode(encoding or "utf-8", errors="ignore")
                else:
                    subject += part
        except Exception:
            subject = str(subject)

    # 送信者取得
    sender = message.get("From", "送信者不明")

    # 受信日時取得
    date_str = message.get("Date", "")
    received_time = None
    if date_str:
        try:
            # RFC 2822 形式の日付をパース
            received_time = email.utils.parsedate_to_datetime(date_str)
            # タイムゾーン情報がない場合はUTCとして扱う
            if received_time.tzinfo is None:
                received_time = received_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
        except Exception:
            # パースできない場合は現在時刻をタイムゾーン情報付きで設定
            received_time = datetime.now().astimezone()

    # メッセージID取得
    message_id = message.get("Message-ID", "")

    # メール形式とコンテンツタイプを解析
    content_type = message.get_content_type()
    is_multipart = message.is_multipart()

    # 利用可能な形式を収集
    available_formats = []
    text_body = ""
    html_body = ""

    if is_multipart:
        available_formats.append("マルチパート")
        for part in message.walk():
            part_content_type = part.get_content_type()
            available_formats.append(part_content_type)

            # テキスト部分を取得
            if part_content_type == "text/plain" and not text_body:
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        text_body = payload.decode("utf-8", errors="ignore")
                    else:
                        text_body = str(payload)
                except Exception:
                    continue

            # HTML部分を取得
            elif part_content_type == "text/html" and not html_body:
                try:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        html_body = payload.decode("utf-8", errors="ignore")
                    else:
                        html_body = str(payload)
                except Exception:
                    continue
    else:
        available_formats.append(content_type)
        try:
            payload = message.get_payload(decode=True)
            if isinstance(payload, bytes):
                body_text = payload.decode("utf-8", errors="ignore")
            else:
                body_text = str(payload)

            if content_type == "text/html":
                html_body = body_text
            else:
                text_body = body_text
        except Exception:
            text_body = "本文取得失敗"

    # 表示用の本文を決定（テキスト優先、なければHTML）
    display_body = text_body if text_body else html_body
    if not display_body:
        display_body = "本文なし"

    # 切り詰め処理を条件分岐
    if truncate:
        # 一覧表示用（短縮版）
        return {
            "subject": subject,
            "sender": sender,
            "received_time": received_time,
            "message_id": message_id,
            "content_type": content_type,
            "is_multipart": is_multipart,
            "available_formats": list(set(available_formats)),
            "text_body": text_body[:200] + "..." if len(text_body) > 200 else text_body,
            "html_body": html_body[:200] + "..." if len(html_body) > 200 else html_body,
            "body": display_body[:200] + "..." if len(display_body) > 200 else display_body,
        }
    else:
        # 詳細表示用（完全版）
        return {
            "subject": subject,
            "sender": sender,
            "received_time": received_time,
            "message_id": message_id,
            "content_type": content_type,
            "is_multipart": is_multipart,
            "available_formats": list(set(available_formats)),
            "text_body": text_body,  # 全文！
            "html_body": html_body,  # 全文！
            "body": display_body,  # 全文！
        }


def get_latest_mails(inbox_file: Path, count: int = 10, full_content: bool = True) -> List[Dict[str, Any]]:
    """受信トレイから最新のメールを取得する.

    Args:
        inbox_file: 受信トレイファイルのパス
        count: 取得するメール数
        full_content: 本文を全文取得するかどうか

    Returns:
        List[Dict[str, Any]]: メールデータのリスト
    """
    try:
        print(f"📧 受信トレイ読み込み中: {inbox_file}")

        # mboxファイルとして開く
        mbox = mailbox.mbox(str(inbox_file))

        print(f"✅ 総メール数: {len(mbox)} 件")

        # メールを取得してソート
        mails = []
        for message in mbox:
            # full_contentに応じて切り詰めを制御
            mail_data = parse_mail_data(message, truncate=not full_content)
            mails.append(mail_data)

        # 受信日時でソート（新しい順）
        mails.sort(
            key=lambda x: x["received_time"] or datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo),
            reverse=True,
        )

        # 指定件数分返す
        return mails[:count]

    except Exception as e:
        print(f"❌ メール読み込みエラー: {type(e).__name__}: {e}")
        return []


def display_mails(mails: List[Dict[str, Any]]) -> None:
    """メール一覧を表示する.

    Args:
        mails: メールデータのリスト
    """
    if not mails:
        print("😭 表示するメールがないよ〜")
        return

    print(f"\n📬 最新 {len(mails)} 件のメール:")
    print("=" * 80)

    for i, mail in enumerate(mails, 1):
        print(f"\n{i}. 件名: {mail['subject']}")
        print(f"   送信者: {mail['sender']}")
        print(f"   受信日時: {mail['received_time']}")
        print(f"   メッセージID: {mail['message_id']}")
        print(f"   コンテンツタイプ: {mail['content_type']}")
        print(f"   マルチパート: {'はい' if mail['is_multipart'] else 'いいえ'}")
        print(f"   利用可能な形式: {', '.join(mail['available_formats'])}")

        # テキスト版と HTML版を分けて表示
        if mail["text_body"]:
            print(f"   テキスト本文: {mail['text_body']}")
        if mail["html_body"]:
            print(f"   HTML本文: {mail['html_body']}")
        if not mail["text_body"] and not mail["html_body"]:
            print(f"   本文: {mail['body']}")

        print("-" * 80)


def main():
    """メイン処理."""
    print("🚀 Thunderbird受信トレイ読み込み開始！")

    # プロファイル検索
    profile_dir = find_thunderbird_profile()
    if not profile_dir:
        print("😭 Thunderbirdのプロファイルが見つからないよ〜")
        print("手動でパスを指定する場合は以下を参考にして：")
        print("Windows: %APPDATA%\\Thunderbird\\Profiles\\xxxxxxxx.default")
        print("macOS: ~/Library/Thunderbird/Profiles/xxxxxxxx.default")
        print("Linux: ~/.thunderbird/xxxxxxxx.default")
        return

    # 受信トレイファイル検索
    inbox_file = find_inbox_file(profile_dir)
    if not inbox_file:
        print("😭 受信トレイファイルが見つからないよ〜")
        return

    # メール取得（全文表示モード！）
    mails = get_latest_mails(inbox_file, count=1, full_content=True)

    # 結果表示
    display_mails(mails)

    print(f"\n🎉 処理完了！{len(mails)} 件のメールを取得したよ〜✨")


if __name__ == "__main__":
    main()
