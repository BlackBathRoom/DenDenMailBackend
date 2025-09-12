"""データベース初期シード.

FOLDERS テーブルへ固定フォルダ (Inbox, Trash) を投入する。
存在チェックを行い、無ければ作成。競合時(同時起動など)はユニーク制約で
IntegrityError が発生し得るため握りつぶしてログのみ出す。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from models.folder import Folder
from utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.engine import Engine

logger = get_logger(__name__)


def _ensure_folders(session: Session, folders: Iterable[tuple[str, str]]) -> None:
    """指定フォルダ(system_type, name) の存在を保証する内部関数.

    Args:
        session (Session): DBセッション
        folders (Iterable[tuple[str, str]]): (system_type, name) のタプル列.
    """
    for system_type, name in folders:
        exists = session.exec(select(Folder).where(Folder.system_type == system_type)).first()
        if exists:
            continue
        folder = Folder(id=None, name=name, system_type=system_type)
        session.add(folder)
        logger.info("Seed folder added: %s (%s)", name, system_type)


def seed_core_data(engine: Engine) -> None:
    """コアとなる初期データを投入する.

    現状: FOLDERS (Inbox, Trash).
    """
    with Session(engine) as session:
        try:
            _ensure_folders(
                session,
                [
                    ("inbox", "Inbox"),
                    ("trash", "Trash"),
                ],
            )
            session.commit()
        except IntegrityError:
            # 同時起動などで他プロセスが先に投入したケース
            session.rollback()
            logger.warning("Folder seeding encountered IntegrityError (likely already inserted).")
        except Exception:  # 予期せぬ例外はログ化
            session.rollback()
            logger.exception("Unexpected error during folder seeding")
