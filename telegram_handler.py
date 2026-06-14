# telegram_handler.py
# Telegram bot handler — plugs into existing RAG pipeline
# Does NOT modify any existing code

import os
import requests
import logging

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# In-memory session store for Telegram users
# Maps telegram user_id -> conversation_id (from your DB)
telegram_sessions = {}


def send_telegram_message(chat_id: int, text: str) -> None:
    """Send a reply back to Telegram user."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return

    # Telegram message limit is 4096 chars — split if needed
    max_len = 4000
    messages = [text[i:i+max_len] for i in range(0, len(text), max_len)]

    for msg in messages:
        try:
            response = requests.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": msg,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")


def send_typing_action(chat_id: int) -> None:
    """Show 'typing...' indicator while RAG pipeline runs."""
    try:
        requests.post(
            f"{TELEGRAM_API_BASE}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"},
            timeout=5
        )
    except requests.RequestException:
        pass  # Non-critical, ignore failures


def set_webhook(webhook_url: str) -> dict:
    """Register the webhook URL with Telegram. Call this once after deploy."""
    response = requests.post(
        f"{TELEGRAM_API_BASE}/setWebhook",
        json={"url": f"{webhook_url}/api/telegram"}
    )
    return response.json()


def process_telegram_update(update: dict, rag_chain) -> None:
    """
    Process a single Telegram update (message).

    Args:
        update: The raw webhook payload from Telegram
        rag_chain: Your existing LangChain RAG chain from app.py
    """
    # Extract message data
    message = update.get("message", {})
    if not message:
        return  # Ignore non-message updates (edits, reactions, etc.)

    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    user_name = message.get("from", {}).get("first_name", "User")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return

    # Handle /start command
    if text == "/start":
        welcome = (
            f"Hello {user_name}! I'm a Medical Q&A Assistant.\n\n"
            "Ask me any medical question and I'll answer based on "
            "my medical knowledge base.\n\n"
            "*Examples:*\n"
            "• What are symptoms of diabetes?\n"
            "• How does hypertension affect the kidneys?\n"
            "• What is the normal range for blood pressure?\n\n"
            "_Note: I provide information only. Always consult a doctor._"
        )
        send_telegram_message(chat_id, welcome)
        return

    # Handle /help command
    if text == "/help":
        help_text = (
            "*Medical Bot Commands:*\n"
            "/start — Welcome message\n"
            "/help — Show this message\n"
            "/clear — Start a new conversation\n\n"
            "Just type any medical question to get started!"
        )
        send_telegram_message(chat_id, help_text)
        return

    # Handle /clear command
    if text == "/clear":
        if user_id in telegram_sessions:
            del telegram_sessions[user_id]
        send_telegram_message(chat_id, "Conversation cleared. Ask me a new question!")
        return

    # Show typing indicator
    send_typing_action(chat_id)

    try:
        # Invoke the existing RAG chain directly
        # rag_chain is the same chain used by your web UI
        response = rag_chain.invoke(text)

        # Handle both string responses and dict responses
        if isinstance(response, dict):
            answer = response.get("result") or response.get("answer") or str(response)
        else:
            answer = str(response)

        # Add a disclaimer for medical context
        answer_with_disclaimer = (
            f"{answer}\n\n"
            "---\n"
            "_This is for informational purposes only. "
            "Consult a healthcare professional for medical advice._"
        )

        send_telegram_message(chat_id, answer_with_disclaimer)

    except Exception as e:
        logger.error(f"RAG chain error for Telegram user {user_id}: {e}")
        send_telegram_message(
            chat_id,
            "Sorry, I encountered an error processing your question. "
            "Please try again in a moment."
        )
