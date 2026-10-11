"""One-time Telegram account link via /start bloom_<token>."""

from __future__ import annotations

import secrets

from models import User, db


def ensure_link_token(user: User) -> str:
    if user.telegram_link_token:
        return user.telegram_link_token
    user.telegram_link_token = secrets.token_urlsafe(16)
    db.session.commit()
    return user.telegram_link_token


def link_chat(token: str, chat_id: int | str) -> User | None:
    raw = (token or "").strip()
    if raw.startswith("bloom_"):
        raw = raw[6:]
    user = User.query.filter_by(telegram_link_token=raw).first()
    if user is None:
        return None
    chat = str(chat_id)
    taken = User.query.filter_by(telegram_chat_id=chat).first()
    if taken and taken.id != user.id:
        taken.telegram_chat_id = None
    user.telegram_chat_id = chat
    db.session.commit()
    return user


def user_for_chat(chat_id: int | str) -> User | None:
    return User.query.filter_by(telegram_chat_id=str(chat_id)).first()
