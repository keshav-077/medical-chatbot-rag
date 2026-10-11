"""Explain uploaded lab text. Not a diagnosis."""

import json
import re

from orchestration.llm import complete
from orchestration.safety import DISCLAIMER

_ROW = re.compile(
    r"([A-Za-z][A-Za-z0-9 /+-]{1,40}?)\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z/%]+)?",
)


def parse_lab_rows(text: str) -> list[dict]:
    rows = []
    for match in _ROW.finditer(text or ""):
        rows.append(
            {
                "name": match.group(1).strip(),
                "value": match.group(2),
                "unit": (match.group(3) or "").strip(),
            }
        )
    return rows[:40]


def lab_node(state: dict) -> dict:
    lab_text = (state.get("lab_text") or "").strip()
    question = state.get("message") or "Explain this lab report in plain language."
    if not lab_text:
        return {
            "intent": "lab",
            "answer": (
                "Upload a PDF lab report on the Labs page. I will explain the values in plain "
                "language and list questions for your doctor. I will not diagnose you from the report."
            ),
            "citations": [],
            "risk_level": "info",
            "disclaimer": DISCLAIMER,
            "context": "",
        }
    rows = parse_lab_rows(lab_text)
    system = (
        "Explain a laboratory report for a patient in India. "
        "Use only the report text. Do not diagnose. "
        "For each value you mention, say what the name usually refers to and "
        "that the reference range on the report is the one that matters. "
        "End with three questions to ask a doctor. Under 180 words.\n\n"
        f"Report:\n{lab_text[:6000]}"
    )
    answer = complete(system, question, context=lab_text[:6000])
    if not answer:
        listed = ", ".join(f"{row['name']} {row['value']} {row['unit']}" for row in rows[:8])
        answer = (
            "I extracted these values but could not reach a language model to narrate them: "
            f"{listed or 'no numeric rows detected'}. "
            "Take the original report to your doctor. This is not a diagnosis."
        )
    excerpt = lab_text[:500]
    return {
        "intent": "lab",
        "answer": answer,
        "citations": [
            {
                "source": "Uploaded lab report",
                "excerpt": excerpt,
                "document_date": "",
                "section": "lab",
            }
        ],
        "context": lab_text[:2000],
        "risk_level": "caution",
        "disclaimer": DISCLAIMER,
        "extra": {"lab_rows": rows, "rows_json": json.dumps(rows)},
    }
