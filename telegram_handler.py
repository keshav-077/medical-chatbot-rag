"""Telegram webhook: link accounts, accept voice/PDF/location, then run LangGraph."""

from __future__ import annotations

import io
import logging
import os

import requests
from pypdf import PdfReader

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

telegram_sessions = {}


def send_telegram_message(chat_id: int, text: str) -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    max_len = 4000
    chunks = [text[i : i + max_len] for i in range(0, len(text or ""), max_len)] or [""]
    for msg in chunks:
        payload = {"chat_id": chat_id, "text": msg}
        try:
            response = requests.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                json={**payload, "parse_mode": "Markdown"},
                timeout=10,
            )
            if response.status_code >= 400:
                requests.post(f"{TELEGRAM_API_BASE}/sendMessage", json=payload, timeout=10)
        except requests.RequestException as exc:
            logger.error("Failed to send Telegram message: %s", exc)


def send_typing_action(chat_id: int) -> None:
    try:
        requests.post(
            f"{TELEGRAM_API_BASE}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"},
            timeout=5,
        )
    except requests.RequestException:
        pass


def set_webhook(webhook_url: str) -> dict:
    response = requests.post(
        f"{TELEGRAM_API_BASE}/setWebhook",
        json={"url": f"{webhook_url}/api/telegram"},
    )
    return response.json()


def _invoke_runner(rag_chain, text: str, user_id: int | None = None):
    if callable(rag_chain) and not hasattr(rag_chain, "invoke"):
        try:
            return rag_chain(text, user_id=user_id)
        except TypeError:
            return rag_chain(text)
    return rag_chain.invoke(text)


def _download_file(file_id: str) -> tuple[str, bytes]:
    meta = requests.get(
        f"{TELEGRAM_API_BASE}/getFile",
        params={"file_id": file_id},
        timeout=20,
    )
    meta.raise_for_status()
    path = ((meta.json() or {}).get("result") or {}).get("file_path") or ""
    filename = path.rsplit("/", 1)[-1] or "telegram.bin"
    data = requests.get(
        f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{path}",
        timeout=30,
    )
    data.raise_for_status()
    return filename, data.content


def process_telegram_update(update: dict, rag_chain) -> None:
    message = update.get("message") or {}
    if not message:
        return
    chat_id = (message.get("chat") or {}).get("id")
    tg_user = (message.get("from") or {}).get("id")
    user_name = (message.get("from") or {}).get("first_name") or "User"
    text = (message.get("text") or "").strip()
    if not chat_id:
        return

    from models import UserMedication, db
    from services.location import save_user_location
    from services.telegram_link import link_chat, user_for_chat

    linked = user_for_chat(chat_id)

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            user = link_chat(parts[1], chat_id)
            if user:
                send_telegram_message(
                    chat_id,
                    f"Linked to Bloom as {user.name}. I will send visit packs, lab reviews, and digests here.",
                )
                return
            send_telegram_message(chat_id, "That link code was not recognized. Copy it again from Profile.")
            return
        send_telegram_message(
            chat_id,
            f"Hello {user_name}. Ask a health question, send a lab PDF, share your location, "
            "or send a voice note.\n\nTo link your website account, open Profile and send "
            "`/start bloom_YOURCODE`.\n\nEducational only. Emergency: 112 or 108. Tele-MANAS 14416.",
        )
        return

    if text in {"/help"}:
        send_telegram_message(
            chat_id,
            "*Bloom commands*\n"
            "/start — welcome\n"
            "/help — this message\n"
            "/clear — new conversation\n"
            "Share location once for nearby care and AQI.\n"
            "Send a PDF lab report for an automatic review.\n"
            "Reply `undo med` if I added a medicine by mistake.",
        )
        return

    if text == "/clear":
        if tg_user in telegram_sessions:
            del telegram_sessions[tg_user]
        send_telegram_message(chat_id, "Conversation cleared. Ask a new question.")
        return

    if text.lower() in {"undo med", "stop meds", "undo medicine"} and linked:
        last = (
            UserMedication.query.filter_by(user_id=linked.id)
            .order_by(UserMedication.id.desc())
            .first()
        )
        if last:
            name = last.name
            db.session.delete(last)
            db.session.commit()
            send_telegram_message(chat_id, f"Removed {name} from your medicine list.")
        else:
            send_telegram_message(chat_id, "There was no medicine to remove.")
        return

    if message.get("location"):
        if not linked:
            send_telegram_message(
                chat_id,
                "Link your Bloom account from Profile first (`/start bloom_YOURCODE`), then share location again.",
            )
            return
        loc = message["location"]
        try:
            save_user_location(linked.id, loc.get("latitude"), loc.get("longitude"))
        except (TypeError, ValueError):
            send_telegram_message(chat_id, "I could not read that location pin.")
            return
        send_telegram_message(
            chat_id,
            "Saved your location for nearby care and air-quality notes. I will not keep sending map pins.",
        )
        return

    if message.get("voice") or message.get("audio"):
        media = message.get("voice") or message.get("audio")
        try:
            from services.voice import transcribe_audio

            filename, data = _download_file(media["file_id"])
            text = transcribe_audio(filename, data).strip()
        except Exception as exc:
            logger.warning("Telegram voice failed: %s", exc)
            send_telegram_message(chat_id, "I could not transcribe that voice note. Type the question instead.")
            return
        if not text:
            send_telegram_message(chat_id, "I heard no words in that voice note.")
            return

    document = message.get("document") or {}
    if document.get("file_id") and (
        (document.get("mime_type") or "").endswith("pdf")
        or (document.get("file_name") or "").lower().endswith(".pdf")
    ):
        if not linked:
            send_telegram_message(chat_id, "Link your Bloom account from Profile first, then send the PDF again.")
            return
        try:
            filename, data = _download_file(document["file_id"])
            reader = PdfReader(io.BytesIO(data))
            lab_text = "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:
            send_telegram_message(chat_id, f"I could not read that PDF: {exc}")
            return
        from missions.enqueue import enqueue_mission
        from models import UploadedDocument
        from services.storage import save_bytes

        key = save_bytes(filename, data)
        doc = UploadedDocument(
            user_id=linked.id,
            filename=filename,
            storage_key=key,
            doc_type="lab",
            status="extracted" if lab_text else "stored",
            extracted_text=(lab_text or "")[:20000],
        )
        from models import db as _db

        _db.session.add(doc)
        _db.session.commit()
        enqueue_mission(
            "lab_review",
            linked.id,
            payload={"lab_text": lab_text[:8000], "document_id": doc.id},
            dedupe_key=f"lab:{linked.id}:{doc.id}",
        )
        send_telegram_message(
            chat_id,
            "I received the report and started a review. I will message you when it is ready. This is not a diagnosis.",
        )
        return

    if not text:
        return

    send_typing_action(chat_id)
    try:
        response = _invoke_runner(rag_chain, text, user_id=linked.id if linked else None)
        if isinstance(response, dict):
            answer = response.get("result") or response.get("answer") or str(response)
        else:
            answer = str(response)
        send_telegram_message(
            chat_id,
            f"{answer}\n\n---\nThis is for informational purposes only. Consult a healthcare professional.",
        )
    except Exception as exc:
        logger.error("RAG chain error for Telegram user %s: %s", tg_user, exc)
        send_telegram_message(
            chat_id,
            "Sorry, I encountered an error processing your question. Please try again in a moment.",
        )
