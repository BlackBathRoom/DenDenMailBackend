"""デモ用EMLファイル生成スクリプト."""

import email.mime.text
import email.utils
import logging
import sys

from datetime import UTC, datetime, timedelta
from pathlib import Path

# プロジェクトルートを追加
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    # ロガーが利用できない場合は標準ロガーを使用
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)


class DemoEMLGenerator:
    """デモ用EMLファイル生成クラス."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """初期化.

        Args:
            output_dir: 出力ディレクトリ(デフォルト: demo/eml_files/)
        """
        self.output_dir = output_dir or Path(__file__).parent / "eml_files"
        self.output_dir.mkdir(exist_ok=True)

    def create_meeting_email(self) -> str:
        """会議関連のプレーンテキストメールを作成."""
        content = """来週金曜日に開催予定のプロジェクト会議についてお知らせします。

■ 会議概要
日時: 2024年11月15日(金)14:00-16:00
場所: 会議室A
参加者: 開発チーム全員

■ 議題
1. プロジェクトの進捗確認
2. 新機能の仕様検討
3. 次期スケジュールの調整
4. 課題と解決策の検討

事前に資料の確認をお願いします。
ご質問がございましたらお気軽にお声がけください。

よろしくお願いいたします。"""

        msg = email.mime.text.MIMEText(content, "plain", "utf-8")
        msg["Subject"] = "プロジェクト会議の件について"
        msg["From"] = "manager@example.com"
        msg["To"] = "team@example.com"
        msg["Date"] = email.utils.formatdate((datetime.now(UTC) - timedelta(days=1)).timestamp(), localtime=True)
        msg["Message-ID"] = "<meeting-001@example.com>"

        return msg.as_string()

    def create_system_maintenance_email(self) -> str:
        """システムメンテナンス関連のプレーンテキストメールを作成."""
        content = """システムメンテナンスのお知らせ

いつもシステムをご利用いただき、ありがとうございます。

下記の日程でシステムメンテナンスを実施いたします。

■ メンテナンス詳細
実施日時: 2024年11月17日(日)02:00-06:00
対象システム: 全サービス
影響範囲: 全機能が一時的に利用できません

■ 事前準備のお願い
- 重要なデータは事前にバックアップを取得してください
- 作業中のファイルは保存してからログアウトしてください
- メンテナンス時間中はアクセスできませんのでご注意ください

■ 実施内容
- データベースの最適化
- セキュリティパッチの適用
- システムパフォーマンスの向上

ご不便をおかけいたしますが、ご理解とご協力のほどよろしくお願いいたします。

システム管理者"""

        msg = email.mime.text.MIMEText(content, "plain", "utf-8")
        msg["Subject"] = "重要: システムメンテナンスのお知らせ"
        msg["From"] = "admin@example.com"
        msg["To"] = "all@example.com"
        msg["Date"] = email.utils.formatdate((datetime.now(UTC) - timedelta(hours=12)).timestamp(), localtime=True)
        msg["Message-ID"] = "<maintenance-001@example.com>"

        return msg.as_string()

    def create_feature_release_email(self) -> str:
        """新機能リリース関連のプレーンテキストメールを作成."""
        content = """新機能リリースのお知らせ

いつもご利用いただきありがとうございます。

この度、以下の新機能をリリースいたしました。

■ 新機能一覧

1. メール自動分類機能
   - AIがメールの内容を分析して自動で分類
   - 重要度に応じた優先表示
   - カスタム分類ルールの設定が可能

2. 優先度スコアリング機能
   - メールの重要度を1-3の数値で表示
   - 送信者の重要度や件名キーワードを自動解析
   - ユーザー設定による優先度の調整が可能

3. 類似メール検索機能
   - 自然言語での検索が可能
   - 関連するメールを素早く発見
   - 検索履歴の保存と再利用

■ 利用開始方法
1. アプリケーションを最新版に更新
2. 設定画面から新機能を有効化
3. チュートリアルに従って初期設定を完了

■ サポート情報
- 使い方ガイド: https://example.com/guide
- よくある質問: https://example.com/faq
- お問い合わせ: support@example.com

新機能を活用して、より効率的なメール管理をお楽しみください。

プロダクトチーム"""

        msg = email.mime.text.MIMEText(content, "plain", "utf-8")
        msg["Subject"] = "新機能リリースのお知らせ - メール管理がさらに便利に"
        msg["From"] = "product@example.com"
        msg["To"] = "users@example.com"
        msg["Date"] = email.utils.formatdate((datetime.now(UTC) - timedelta(hours=6)).timestamp(), localtime=True)
        msg["Message-ID"] = "<release-001@example.com>"

        return msg.as_string()

    def generate_all_demo_files(self) -> dict[str, Path]:
        """全てのデモEMLファイルを生成."""
        generated_files = {}

        # 会議メール
        meeting_email = self.create_meeting_email()
        meeting_file = self.output_dir / "meeting_email.eml"
        meeting_file.write_text(meeting_email, encoding="utf-8")
        generated_files["meeting_email"] = meeting_file

        # システムメンテナンスメール
        maintenance_email = self.create_system_maintenance_email()
        maintenance_file = self.output_dir / "system_maintenance.eml"
        maintenance_file.write_text(maintenance_email, encoding="utf-8")
        generated_files["system_maintenance"] = maintenance_file

        # 新機能リリースメール
        release_email = self.create_feature_release_email()
        release_file = self.output_dir / "feature_release.eml"
        release_file.write_text(release_email, encoding="utf-8")
        generated_files["feature_release"] = release_file

        logger.info("デモEMLファイルを %d 件生成: %s", len(generated_files), self.output_dir)
        return generated_files


def main() -> None:
    """メイン処理."""
    logger.info("デモEMLファイル生成開始!")

    generator = DemoEMLGenerator()
    generated_files = generator.generate_all_demo_files()

    logger.info("生成完了:")
    for name, file_path in generated_files.items():
        file_size = file_path.stat().st_size
        logger.info("  - %s: %s (%d bytes)", name, file_path, file_size)

    logger.info("出力ディレクトリ: %s", generator.output_dir)

    # 生成されたファイルの内容を簡単に確認
    logger.info("生成されたメールの概要:")
    for name, file_path in generated_files.items():
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        subject_line = next((line for line in lines if line.startswith("Subject:")), "件名: 不明")
        from_line = next((line for line in lines if line.startswith("From:")), "送信者: 不明")
        logger.info("  %s:", name)
        logger.info("    %s", subject_line)
        logger.info("    %s", from_line)

    logger.info("デモEMLファイル生成完了!")


if __name__ == "__main__":
    main()
