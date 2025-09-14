"""メールデータをDBへ保存するユースケース."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app_conf import MailVendor
from models.message import MessageCreate
from models.message_part import MessagePartCreate
from services.database.engine import get_engine
from services.database.manager.condition import FieldCondition
from services.database.manager.message_manager import MessageDBManager
from services.database.manager.message_part_manager import MessagePartDBManager
from services.database.manager.vendor_manager import VendorDBManager
from services.mail.base import BaseClientConfig, BaseMailClient
from services.mail.thunderbird import ThunderbirdClient
from utils.logging import get_logger

if TYPE_CHECKING:  # 型参照のみ (実行時依存を避ける)
    from sqlalchemy.engine import Engine

    from services.mail.base import MessageData

# 具体的な保存は MessageDBManager を中心に、必要に応じて
# MessagePartDBManager / Address 系 Manager を利用する想定。
# 実装は後続で追加。


logger = get_logger(__name__)


# メールクライアントの型エイリアス
type MailClient = BaseMailClient


def connect_vendor(vendor: MailVendor, config: BaseClientConfig | None = None) -> MailClient:
    """ベンダーに対応するメールクライアントを生成し、接続して返す.

    Args:
        vendor: 接続対象のメールベンダー.
        config: クライアント固有の接続設定 (無指定時はデフォルト).

    Returns:
        MailClient: 接続済みのクライアント.

    Raises:
        ValueError: 未対応のベンダーの場合.
    """
    if vendor == MailVendor.THUNDERBIRD:
        client: MailClient = ThunderbirdClient(config or {"connection_type": "local"})

    client.connect()
    return client


def _ensure_vendor(engine: Engine, vendor: MailVendor) -> int:
    """Vendor を保証し、ID を返す.

    既存なければ登録。登録後にIDを読み出す。
    """
    vendor_manager = VendorDBManager()
    # name は Enum(MailVendor) の .value が保存される想定
    vendor_manager.register(engine, vendor)  # 既にあれば内部でスキップ
    vendors = vendor_manager.read(
        engine,
        conditions=[FieldCondition(operator="eq", field="name", value=vendor.value)],
        limit=1,
    )
    if not vendors:
        msg = f"Vendor '{vendor.value}' not found after registration"
        logger.error(msg)
        raise RuntimeError(msg)
    vendor_id = vendors[0].id
    if vendor_id is None:
        msg = f"Vendor '{vendor.value}' has no id"
        logger.error(msg)
        raise RuntimeError(msg)
    return vendor_id


def save_mail(mail: MessageData, engine: Engine | None = None) -> None:
    """単一のメールをDBへ保存する.

    - RFC822 Message-ID で重複チェックし、既存ならスキップ。
    - Vendor を保証して vendor_id を採番。
    - Message を作成。
    - parts があれば parent_part_order を親子IDに解決して保存。
    """
    engine = engine or get_engine()

    # 重複チェック
    message_manager = MessageDBManager()
    exists = message_manager.read(
        engine,
        conditions=[FieldCondition(operator="eq", field="rfc822_message_id", value=mail.rfc822_message_id)],
        limit=1,
    )
    if exists:
        logger.info("Message already exists: %s", mail.rfc822_message_id)
        return

    # Vendor を確保
    vendor_id = _ensure_vendor(engine, mail.mail_vendor)

    # Message を保存
    create_obj = MessageCreate(
        rfc822_message_id=mail.rfc822_message_id,
        subject=mail.subject,
        date_sent=mail.date_sent,
        date_received=mail.date_received,
        in_reply_to=mail.in_reply_to,
        references_list=mail.references_list,
        is_read=mail.is_read,
        is_replied=mail.is_replied,
        is_flagged=mail.is_flagged,
        is_forwarded=mail.is_forwarded,
        vendor_id=vendor_id,
        folder_id=mail.folder_id,  # 無指定なら None のまま
    )
    message_manager.create(engine, create_obj)

    # 作成したレコードを再取得して ID を得る
    created = message_manager.read(
        engine,
        conditions=[FieldCondition(operator="eq", field="rfc822_message_id", value=mail.rfc822_message_id)],
        limit=1,
    )
    if not created:
        msg = f"Failed to read back created message: {mail.rfc822_message_id}"
        logger.error(msg)
        raise RuntimeError(msg)
    message_id = created[0].id
    if message_id is None:
        msg = f"Created message had no id: {mail.rfc822_message_id}"
        logger.error(msg)
        raise RuntimeError(msg)

    # メッセージに含まれるMIMEパーツがある場合は保存する
    if getattr(mail, "parts", None):
        part_manager = MessagePartDBManager()
        order_to_id: dict[int, int] = {}

        # order の昇順で処理 (生成側は順序で付与済みだが念のためソート)
        sorted_parts = sorted(
            mail.parts,
            key=lambda p: (p.part_order if p.part_order is not None else 1_000_000),
        )

        for p in sorted_parts:
            parent_part_id = None
            if p.parent_part_order is not None and p.parent_part_order in order_to_id:
                parent_part_id = order_to_id[p.parent_part_order]

            create_part = MessagePartCreate(
                message_id=message_id,  # type: ignore[arg-type]
                parent_part_id=parent_part_id,
                mime_type=p.mime_type,
                mime_subtype=p.mime_subtype,
                filename=p.filename,
                content_id=p.content_id,
                content_disposition=p.content_disposition,
                content=p.content,
                part_order=p.part_order,
                is_attachment=p.is_attachment,
                size_bytes=p.size_bytes,
            )

            part_manager.create(engine, create_part)

            # 直近で作成した Part の ID を再取得してマップ (コスト重めだが簡潔)
            # インデックス (message_id, is_attachment, part_order) によるフィルタで特定
            created_parts = part_manager.read(
                engine,
                conditions=[
                    FieldCondition(operator="eq", field="message_id", value=message_id),
                    FieldCondition(operator="eq", field="part_order", value=p.part_order),
                ],
                limit=1,
            )
            if created_parts and p.part_order is not None:
                created_part_id = created_parts[0].id
                if created_part_id is not None:
                    order_to_id[p.part_order] = created_part_id

    logger.info("Saved message: %s", mail.rfc822_message_id)


def save_mails(mails: list[MessageData], engine: Engine | None = None) -> None:
    """複数のメールをまとめてDBへ保存する.

    - Vendor ごとに最小限の登録チェックを行う。
    - 既存の RFC822 Message-ID は事前にスキップ。
    - 各メールは `save_mail` の単体処理を再利用。
    """
    if not mails:
        logger.info("save_mails called with empty list; nothing to do")
        return

    engine = engine or get_engine()

    # Vendor 事前保証 (重複チェックのため先に列挙)
    vendors = {m.mail_vendor for m in mails}
    for v in vendors:
        try:
            _ensure_vendor(engine, v)
        except Exception:
            logger.exception("Failed to ensure vendor: %s", getattr(v, "value", v))

    # 既存メッセージの事前スキャンで重複スキップ集合を作成
    message_manager = MessageDBManager()
    existing_ids: set[str] = set()
    for m in mails:
        try:
            exists = message_manager.read(
                engine,
                conditions=[FieldCondition(operator="eq", field="rfc822_message_id", value=m.rfc822_message_id)],
                limit=1,
            )
            if exists:
                existing_ids.add(m.rfc822_message_id)
        except Exception:
            logger.exception("Error checking existence for: %s", m.rfc822_message_id)

    # 保存処理
    saved = 0
    skipped = 0
    failed = 0
    for m in mails:
        if m.rfc822_message_id in existing_ids:
            skipped += 1
            logger.info("Skip existing message: %s", m.rfc822_message_id)
            continue
        try:
            save_mail(m, engine)
            saved += 1
        except Exception:
            failed += 1
            logger.exception("Failed to save message: %s", m.rfc822_message_id)

    logger.info("save_mails finished: saved=%d skipped=%d failed=%d", saved, skipped, failed)
