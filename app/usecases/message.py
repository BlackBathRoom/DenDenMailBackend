"""メールデータのユースケース (保存・本文再構成など)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

import bleach

from bs4 import BeautifulSoup
from bs4.element import Tag
from sqlalchemy.exc import SQLAlchemyError

from app_conf import (
    CANDIDATE_ENCODINGS,
    HTML_SANITIZE_ALLOWED_ATTRS,
    HTML_SANITIZE_ALLOWED_PROTOCOLS,
    HTML_SANITIZE_EXTRA_TAGS,
    MailVendor,
)
from dtos.messages import AttachmentDTO, MessageBodyDTO
from models.address import AddressCreate, AddressUpdate
from models.message import MessageCreate
from models.message_address_map import AddressType, MessageAddressMapCreate
from models.message_part import MessagePartCreate
from services.database.engine import get_engine
from services.database.manager import (
    AddressDBManager,
    FolderDBManager,
    MessageAddressMapDBManager,
    MessageDBManager,
    MessagePartDBManager,
    VendorDBManager,
)
from services.database.manager.condition import FieldCondition
from services.mail.base import BaseClientConfig, BaseMailClient
from services.mail.thunderbird import ThunderbirdClient
from usecases.errors import ContentNotAvailableError, MessageNotFoundError, PartNotFoundError
from utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from sqlalchemy.engine import Engine

    from services.mail.base import MessageData

# 具体的な保存は MessageDBManager を中心に、必要に応じて
# MessagePartDBManager / Address 系 Manager を利用します。


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


def _normalize_email(email: str) -> str:
    return email.strip().lower()


class _AddressLike(Protocol):
    """Protocol for address-like entries from MessageData.

    This captures only the attributes used by address-saving logic.
    """

    email_address: object
    display_name: str | None


def _find_or_create_address(engine: Engine, email: str, display_name: str | None) -> int | None:
    """Find Address by email or create a new one. Optionally fill display_name.

    Returns address_id or None when failed.
    """
    addr_manager = AddressDBManager()
    # 既存検索
    existing = addr_manager.read(
        engine,
        conditions=[FieldCondition(operator="eq", field="email_address", value=email)],
        limit=1,
    )
    if existing is not None:
        addr = existing[0]
        addr_id = addr.id
        # display_name の補完(既存が None の場合のみ)
        if addr_id is not None and addr.display_name is None and display_name:
            try:
                addr_manager.update(
                    engine,
                    AddressUpdate(display_name=display_name),
                    conditions=[FieldCondition(operator="eq", field="id", value=addr_id)],
                )
            except SQLAlchemyError:
                logger.debug("Failed to update display_name for %s", email, exc_info=True)
        return addr_id

    # 新規作成
    created = addr_manager.create(engine, AddressCreate(email_address=email, display_name=display_name))
    return created.id


def _save_address_map(engine: Engine, message_id: int, address_id: int, addr_type: AddressType) -> None:
    """Create MessageAddressMap if not exists (best-effort)."""
    map_manager = MessageAddressMapDBManager()
    try:
        map_manager.create(
            engine,
            MessageAddressMapCreate(message_id=message_id, address_id=address_id, address_type=addr_type),
        )
    except SQLAlchemyError:
        # 複合PKの重複などは基本発生しない想定だが、念のためスキップ
        logger.debug(
            "Skip creating MessageAddressMap (maybe duplicate): msg=%s addr=%s type=%s",
            message_id,
            address_id,
            addr_type.value,
            exc_info=True,
        )


def _process_address_list(
    engine: Engine,
    message_id: int,
    items: Sequence[_AddressLike],
    addr_type: AddressType,
) -> None:
    """Normalize, deduplicate, and persist one address-type list."""
    seen: set[str] = set()
    for it in items or []:
        try:
            # EmailStr を文字列化し、正規化
            email = _normalize_email(str(it.email_address))
            if not email or email in seen:
                continue
            seen.add(email)

            addr_id = _find_or_create_address(engine, email, it.display_name or None)
            if addr_id is None:
                logger.warning("Address id missing after create/find: %s", email)
                continue

            _save_address_map(engine, message_id, addr_id, addr_type)
        except (AttributeError, TypeError, ValueError):
            logger.debug("Skip invalid address entry", exc_info=True)


def save_addresses_for_message(engine: Engine, message_id: int, m: MessageData) -> None:
    """Save all addresses (from/to/cc/bcc) for a message."""
    _process_address_list(engine, message_id, getattr(m, "from_addrs", []) or [], AddressType.FROM)
    _process_address_list(engine, message_id, getattr(m, "to_addrs", []) or [], AddressType.TO)
    _process_address_list(engine, message_id, getattr(m, "cc_addrs", []) or [], AddressType.CC)
    _process_address_list(engine, message_id, getattr(m, "bcc_addrs", []) or [], AddressType.BCC)


def save_message(message: MessageData, engine: Engine | None = None) -> None:
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
        conditions=[FieldCondition(operator="eq", field="rfc822_message_id", value=message.rfc822_message_id)],
        limit=1,
    )
    if exists:
        logger.info("Message already exists: %s", message.rfc822_message_id)
        return

    # Vendor を確保
    vendor_id = _ensure_vendor(engine, message.mail_vendor)

    # フォルダ名から folder_id を解決 (見つからなければ None のまま)
    folder_id = FolderDBManager().get_id(engine, message.folder) if message.folder else None

    # Message を保存
    create_obj = MessageCreate(
        rfc822_message_id=message.rfc822_message_id,
        subject=message.subject,
        date_sent=message.date_sent,
        date_received=message.date_received,
        in_reply_to=message.in_reply_to,
        references_list=message.references_list,
        is_read=message.is_read,
        is_replied=message.is_replied,
        is_flagged=message.is_flagged,
        is_forwarded=message.is_forwarded,
        vendor_id=vendor_id,
        folder_id=folder_id,
    )
    created_message = message_manager.create(engine, create_obj)
    message_id = created_message.id
    if message_id is None:
        msg = f"Created message had no id: {message.rfc822_message_id}"
        logger.error(msg)
        raise RuntimeError(msg)

    # メッセージに含まれるMIMEパーツがある場合は保存する
    if message.parts:
        part_manager = MessagePartDBManager()
        order_to_id: dict[int, int] = {}

        # order の昇順で処理 (生成側は順序で付与済みだが念のためソート)
        sorted_parts = sorted(
            message.parts,
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

            created_part = part_manager.create(engine, create_part)
            # 作成直後のIDをそのままマップ
            if p.part_order is not None and created_part.id is not None:
                order_to_id[p.part_order] = created_part.id

    # アドレスを保存
    try:
        save_addresses_for_message(engine, message_id, message)
    except SQLAlchemyError:
        logger.exception("Failed to save addresses for message: %s", message.rfc822_message_id)

    logger.info("Saved message: %s", message.rfc822_message_id)


def save_messages(messages: list[MessageData], engine: Engine | None = None) -> None:
    """複数のメールをまとめてDBへ保存する.

    - Vendor ごとに最小限の登録チェックを行う。
    - 既存の RFC822 Message-ID は事前にスキップ。
    - 各メールは `save_message` の単体処理を再利用。
    """
    if not messages:
        logger.info("save_mails called with empty list; nothing to do")
        return

    engine = engine or get_engine()

    # Vendor 事前保証 (重複チェックのため先に列挙)
    vendors = {m.mail_vendor for m in messages}
    for v in vendors:
        try:
            _ensure_vendor(engine, v)
        except Exception:
            logger.exception("Failed to ensure vendor: %s", v.value)

    # 既存メッセージの事前スキャンで重複スキップ集合を作成
    message_manager = MessageDBManager()
    existing_ids: set[str] = set()
    for m in messages:
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
    for m in messages:
        if m.rfc822_message_id in existing_ids:
            skipped += 1
            logger.info("Skip existing message: %s", m.rfc822_message_id)
            continue
        try:
            save_message(m, engine)
            saved += 1
        except Exception:
            failed += 1
            logger.exception("Failed to save message: %s", m.rfc822_message_id)

    logger.info("save_mails finished: saved=%d skipped=%d failed=%d", saved, skipped, failed)


def _decode_bytes(data: bytes | None) -> tuple[str | None, str | None]:
    """Decode bytes into str with common Japanese encodings.

    Returns (text, encoding). If data is None or decoding fails, returns (None, None).
    """
    if data is None:
        return None, None
    for enc in CANDIDATE_ENCODINGS:
        try:
            s = data.decode(enc)
            return s.replace("\r\n", "\n"), enc
        except UnicodeDecodeError as exc:  # continue trying, but log
            logger.debug("Decode failed with %s", enc, exc_info=exc)
            continue
    # last resort
    try:
        s = data.decode("utf-8", errors="replace")
        return s.replace("\r\n", "\n"), "utf-8?"
    except UnicodeDecodeError:
        return None, None


def _normalize_cid(cid: str | None) -> str | None:
    if cid is None:
        return None
    c = cid.strip().lower()
    if c.startswith("<") and c.endswith(">"):
        c = c[1:-1]
    return c


def _rewrite_cid_with_bs4(html: str, cid_map: dict[str, int], build_url: Callable[[int], str]) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.find_all("img"):
        if not isinstance(node, Tag):
            continue
        src = node.get("src")
        if isinstance(src, str) and src.lower().startswith("cid:"):
            key = _normalize_cid(src[4:])
            if key and key in cid_map:
                node["src"] = build_url(cid_map[key])
    return str(soup)


def _sanitize_html(html: str) -> str:
    allowed_tags = list(set(bleach.sanitizer.ALLOWED_TAGS).union(HTML_SANITIZE_EXTRA_TAGS))
    allowed_attrs = HTML_SANITIZE_ALLOWED_ATTRS
    allowed_protocols = list(HTML_SANITIZE_ALLOWED_PROTOCOLS)
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, protocols=allowed_protocols, strip=True)


def _ensure_message_belongs(engine: Engine, message_id: int, vendor_id: int, folder_id: int) -> None:
    """Validate that a message belongs to the given vendor and folder.

    Raises MessageNotFoundError if not found or ownership mismatch.
    """
    msg = MessageDBManager().read(
        engine,
        conditions=[
            {"operator": "eq", "field": "id", "value": message_id},
            {"operator": "eq", "field": "vendor_id", "value": vendor_id},
            {"operator": "eq", "field": "folder_id", "value": folder_id},
        ],
        limit=1,
    )
    if not msg:
        err = f"Message not found or not owned by vendor={vendor_id}, folder={folder_id}: id={message_id}"
        raise MessageNotFoundError(err)


class _PartLike(Protocol):
    """Protocol for message part-like objects used in body reconstruction.

    This captures only the attributes we access to avoid using Any.
    """

    mime_type: str | None
    mime_subtype: str | None
    filename: str | None
    content_id: str | None
    content: bytes | None
    part_order: int | None
    is_attachment: bool | None
    size_bytes: int | None
    id: int | None


def _partition_parts(
    parts: Sequence[_PartLike],
) -> tuple[list[_PartLike], _PartLike | None, _PartLike | None]:
    """Partition parts into body vs attachments and pick first plain/html.

    Returns (body_parts, attachments, plain_part, html_part).
    """
    attachments: list[_PartLike] = []
    plain_part: _PartLike | None = None
    html_part: _PartLike | None = None
    for p in parts:
        if p.is_attachment is True:
            attachments.append(p)
            continue
        if plain_part is None and (p.mime_type, p.mime_subtype) == ("text", "plain"):
            plain_part = p
        elif html_part is None and (p.mime_type, p.mime_subtype) == ("text", "html"):
            html_part = p
    return attachments, plain_part, html_part


def get_message_body(
    message_id: int,
    content_url_builder: Callable[[int], str],
    engine: Engine | None = None,
    *,
    vendor_id: int | None = None,
    folder_id: int | None = None,
) -> MessageBodyDTO:
    """Build sanitized message body with CID images rewritten to fetchable URLs.

    Args:
        message_id: Message id.
        engine: Optional DB engine.
        content_url_builder: Function to build content URL from part_id.
        vendor_id: Optional vendor id to validate message ownership.
        folder_id: Optional folder id to validate message ownership.

    Returns:
        MessageBodyDTO: Reconstructed body with attachments metadata.
    """
    engine = engine or get_engine()
    # Optional ownership validation when vendor/folder are provided
    if vendor_id is not None and folder_id is not None:
        _ensure_message_belongs(engine, message_id, vendor_id, folder_id)
    part_manager = MessagePartDBManager()
    parts = (
        part_manager.read(
            engine,
            conditions=[{"operator": "eq", "field": "message_id", "value": message_id}],
        )
        or []
    )

    # Separate body candidates and attachments in one pass, and pick first plain/html
    attachments, plain_part, html_part = _partition_parts(parts)

    text, text_enc = _decode_bytes(plain_part.content if plain_part else None)
    raw_html, html_enc = _decode_bytes(html_part.content if html_part else None)

    # Prepare CID map from any part with content_id
    cid_map: dict[str, int] = {}
    for p in parts:
        norm = _normalize_cid(p.content_id)
        if norm and p.id is not None:
            cid_map[norm] = p.id

    # Rewrite CID in html then sanitize
    html_processed: str | None = None
    if raw_html is not None:
        builder = content_url_builder
        temp = _rewrite_cid_with_bs4(raw_html, cid_map, builder)
        html_processed = _sanitize_html(temp)

    # Build attachments DTOs (exclude inline images from list)
    dto_attachments: list[AttachmentDTO] = []
    for p in attachments:
        if p.id is None:
            continue
        dto_attachments.append(
            AttachmentDTO(
                part_id=p.id,
                filename=p.filename,
                mime_type=p.mime_type or "application",
                mime_subtype=p.mime_subtype or "octet-stream",
                size_bytes=p.size_bytes,
                content_id=p.content_id,
                is_inline=False,
                content_url=content_url_builder(p.id),
            )
        )

    encoding = html_enc or text_enc
    return MessageBodyDTO(
        message_id=message_id,
        text=text,
        html=html_processed,
        encoding=encoding,
        attachments=dto_attachments,
    )


def get_message_part_content(
    vendor_id: int,
    folder_id: int,
    message_id: int,
    part_id: int,
    engine: Engine | None = None,
) -> tuple[bytes, str, dict[str, str] | None]:
    """Fetch a message part's raw content with media type and headers.

    Returns (content_bytes, media_type, headers).
    Raises RuntimeError on not found cases to be translated at router layer.
    """
    engine = engine or get_engine()
    part_manager = MessagePartDBManager()
    parts = part_manager.read(
        engine,
        conditions=[
            {"operator": "eq", "field": "id", "value": part_id},
            {"operator": "eq", "field": "message_id", "value": message_id},
        ],
        limit=1,
    )
    if not parts:
        msg = "Part not found"
        raise PartNotFoundError(msg)
    part = parts[0]

    # Ensure message belongs to vendor/folder
    _ensure_message_belongs(engine, message_id, vendor_id, folder_id)

    if not part.content:
        msg = "Content not available"
        raise ContentNotAvailableError(msg)

    media_type = f"{part.mime_type or 'application'}/{part.mime_subtype or 'octet-stream'}"

    headers: dict[str, str] | None = None
    disposition = (part.content_disposition or "").lower()
    if part.is_attachment or disposition.startswith("attachment"):
        filename = part.filename or "attachment"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return part.content, media_type, headers
