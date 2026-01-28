#!/data/data/com.termux/files/usr/bin/env python3
"""
FastAPI backend for Termux-OSINT Manager (Original Edition)
Includes:
- Auth (simple JWT)
- Projects / Targets / Jobs
- Investigations & Evidence management
- Social discovery, image tools, PDF export
"""
import os
import time
from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, create_engine, Session, select
from models import User, Project, Target, Job, Result, Investigation, Evidence
from passlib.context import CryptContext
from jose import jwt, JWTError
from job_runner import run_job
import threading
from investigations import create_investigation, list_investigations, get_investigation, add_reference_evidence, save_file_evidence, list_evidence
from pdf_report import generate_pdf_for_investigation
from social_discovery import discover_username
from image_tools import download_image, compute_phash
from pathlib import Path

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "osint.db")
TEMPLATES_DIR = os.path.join(PROJECT_DIR, "..", "frontend")

# Security (change SECRET_KEY in production)
SECRET_KEY = "change-this-secret-in-production"
ALGO = "HS256"
ACCESS_EXPIRE = 3600

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Termux-OSINT Manager")
app.mount("/static", StaticFiles(directory=TEMPLATES_DIR), name="static")

# SQLite engine (check_same_thread False for threads)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)

# -- Auth helpers --
def create_user(username: str, password: str, role="operator"):
    with Session(engine) as s:
        u = s.exec(select(User).where(User.username == username)).first()
        if u:
            raise RuntimeError("User exists")
        uh = pwd_context.hash(password)
        user = User(username=username, pw_hash=uh, role=role)
        s.add(user); s.commit()

def authenticate_user(username: str, password: str):
    with Session(engine) as s:
        u = s.exec(select(User).where(User.username == username)).first()
        if not u: return None
        if not pwd_context.verify(password, u.pw_hash): return None
        return u

def create_token(user: User):
    payload = {"sub": user.username, "role": user.role, "exp": time.time() + ACCESS_EXPIRE}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def get_current_user(request: Request):
    auth = request.headers.get("authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ",1)[1].strip()
    else:
        token = auth.strip()
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        username = data.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    with Session(engine) as s:
        u = s.exec(select(User).where(User.username == username)).first()
        if not u:
            raise HTTPException(status_code=401, detail="User not found")
        return u

# -- Routes --
@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(TEMPLATES_DIR, "index.html"), "r") as f:
        return HTMLResponse(f.read())

@app.post("/api/register")
def register(username: str = Form(...), password: str = Form(...)):
    try:
        create_user(username, password)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    u = authenticate_user(username, password)
    if not u:
        raise HTTPException(status_code=401, detail="Bad credentials")
    token = create_token(u)
    return {"access_token": token, "token_type": "bearer", "username": u.username}

# Projects / Targets / Jobs
@app.post("/api/project")
def create_project(name: str = Form(...), description: str = Form(""), current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        p = Project(name=name, description=description, owner=current_user.username)
        s.add(p); s.commit(); s.refresh(p)
        return p

@app.post("/api/target")
def add_target(project_id: int = Form(...), value: str = Form(...), note: str = Form(""), in_scope: bool = Form(True), current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        t = Target(project_id=project_id, value=value, note=note, in_scope=in_scope)
        s.add(t); s.commit(); s.refresh(t)
        return t

@app.post("/api/job")
def create_job(job_type: str = Form(...), target: str = Form(...), project_id: int = Form(None), current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        j = Job(job_type=job_type, target=target, project_id=project_id, status="queued")
        s.add(j); s.commit(); s.refresh(j)
        th = threading.Thread(target=run_job, args=(engine, j.id), daemon=True)
        th.start()
        return {"job_id": j.id}

@app.get("/api/jobs")
def list_jobs(current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        rows = s.exec(select(Job).order_by(Job.created_at.desc())).all()
        return rows

@app.get("/api/result/{job_id}")
def get_result(job_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        r = s.exec(select(Result).where(Result.job_id == job_id)).first()
        if not r:
            raise HTTPException(status_code=404, detail="Not found")
        return r

# Investigations & Evidence
@app.post("/api/investigation")
def api_create_investigation(title: str = Form(...), description: str = Form(""), scope_note: str = Form(""), current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        inv = create_investigation(s, title, description, current_user.username, scope_note)
        return inv

@app.get("/api/investigations")
def api_list_investigations(current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        return list_investigations(s)

@app.post("/api/investigation/{inv_id}/attach/url")
def attach_reference(inv_id: int, kind: str = Form(...), title: str = Form(...), url: str = Form(...), current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        inv = get_investigation(s, inv_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")
        ev = add_reference_evidence(s, inv_id, kind, title, url, meta={"added_by": current_user.username})
        return ev

@app.post("/api/investigation/{inv_id}/attach/upload")
def attach_upload(inv_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    content = file.file.read()
    with Session(engine) as s:
        inv = get_investigation(s, inv_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Investigaton not found")
        ev = save_file_evidence(s, inv_id, file.filename, content, kind="file", title=file.filename, meta={"added_by": current_user.username})
        return ev

@app.post("/api/investigation/{inv_id}/attach/from-job/{job_id}")
def attach_job_result(inv_id: int, job_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        inv = get_investigation(s, inv_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")
        ev = add_reference_evidence(s, inv_id, "result", f"Job result {job_id}", f"job:{job_id}", meta={"added_by": current_user.username})
        return ev

@app.get("/api/investigation/{inv_id}/evidence")
def api_list_evidence(inv_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        return list_evidence(s, inv_id)

@app.post("/api/investigation/{inv_id}/download-image")
def api_download_image(inv_id: int, url: str = Form(...), current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        inv = get_investigation(s, inv_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")
        dest_dir = os.path.join(PROJECT_DIR, "evidence")
        path = download_image(url, dest_dir)
        if not path:
            raise HTTPException(status_code=400, detail="Failed to download image")
        ph = compute_phash(path)
        ev = save_file_evidence(s, inv_id, os.path.basename(path), open(path, "rb").read(), kind="image", title=os.path.basename(path), meta={"phash": ph, "source": url, "added_by": current_user.username})
        return ev

@app.get("/api/investigation/{inv_id}/export/pdf")
def api_export_pdf(inv_id: int, current_user: User = Depends(get_current_user)):
    with Session(engine) as s:
        inv = get_investigation(s, inv_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Investigation not found")
        path = generate_pdf_for_investigation(s, inv_id)
        return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))

@app.post("/api/discover/username")
def api_discover_username(username: str = Form(...), use_tor: bool = Form(False), current_user: User = Depends(get_current_user)):
    try:
        results = discover_username(username, use_tor=use_tor)
        return {"username": username, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Create default admin on first run
def ensure_admin():
    with Session(engine) as s:
        cnt = s.exec(select(User)).first()
        if not cnt:
            print("[*] Creating default admin: admin / admin (change immediately)")
            create_user("admin", "admin", role="admin")

if __name__ == "__main__":
    ensure_admin()
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)