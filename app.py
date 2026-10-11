"""
Medical Chatbot RAG — Flask Application (v2.1.0)

Serverless-ready, API-based embeddings, multi-LLM fallback.
Deployable on Vercel, Railway, Render, or any WSGI-compatible platform.
"""

import os
import logging
from datetime import datetime, timezone

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import text
from dotenv import load_dotenv

from src.embeddings import get_embedding_manager
from src.llm_providers import get_llm_manager
from config import get_config
from models import db, bcrypt, User, Conversation, Message
from services.telemetry import init_telemetry, new_request_id
import json
import re

# ============================================================
# Load environment & configure logging
# ============================================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================
# Create Flask app with environment-based config
# ============================================================

app = Flask(__name__)
app.config.from_object(get_config())

if os.environ.get("FLASK_ENV", "development").lower() == "production":
    from werkzeug.middleware.proxy_fix import ProxyFix

    # App Runner and load balancers terminate TLS and forward the original host.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# ============================================================
# Initialize extensions
# ============================================================

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# Rate limiting — uses memory:// locally, Redis in production
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Retrieval and generation run inside the LangGraph supervisor (lazy).
init_telemetry(app)


@app.before_request
def attach_request_id():
    g.request_id = new_request_id()


# ============================================================
# Error handlers
# ============================================================


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return jsonify(error="Rate limit exceeded. Please try again later."), 429


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    db.session.rollback()
    logger.error(f"Internal server error: {e}")
    return jsonify(error="Internal server error. Please try again."), 500


# ============================================================
# Health check endpoint
# ============================================================


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring and deployment verification.
    Returns status of all critical components.
    """
    # Test database connection
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    try:
        manager = get_embedding_manager()
        embedding_provider = manager.active_provider.name
        embedding_dimensions = manager.active_provider.dimensions
    except Exception as exc:
        embedding_provider = f"unavailable: {exc}"
        embedding_dimensions = None

    try:
        llm_provider = get_llm_manager().active_provider.name
    except Exception as exc:
        llm_provider = f"unavailable: {exc}"

    return jsonify(
        {
            "status": "ok",
            "version": "2.1.0",
            "database": db_status,
            "embedding_provider": embedding_provider,
            "embedding_dimensions": embedding_dimensions,
            "llm_provider": llm_provider,
            "request_id": getattr(g, "request_id", None),
        }
    )


# ============================================================
# Auth routes
# ============================================================


@app.route("/")
@login_required
def index():
    return render_template("chat.html")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Please check your login details and try again.", "danger")
            return redirect(url_for("login"))

        login_user(user, remember=remember)
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        next_page = request.args.get("next")
        return redirect(next_page or url_for("index"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Server-side validation
        email_re = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

        if not name or len(name) < 2:
            flash("Name must be at least 2 characters.", "danger")
            return redirect(url_for("signup"))

        if not re.match(email_re, email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("signup"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("signup"))

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email address already exists.", "danger")
            return redirect(url_for("signup"))

        new_user = User(name=name, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    from models import UserHealthProfile
    from services.telegram_link import ensure_link_token

    health = UserHealthProfile.query.filter_by(user_id=current_user.id).first()
    token = ensure_link_token(current_user)
    mcp_snippet = {
        "mcpServers": {
            "bloom": {
                "command": "python",
                "args": ["-m", "mcp_bloom"],
                "env": {
                    "BLOOM_MCP_TOKEN": os.getenv("BLOOM_MCP_TOKEN") or "set-BLOOM_MCP_TOKEN",
                    "BLOOM_MCP_CLIENT_TOKEN": os.getenv("BLOOM_MCP_TOKEN") or "set-BLOOM_MCP_TOKEN",
                    "BLOOM_MCP_USER_ID": str(current_user.id),
                },
            }
        }
    }
    return render_template(
        "profile.html",
        health=health,
        telegram_token=token,
        telegram_linked=bool(current_user.telegram_chat_id),
        mcp_snippet=json.dumps(mcp_snippet, indent=2),
    )


@app.route("/change-password", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
def change_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_new_password = request.form.get("confirm_new_password")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("profile"))

    if new_password != confirm_new_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("profile"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters long.", "danger")
        return redirect(url_for("profile"))

    current_user.set_password(new_password)
    db.session.commit()
    flash("Password updated successfully!", "success")
    return redirect(url_for("profile"))


# ============================================================
# Chat routes
# ============================================================


@app.route("/get", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def chat():
    msg = request.form["msg"]
    conversation_id = request.form.get("conversation_id")

    logger.info(f"User {current_user.id} input: {msg[:100]}...")

    # Get or create conversation
    if conversation_id:
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first()
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
    else:
        # Create new conversation
        conversation = Conversation(user_id=current_user.id, title="New Conversation")
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id

    user_message = Message(
        conversation_id=conversation_id,
        content=msg,
        is_user=True,
    )
    db.session.add(user_message)

    try:
        from orchestration.graphs.main import run_turn

        extra = {}
        from services.location import get_user_location

        coords = get_user_location(current_user.id)
        if coords:
            extra["lat"], extra["lng"] = coords
        result = run_turn(
            msg,
            user_id=current_user.id,
            extra=extra,
            request_id=getattr(g, "request_id", ""),
        )
        response = result.get("answer") or ""
        logger.info("Graph response intent=%s (%s chars)", result.get("intent"), len(response))

        assistant_message = Message(
            conversation_id=conversation_id,
            content=response,
            is_user=False,
            citations_json=json.dumps(result.get("citations") or []),
            risk_level=result.get("risk_level"),
            trace_id=result.get("trace_id"),
            intent=result.get("intent"),
        )
        db.session.add(assistant_message)

        # Update conversation timestamp and title if it's the first message
        conversation.updated_at = datetime.now(timezone.utc)
        if conversation.title == "New Conversation" and len(msg.strip()) > 0:
            if result.get("intent") == "guardrail" or result.get("risk_level") == "blocked":
                conversation.title = "Blocked request"
            else:
                from orchestration.guardrails import preview_for_log

                shown = preview_for_log(msg.strip())
                conversation.title = shown[:50] + ("..." if len(shown) > 50 else "")

        db.session.commit()
        if result.get("intent") not in {"emergency", "guardrail"} and result.get("risk_level") != "blocked":
            from missions.enqueue import maybe_enqueue_after_turn

            maybe_enqueue_after_turn(current_user.id, msg, result)

        return jsonify(
            {
                "answer": response,
                "conversation_id": conversation_id,
                "citations": result.get("citations") or [],
                "risk_level": result.get("risk_level"),
                "disclaimer": result.get("disclaimer"),
                "intent": result.get("intent"),
                "map_payload": result.get("map_payload") or {},
                "freshness": result.get("freshness") or "",
                "trace_id": result.get("trace_id"),
                "message_id": assistant_message.id,
                "appointment": result.get("appointment") or {},
                "guardrail_action": result.get("guardrail_action") or "allow",
            }
        )
    except Exception as e:
        logger.error(f"Chat error for user {current_user.id}: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/new-chat", methods=["POST"])
@login_required
def new_chat():
    conversation = Conversation(user_id=current_user.id, title="New Conversation")
    db.session.add(conversation)
    db.session.commit()
    return jsonify({"conversation_id": conversation.id})


@app.route("/load-chat/<int:conversation_id>")
@login_required
def load_chat(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=current_user.id
    ).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    messages = (
        Message.query.filter_by(conversation_id=conversation_id)
        .order_by(Message.timestamp.asc())
        .all()
    )

    chat_history = []
    for msg in messages:
        citations = []
        if msg.citations_json:
            try:
                citations = json.loads(msg.citations_json)
            except json.JSONDecodeError:
                citations = []
        chat_history.append(
            {
                "content": msg.content,
                "is_user": msg.is_user,
                "timestamp": msg.timestamp.strftime("%H:%M"),
                "citations": citations,
                "risk_level": msg.risk_level,
                "trace_id": msg.trace_id,
                "message_id": msg.id,
            }
        )

    return jsonify(
        {
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.strftime("%Y-%m-%d %H:%M"),
                "updated_at": conversation.updated_at.strftime("%Y-%m-%d %H:%M"),
            },
            "messages": chat_history,
        }
    )


@app.route("/delete-chat/<int:conversation_id>", methods=["POST"])
@login_required
def delete_chat(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=current_user.id
    ).first()
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    db.session.delete(conversation)
    db.session.commit()

    return jsonify({"success": True})


@app.route("/get-conversations")
@login_required
def get_conversations():
    conversations = (
        Conversation.query.filter_by(user_id=current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    conv_list = []
    for conv in conversations:
        conv_list.append(
            {
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.strftime("%Y-%m-%d %H:%M"),
                "updated_at": conv.updated_at.strftime("%Y-%m-%d %H:%M"),
                "message_count": len(conv.messages),
            }
        )

    return jsonify({"conversations": conv_list})


# ============================================================
# Initialize database tables
# ============================================================

with app.app_context():
    from db_setup import ensure_schema, seed_if_empty
    from routes.platform import bp as platform_bp

    ensure_schema()
    seed_if_empty()
    app.register_blueprint(platform_bp)
    logger.info("Database tables verified/created")

# ============================================================
# Run development server (not used on Vercel)
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)