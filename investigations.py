#!/data/data/com.termux/files/usr/bin/env python3
"""
Investigation & Evidence manager.
Saves uploaded files into backend/evidence/ and records Evidence rows.
"""
import os
import uuid
import time
from typing import Optional
from sqlmodel import Session, select
from models import Investigation, Evidence
from pathlib import Path
from utils import safe_filename

PROJECT_DIR = Path(__file__).resolve().parent
EVIDENCE_DIR = PROJECT_DIR / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

def create_investigation(session: Session, title: str, description: Optional[str], owner: Optional[str], scope_note: Optional[str]) -> Investigation:
    inv = Investigation(title=title, description=description, owner=owner, scope_note=scope_note)
    session.add(inv); session.commit(); session.refresh(inv)
    return inv

def list_investigations(session: Session):
    return session.exec(select(Investigation).order_by(Investigation.created_at.desc())).all()

def get_investigation(session: Session, inv_id: int):
    return session.get(Investigation, inv_id)

def add_reference_evidence(session: Session, inv_id: int, kind: str, title: str, reference: str, meta: Optional[dict] = None) -> Evidence:
    ev = Evidence(investigation_id=inv_id, kind=kind, title=title, reference=reference, meta=meta)
    session.add(ev); session.commit(); session.refresh(ev)
    return ev

def save_file_evidence(session: Session, inv_id: int, filename: str, file_bytes: bytes, kind="file", title: Optional[str] = None, meta: Optional[dict] = None) -> Evidence:
    safe = safe_filename(filename)
    unique = f"{int(time.time())}_{uuid.uuid4().hex}_{safe}"
    path = EVIDENCE_DIR / unique
    with open(path, "wb") as f:
        f.write(file_bytes)
    ev = Evidence(investigation_id=inv_id, kind=kind, title=title or safe, reference=str(path), meta=meta)
    session.add(ev); session.commit(); session.refresh(ev)
    return ev

def list_evidence(session: Session, inv_id: int):
    return session.exec(select(Evidence).where(Evidence.investigation_id == inv_id).order_by(Evidence.created_at.desc())).all()