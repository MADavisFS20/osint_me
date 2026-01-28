#!/data/data/com.termux/files/usr/bin/env python3
"""
PDF report generator using ReportLab.
Generates a PDF report for an investigation and writes a SHA256 alongside it.
Optionally signs the PDF with GPG using pgp_sign.sign_file() if available.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from sqlmodel import select
from models import Investigation, Evidence, Result
from datetime import datetime
from pathlib import Path
import textwrap
import hashlib

from pgp_sign import sign_file  # optional: sign_file returns path to signature or None

PROJECT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def _draw_wrapped(c, text, x, y, leading=12):
    lines = []
    for paragraph in str(text).splitlines():
        wrapped = textwrap.wrap(paragraph, width=90)
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
    for line in lines:
        if y < 60:
            c.showPage()
            y = 750
        c.drawString(x, y, line)
        y -= leading
    return y

def generate_pdf_for_investigation(session, inv_id: int, sign_with_gpg: bool = False, gpg_key: str | None = None) -> str:
    inv = session.get(Investigation, inv_id)
    if not inv:
        raise RuntimeError("Investigation not found")
    evidences = session.exec(select(Evidence).where(Evidence.investigation_id == inv_id)).all()
    filename = REPORTS_DIR / f"investigation_{inv_id}_{int(datetime.utcnow().timestamp())}.pdf"
    c = canvas.Canvas(str(filename), pagesize=letter)
    y = 750
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, f"Investigation Report: {inv.title}")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Owner: {inv.owner or ''}    Created: {datetime.fromtimestamp(inv.created_at).isoformat()}")
    y -= 18
    c.drawString(40, y, f"Scope note: {inv.scope_note or ''}")
    y -= 24
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Description:")
    y -= 16
    c.setFont("Helvetica", 10)
    y = _draw_wrapped(c, inv.description or "(no description)", 45, y, leading=12)
    y -= 12
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Evidence")
    y -= 18
    c.setFont("Helvetica", 10)
    for ev in evidences:
        if y < 120:
            c.showPage(); y = 750
        c.drawString(45, y, f"- [{ev.kind}] {ev.title or ''} (added: {datetime.fromtimestamp(ev.created_at).isoformat()})")
        y -= 14
        ref = ev.reference or ""
        if ref.startswith("job:"):
            try:
                jid = int(ref.split(":",1)[1])
                r = session.exec(select(Result).where(Result.job_id == jid)).first()
                if r and r.output:
                    if y < 160:
                        c.showPage(); y = 750
                    c.setFont("Helvetica-Oblique", 9)
                    y = _draw_wrapped(c, r.output[:4000], 60, y, leading=10)
                    y -= 8
                    c.setFont("Helvetica", 10)
            except Exception:
                pass
        elif os.path.isfile(ref):
            try:
                img = ImageReader(ref)
                iw, ih = img.getSize()
                aspect = ih/iw
                display_w = 200
                display_h = display_w * aspect
                if y - display_h < 60:
                    c.showPage(); y = 750
                c.drawImage(img, 60, y - display_h, width=display_w, height=display_h, preserveAspectRatio=True, mask='auto')
                y -= (display_h + 8)
            except Exception:
                c.drawString(60, y, f"File: {ref}")
                y -= 12
        else:
            if y < 80:
                c.showPage(); y = 750
            c.setFont("Helvetica-Oblique", 9)
            y = _draw_wrapped(c, f"Reference: {ref}", 60, y, leading=10)
            y -= 6
            c.setFont("Helvetica", 10)
    c.showPage()
    c.save()

    # create sha256
    h = hashlib.sha256(open(filename, "rb").read()).hexdigest()
    sha_path = str(filename) + ".sha256"
    with open(sha_path, "w") as f:
        f.write(h)

    sig_path = None
    if sign_with_gpg:
        try:
            sig_path = sign_file(str(filename), key_id=gpg_key)
        except Exception:
            sig_path = None

    return str(filename)