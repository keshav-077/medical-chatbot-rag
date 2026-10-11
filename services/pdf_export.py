"""Visit packet PDF: chat, labs, and questions for a clinician."""

import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_visit_pdf(title: str, sections: list[tuple[str, str]]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 48
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, title[:90])
    y -= 28
    pdf.setFont("Helvetica", 10)
    for heading, body in sections:
        if y < 80:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 10)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(40, y, heading[:80])
        y -= 16
        pdf.setFont("Helvetica", 10)
        for line in _wrap(body or "", 95):
            if y < 48:
                pdf.showPage()
                y = height - 48
                pdf.setFont("Helvetica", 10)
            pdf.drawString(40, y, line)
            y -= 13
        y -= 10
    pdf.save()
    return buffer.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    lines = []
    for paragraph in (text or "").splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            if len(current) + 1 + len(word) <= width:
                current += " " + word
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines
