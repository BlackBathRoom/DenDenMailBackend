"""Thunderbirdのパス管理モジュール."""

from os import environ
from pathlib import Path
from platform import system

from utils.log_config import get_logger

logger = get_logger(__name__)


# WindowsのThunderbirdプロファイルパスを取得するための候補ディレクトリ
appdata = environ.get("APPDATA", "")
local_appdata = environ.get("LOCALAPPDATA", "")
system_name = system()

thunderbird_candidates = [
    Path(environ.get("APPDATA", "")) / "Thunderbird" / "Profiles",
    Path(environ.get("LOCALAPPDATA", "")) / "AppData" / "Roaming" / "Thunderbird" / "Profiles",
]

packages_dir = Path(local_appdata) / "Packages"
if packages_dir.exists():
    for package_dir in packages_dir.iterdir():
        if package_dir.is_dir() and "thunderbird" in package_dir.name.lower():
            profiles_path = package_dir / "LocalCache" / "Roaming" / "Thunderbird" / "Profiles"
            if profiles_path.exists():
                thunderbird_candidates.append(profiles_path)

MAIL_DIRS = ["ImapMail", "Mail"]


class ThunderbirdPath:
    """Thunderbirdのプロファイルパスを管理するクラス."""

    def __init__(self) -> None:
        self.storage_path = self._get_storage_path()
        self.profile_path = self._get_profile_path(self.storage_path)
        self.mailbox_files = self._get_mailbox_files(self.profile_path) if self.profile_path else []

    def _get_storage_path(self) -> Path:
        """ローカルのThunderbirdのデータが保存されているディレクトリを取得.

        Raises:
            NotImplementedError: サポートされていないOSの場合に発生.
            FileNotFoundError: ディレクトリが見つからない場合に発生.
        """
        path = None
        match system_name:
            case "Windows":
                path = self._get_windows_storage_path()
            case _:
                msg = f"Unsupported OS: {system_name}."
                logger.error(msg)
                raise NotImplementedError(msg)

        if not path:
            msg = "Thunderbird profile path not found."
            logger.error(msg)
            raise FileNotFoundError(msg)
        return path

    def _get_windows_storage_path(self) -> Path | None:
        """WindowsのThunderbirdプロファイルパスを取得.

        Returns:
            Path | None: プロファイルパスが見つかった場合はそのパス、見つからなければNone。
        """
        path = None
        for candidate in thunderbird_candidates:
            if candidate.exists():
                path = candidate
                break
        if path:
            return path
        return None

    def _get_profile_path(self, path: Path) -> list[Path] | None:
        paths = []
        logger.info("Searching for Thunderbird profiles in: %s", path)
        for profile in path.iterdir():
            if profile.is_dir():
                mail_dirs = [profile / _dir for _dir in MAIL_DIRS]
                if any(mail_dir.exists() for mail_dir in mail_dirs if mail_dir.exists()):
                    paths.append(profile)
        if paths:
            return paths
        return None

    def _get_mailbox_files(self, path: list[Path]) -> list[Path]:
        """プロファイルパス内のメールボックスファイルのパスを取得.

        Returns:
            list[Path]: メールボックスファイルのパスリスト
        """
        mailbox_files = []

        for profile in path:
            logger.info("Searching mailboxes in profile: %s", profile)
            files = self._search_mailboxes_in_profile(profile)
            mailbox_files.extend(files)

        logger.info("Total mailbox files found: %d", len(mailbox_files))
        return mailbox_files

    def _search_mailboxes_in_profile(self, profile: Path) -> list[Path]:
        """単一プロファイル内のメールボックスファイルを検索."""
        files = []

        for mail_dir_name in MAIL_DIRS:
            mail_dir = profile / mail_dir_name
            if not mail_dir.exists():
                continue

            logger.info("Searching in %s directory: %s", mail_dir_name, mail_dir)
            account_files = self._search_accounts_in_mail_dir(mail_dir)
            files.extend(account_files)

        return files

    def _search_accounts_in_mail_dir(self, mail_dir: Path) -> list[Path]:
        """メールディレクトリ内のアカウントを検索."""
        files = []

        for account_dir in mail_dir.iterdir():
            if not account_dir.is_dir():
                continue

            logger.info("Checking account directory: %s", account_dir.name)
            account_files = self._find_mailbox_files_in_account(account_dir)
            files.extend(account_files)

        return files

    def _find_mailbox_files_in_account(self, account_dir: Path) -> list[Path]:
        """アカウントディレクトリ内のメールボックスファイルを検索."""
        files = []
        mailbox_files, msf_files = self._categorize_files(account_dir)

        # MSFファイルとペアになるメールボックスファイルのみを対象
        for mailbox_name, mailbox_path in mailbox_files.items():
            if mailbox_name not in msf_files:
                continue  # MSFファイルがない場合はスキップ

            # ファイルサイズチェック
            try:
                mailbox_size = mailbox_path.stat().st_size
                if mailbox_size > 0:
                    files.append(mailbox_path)
                    logger.info(
                        "Found mailbox: %s/%s (%d bytes)",
                        account_dir.name,
                        mailbox_name,
                        mailbox_size,
                    )
            except OSError as e:
                logger.warning(
                    "Failed to get file size for %s: %s",
                    mailbox_path,
                    e,
                )

        return files

    def _categorize_files(self, account_dir: Path) -> tuple[dict[str, Path], dict[str, Path]]:
        """アカウントディレクトリ内のファイルを分類."""
        mailbox_files = {}  # ファイル名 -> パス のマッピング
        msf_files = {}  # ファイル名 -> パス のマッピング

        for file_path in account_dir.iterdir():
            if not file_path.is_file():
                continue

            if file_path.suffix == ".msf":
                # MSF index file
                base_name = file_path.stem
                msf_files[base_name] = file_path
            elif file_path.suffix == "":
                # Mailbox file without extension
                mailbox_files[file_path.name] = file_path

        return mailbox_files, msf_files
