"""Write an in-app notification, optional Telegram push, and a chat message."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from models import Conversation, Message, Notification, User, db

logger = logging.getLogger(__name__)


def notify(
    user_id: int,
    message: str,
    kind: str = "info",
    href: str = "/",
    payload: dict | None = None,
    push_telegram: bool = True,
    append_chat: bool = True,
) -> Notification:
    row = Notification(
        user_id=user_id,
        message=message,
        kind=kind,
        href=href or "/",
        payload_json=json.dumps(payload or {}),
        read=False,
    )
    db.session.add(row)
    if append_chat:
        _append_chat(user_id, message, kind)
    db.session.commit()
    if push_telegram:
        _push_telegram(user_id, message)
    return row


def _append_chat(user_id: int, message: str, kind: str) -> None:
    conversation = (
        Conversation.query.filter_by(user_id=user_id)
        .order_by(Conversation.updated_at.desc())
        .first()
    )
    if conversation is None:
        conversation = Conversation(user_id=user_id, title="Bloom updates")
        db.session.add(conversation)
        db.session.flush()
    db.session.add(
        Message(
            conversation_id=conversation.id,
            content=message,
            is_user=False,
            intent="mission",
            risk_level="info",
            citations_json=json.dumps([{"source": "bloom mission", "excerpt": kind}]),
        )
    )
    conversation.updated_at = datetime.now(timezone.utc)


def _push_telegram(user_id: int, message: str) -> None:
    user = db.session.get(User, user_id)
    if user is None or not user.telegram_chat_id:
        return
    try:
        from telegram_handler import send_telegram_message

        send_telegram_message(int(user.telegram_chat_id), message)
    except Exception as exc:
        logger.warning("Telegram notify failed for user %s: %s", user_id, exc)


def serialize_notification(row: Notification) -> dict:
    payload = {}
    if row.payload_json:
        try:
            payload = json.loads(row.payload_json)
        except json.JSONDecodeError:
            payload = {}
    return {
        "id": row.id,
        "message": row.message,
        "kind": row.kind,
        "read": bool(row.read),
        "href": row.href or "/",
        "payload": payload,
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }
