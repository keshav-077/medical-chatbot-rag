"""Authenticated pages beyond the original chat: meds, map, labs, visits, learn."""

import io
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from pypdf import PdfReader

from ingestion.pipeline import run_ingest
from models import (
    AppointmentRequest,
    Conversation,
    Feedback,
    LabResult,
    Message,
    Notification,
    ShareToken,
    UploadedDocument,
    UserFavoritePlace,
    UserHealthProfile,
    UserMedication,
    db,
)
from orchestration.graphs.main import run_turn
from services.calendar import auth_url, exchange_code, oauth_configured, suggest_slots
from services.pdf_export import build_visit_pdf
from services.storage import save_bytes
from services.voice import transcribe_audio
from telegram_handler import process_telegram_update
from worker.jobs import run_reminders, run_safety_notices

bp = Blueprint("platform", __name__)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _profile():
    row = UserHealthProfile.query.filter_by(user_id=current_user.id).first()
    if row is None:
        row = UserHealthProfile(user_id=current_user.id, allergies="", conditions="", notes="")
        db.session.add(row)
        db.session.commit()
    return row


def _worker_authorized() -> bool:
    secret = os.getenv("WORKER_WEBHOOK_SECRET")
    if not secret:
        return os.getenv("FLASK_ENV", "development") != "production"
    return request.headers.get("X-Worker-Secret") == secret


@bp.route("/meds", methods=["GET", "POST"])
@login_required
def meds():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if len(name) < 2:
            flash("Enter the medicine name.", "danger")
        else:
            db.session.add(
                UserMedication(
                    user_id=current_user.id,
                    name=name,
                    dose=(request.form.get("dose") or "").strip(),
                    frequency=(request.form.get("frequency") or "").strip(),
                )
            )
            db.session.commit()
            flash("Medicine saved to your profile.", "success")
        return redirect(url_for("platform.meds"))
    rows = (
        UserMedication.query.filter_by(user_id=current_user.id)
        .order_by(UserMedication.id.desc())
        .all()
    )
    return render_template("meds.html", medications=rows)


@bp.route("/meds/<int:med_id>/delete", methods=["POST"])
@login_required
def delete_med(med_id):
    row = UserMedication.query.filter_by(id=med_id, user_id=current_user.id).first_or_404()
    db.session.delete(row)
    db.session.commit()
    flash("Medicine removed.", "success")
    return redirect(url_for("platform.meds"))


@bp.route("/profile/health", methods=["POST"])
@login_required
def save_health():
    row = _profile()
    row.allergies = (request.form.get("allergies") or "").strip()
    row.conditions = (request.form.get("conditions") or "").strip()
    row.notes = (request.form.get("notes") or "").strip()
    row.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Health profile saved.", "success")
    return redirect(url_for("profile"))


@bp.route("/map")
@login_required
def care_map():
    favorites = UserFavoritePlace.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "map.html",
        maps_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
        favorites=favorites,
    )


@bp.route("/api/places")
@login_required
def api_places():
    from tools.places import search_nearby

    try:
        lat = float(request.args.get("lat"))
        lng = float(request.args.get("lng"))
    except (TypeError, ValueError):
        return jsonify({"error": "lat and lng are required"}), 400
    kind = request.args.get("kind") or "hospital"
    return jsonify(search_nearby(lat, lng, kind))


@bp.route("/api/favorites", methods=["POST"])
@login_required
def add_favorite():
    payload = request.get_json(silent=True) or {}
    place_id = (payload.get("place_id") or "").strip()
    name = (payload.get("name") or "").strip()
    if not place_id or not name:
        return jsonify({"error": "place_id and name are required"}), 400
    existing = UserFavoritePlace.query.filter_by(
        user_id=current_user.id, place_id=place_id
    ).first()
    if existing is None:
        db.session.add(
            UserFavoritePlace(
                user_id=current_user.id,
                place_id=place_id,
                name=name,
                kind=payload.get("kind") or "hospital",
                address=payload.get("address") or "",
                phone=payload.get("phone") or "",
                lat=payload.get("lat"),
                lng=payload.get("lng"),
            )
        )
        db.session.commit()
    return jsonify({"ok": True})


@bp.route("/favorites/<int:fav_id>/delete", methods=["POST"])
@login_required
def delete_favorite(fav_id):
    row = UserFavoritePlace.query.filter_by(id=fav_id, user_id=current_user.id).first_or_404()
    db.session.delete(row)
    db.session.commit()
    return redirect(url_for("platform.care_map"))


@bp.route("/labs", methods=["GET", "POST"])
@login_required
def labs():
    if request.method == "POST":
        upload = request.files.get("report")
        if upload is None or not upload.filename:
            flash("Choose a PDF lab report.", "danger")
            return redirect(url_for("platform.labs"))
        data = upload.read()
        key = save_bytes(upload.filename, data)
        text = ""
        if upload.filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(io.BytesIO(data))
                text = "\n".join((page.extract_text() or "") for page in reader.pages)
            except Exception as exc:
                flash(f"Could not read that PDF: {exc}", "danger")
        else:
            flash("Upload a PDF. Image OCR is not enabled on this server.", "danger")
        doc = UploadedDocument(
            user_id=current_user.id,
            filename=upload.filename,
            storage_key=key,
            doc_type="lab",
            status="extracted" if text else "stored",
            extracted_text=text[:20000],
        )
        db.session.add(doc)
        db.session.commit()
        if text:
            result = run_turn(
                "Explain my lab report",
                user_id=current_user.id,
                extra={"intent": "lab", "lab_text": text[:8000]},
            )
            rows = ((result.get("extra") or {}).get("lab_rows")) or []
            db.session.add(
                LabResult(
                    user_id=current_user.id,
                    document_id=doc.id,
                    summary=result.get("answer") or "",
                    rows_json=json.dumps(rows),
                )
            )
            db.session.commit()
            flash("Report explained below. This is not a diagnosis.", "success")
        return redirect(url_for("platform.labs"))
    documents = (
        UploadedDocument.query.filter_by(user_id=current_user.id)
        .order_by(UploadedDocument.created_at.desc())
        .all()
    )
    results = (
        LabResult.query.filter_by(user_id=current_user.id)
        .order_by(LabResult.created_at.desc())
        .all()
    )
    for result in results:
        try:
            result.parsed_rows = json.loads(result.rows_json or "[]")
        except json.JSONDecodeError:
            result.parsed_rows = []
    return render_template("labs.html", documents=documents, results=results)


@bp.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    profile = _profile()
    if request.method == "POST":
        row = AppointmentRequest(
            user_id=current_user.id,
            specialty=(request.form.get("specialty") or "general physician").strip(),
            reason=(request.form.get("reason") or "").strip(),
            preferred_times=(request.form.get("preferred_times") or "").strip(),
            place_name=(request.form.get("place_name") or "").strip(),
            phone=(request.form.get("phone") or "").strip(),
            place_id=(request.form.get("place_id") or "").strip(),
            status="draft",
        )
        remind = request.form.get("remind_at")
        if remind:
            try:
                parsed = datetime.fromisoformat(remind)
                row.remind_at = _aware(parsed)
            except ValueError:
                row.remind_at = datetime.now(timezone.utc)
        db.session.add(row)
        db.session.commit()
        flash("Appointment draft saved. Call the clinic to confirm.", "success")
        return redirect(url_for("platform.appointments"))
    rows = (
        AppointmentRequest.query.filter_by(user_id=current_user.id)
        .order_by(AppointmentRequest.created_at.desc())
        .all()
    )
    notes = (
        Notification.query.filter_by(user_id=current_user.id, kind="appointment")
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "appointments.html",
        appointments=rows,
        slots=suggest_slots(profile.google_refresh_token),
        calendar_ready=oauth_configured(),
        reminders=notes,
    )


@bp.route("/appointments/<int:appt_id>/remind-now", methods=["POST"])
@login_required
def remind_now(appt_id):
    row = AppointmentRequest.query.filter_by(id=appt_id, user_id=current_user.id).first_or_404()
    row.remind_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    row.reminded_at = None
    db.session.commit()
    run_reminders()
    flash("Reminder added to your notifications.", "success")
    return redirect(url_for("platform.appointments"))


@bp.route("/calendar/connect")
@login_required
def calendar_connect():
    if not oauth_configured():
        flash(
            "Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET to connect a calendar.",
            "danger",
        )
        return redirect(url_for("platform.appointments"))
    redirect_uri = url_for("platform.calendar_callback", _external=True)
    return redirect(auth_url(redirect_uri, state=str(current_user.id)))


@bp.route("/calendar/callback")
@login_required
def calendar_callback():
    if request.args.get("state") != str(current_user.id):
        flash("Calendar connection did not match this login.", "danger")
        return redirect(url_for("platform.appointments"))
    code = request.args.get("code")
    if not code:
        flash("Google did not return a code.", "danger")
        return redirect(url_for("platform.appointments"))
    token = exchange_code(code, url_for("platform.calendar_callback", _external=True))
    profile = _profile()
    if token.get("refresh_token"):
        profile.google_refresh_token = token["refresh_token"]
        db.session.commit()
        flash("Calendar connected for suggested times.", "success")
    else:
        flash("Google did not return a refresh token. Remove app access and try again.", "danger")
    return redirect(url_for("platform.appointments"))


@bp.route("/learn")
@login_required
def learn():
    from models import DrugMonograph

    drugs = DrugMonograph.query.order_by(DrugMonograph.generic_name.asc()).all()
    notices = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("learn.html", drugs=drugs, notices=notices)


@bp.route("/api/feedback", methods=["POST"])
@login_required
def feedback():
    payload = request.get_json(silent=True) or request.form
    rating = (payload.get("rating") or "").strip().lower()
    if rating not in ("up", "down"):
        return jsonify({"error": "rating must be up or down"}), 400
    message_id = payload.get("message_id")
    trace_id = payload.get("trace_id") or ""
    if message_id:
        message = Message.query.get(int(message_id))
        if message is None or message.conversation.user_id != current_user.id:
            return jsonify({"error": "message not found"}), 404
        trace_id = trace_id or (message.trace_id or "")
    db.session.add(
        Feedback(
            user_id=current_user.id,
            message_id=int(message_id) if message_id else None,
            rating=rating,
            trace_id=trace_id,
        )
    )
    db.session.commit()
    return jsonify({"ok": True, "trace_id": trace_id})


@bp.route("/api/share/<int:conversation_id>", methods=["POST"])
@login_required
def share_conversation(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=current_user.id
    ).first_or_404()
    token = secrets.token_urlsafe(24)
    db.session.add(
        ShareToken(
            token=token,
            conversation_id=conversation.id,
            user_id=current_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db.session.commit()
    return jsonify({"url": url_for("platform.shared", token=token, _external=True)})


@bp.route("/share/<token>")
def shared(token):
    row = ShareToken.query.filter_by(token=token).first_or_404()
    if _aware(row.expires_at) < datetime.now(timezone.utc):
        return render_template("share.html", expired=True, conversation=None, messages=[])
    conversation = Conversation.query.get_or_404(row.conversation_id)
    messages = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    return render_template(
        "share.html", expired=False, conversation=conversation, messages=messages
    )


@bp.route("/visits/<int:conversation_id>/pdf")
@login_required
def visit_pdf(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=current_user.id
    ).first_or_404()
    messages = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    chat = "\n".join(
        f"{'You' if msg.is_user else 'bloom'}: {msg.content}" for msg in messages
    )
    labs = (
        LabResult.query.filter_by(user_id=current_user.id)
        .order_by(LabResult.created_at.desc())
        .limit(3)
        .all()
    )
    lab_text = "\n\n".join(item.summary for item in labs)
    pdf = build_visit_pdf(
        f"Visit packet - {conversation.title}",
        [
            ("Conversation", chat),
            ("Recent lab explanations", lab_text or "None uploaded."),
            (
                "Questions for the clinician",
                "What is the most likely explanation? What should I watch for? Do any of my medicines need a change?",
            ),
            ("Disclaimer", "Educational summary only. Not a diagnosis or prescription."),
        ],
    )
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=bloom-visit.pdf"},
    )


@bp.route("/api/voice/transcribe", methods=["POST"])
@login_required
def voice_transcribe():
    upload = request.files.get("audio")
    if upload is None:
        return jsonify({"error": "audio file required"}), 400
    try:
        text = transcribe_audio(upload.filename, upload.read())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"text": text})


@bp.route("/api/telegram", methods=["POST"])
def telegram_webhook():
    update = request.get_json(force=True, silent=True) or {}

    def runner(text: str):
        return run_turn(text, user_id=None)

    process_telegram_update(update, runner)
    return jsonify({"ok": True})


@bp.route("/api/worker/run", methods=["POST"])
def worker_run():
    if not _worker_authorized():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(
        {
            "ingest": run_ingest(),
            "reminders": run_reminders(),
            "safety_notices": run_safety_notices(),
        }
    )
