"""Visit prep crew: historian → researcher → question writer → packager."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mcp_bloom.registry import find_nearby_care, get_profile, search_medical_knowledge
from missions.roles import run_roles
from models import Conversation, LabResult, Message, UserHealthProfile, UserMedication
from orchestration.safety import DISCLAIMER
from services.calendar import suggest_slots
from services.location import get_user_location
from services.notify import notify
from services.pdf_export import build_visit_pdf
from services.storage import save_bytes


def run_visit_pack(user_id: int, payload: dict) -> dict:
    history = _history(user_id)
    meds = [row.name for row in UserMedication.query.filter_by(user_id=user_id).all()]
    labs = (
        LabResult.query.filter_by(user_id=user_id)
        .order_by(LabResult.created_at.desc())
        .limit(3)
        .all()
    )
    lab_text = "\n\n".join(item.summary for item in labs) or "None uploaded."
    profile = get_profile(user_id)
    message = (payload or {}).get("message") or history[:240] or "upcoming clinic visit"
    research = search_medical_knowledge(message)[:3]
    research_text = "\n".join(
        f"- {item.get('source')}: {item.get('excerpt', '')[:180]}" for item in research
    ) or "No library excerpt."
    questions = _questions(message, history, lab_text)
    coords = get_user_location(user_id)
    nearby = ""
    if coords:
        places = find_nearby_care(coords[0], coords[1], "hospital").get("places") or []
        nearby = "\n".join(
            f"- {row.get('name')} ({row.get('distance_km')} km) {row.get('phone') or ''}"
            for row in places[:5]
        )
    health = UserHealthProfile.query.filter_by(user_id=user_id).first()
    slots = suggest_slots(health.google_refresh_token if health else None)
    script = (
        f"Hello, I would like an appointment. Reason: {message[:240]}. "
        f"Preferred time: {', '.join(slots[:2]) or 'next weekday morning'}."
    )
    sections = [
        ("Recent conversation", history or "No recent chat."),
        ("Medicines and profile", f"Meds: {', '.join(meds) or 'none listed'}\n"
         f"Allergies: {profile.get('allergies') or 'none listed'}\n"
         f"Conditions: {profile.get('conditions') or 'none listed'}"),
        ("Recent lab explanations", lab_text),
        ("Library notes", research_text),
        ("Questions for the clinician", questions),
        ("Call script", script),
        ("Nearby hospitals", nearby or "Share location on the Care Map or Telegram once."),
        ("Suggested times", "\n".join(slots) or "Next weekday morning."),
        ("Disclaimer", DISCLAIMER),
    ]
    pdf = build_visit_pdf("Bloom visit pack", sections)
    storage_key = save_bytes("bloom-visit.pdf", pdf)
    summary = (
        "I prepared a visit pack for you.\n\n"
        f"Questions:\n{questions}\n\n"
        f"Call script: {script}\n\n"
        + (f"Nearby:\n{nearby}\n\n" if nearby else "")
        + "I cannot book the clinic. Open Chat to read the pack. "
        + DISCLAIMER
    )
    notify(
        user_id,
        summary,
        kind="visit_pack",
        href="/",
        payload={"storage_key": storage_key, "script": script},
    )
    return {
        "summary": summary,
        "storage_key": storage_key,
        "questions": questions,
        "script": script,
    }


def _history(user_id: int) -> str:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    conversation = (
        Conversation.query.filter_by(user_id=user_id)
        .order_by(Conversation.updated_at.desc())
        .first()
    )
    if conversation is None:
        return ""
    rows = (
        Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.timestamp.desc())
        .limit(40)
        .all()
    )
    rows = list(reversed(rows))
    cutoff = since.replace(tzinfo=None) if since.tzinfo else since
    kept = []
    for row in rows:
        stamp = row.timestamp
        if stamp is None:
            kept.append(row)
            continue
        compare = stamp.replace(tzinfo=None) if stamp.tzinfo else stamp
        if compare >= cutoff:
            kept.append(row)
    rows = kept
    return "\n".join(
        f"{'You' if row.is_user else 'bloom'}: {row.content[:400]}" for row in rows
    )


def _questions(message: str, history: str, lab_text: str) -> str:
    fallback = (
        "1. What is the most likely explanation for these symptoms?\n"
        "2. What should I watch for that means I should come back sooner?\n"
        "3. Do any of my current medicines need a change?\n"
        "4. Are any tests needed after this visit?\n"
        "5. What can I do at home that is safe for me?"
    )
    try:
        from missions.crews.crewai_adapter import run_crewai_roles

        crafted = run_crewai_roles(
            "visit_pack",
            [
                ("historian", "Summarize the patient's last week in 80 words. No diagnosis.", history or message),
                (
                    "researcher",
                    "List educational talking points for an India clinic visit. No diagnosis.",
                    message,
                ),
                (
                    "question_writer",
                    "Write exactly 5 numbered questions for a clinician. No diagnosis.",
                    f"Complaint: {message}\nLabs: {lab_text[:800]}",
                ),
            ],
        )
        if crafted:
            return crafted
    except Exception:
        pass
    crafted = run_roles(
        [
            (
                "question_writer",
                "Write exactly 5 numbered questions a patient in India can ask a clinician. "
                "Do not diagnose. Do not suggest a dose.",
                f"Complaint: {message}\nNotes:\n{history[:1500]}\nLabs:\n{lab_text[:800]}",
            )
        ],
        fallback=fallback,
    )
    return crafted or fallback
