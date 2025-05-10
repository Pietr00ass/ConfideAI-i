# multiagents/routes.py
import os
from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select
from starlette.templating import Jinja2Templates

from db import engine
from models import ScanJob, ScanResult, User
from multiagents.agents.email_agent import detect as detect_email
from multiagents.agents.pesel_agent import detect as detect_pesel
from multiagents.agents.credit_card_agent import detect as detect_credit_card
from multiagents.agents.ml_agent import detect as detect_ml

router = APIRouter(prefix="/scan")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_current_user(request: Request) -> User:
    uid = request.session.get("user_id")
    if not uid:
        raise HTTPException(401, "Zaloguj się")
    with Session(engine) as sess:
        user = sess.get(User, uid)
    if not user:
        raise HTTPException(401, "Nieprawidłowa sesja")
    return user

@router.get("/", response_class=HTMLResponse)
def scan_form(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("scan/form.html", {"request": request, "user": user})

@router.post("/", response_class=HTMLResponse)
async def scan_upload(request: Request, file: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await file.read()
    # prosta funkcja "secure_filename"
    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    with open(path, "wb") as f:
        f.write(content)

    # 1) Zapis zadania
    job = ScanJob(user_id=user.id, filename=filename)
    with Session(engine) as sess:
        sess.add(job); sess.commit(); sess.refresh(job)
        # 2) Wczytaj tekst (jeśli da się zdekodować)
        try:
            text = content.decode("utf-8", errors="ignore")
        except:
            text = ""
        # 3) Uruchom agentów
        for name, fn in [
            ("email", detect_email),
            ("pesel", detect_pesel),
            ("credit_card", detect_credit_card),
            ("ml", detect_ml),
        ]:
            matches = fn(text) or []
            sess.add(ScanResult(job_id=job.id, agent_name=name, matches=matches))
        sess.commit()

    return RedirectResponse(f"/scan/{job.id}", status_code=303)

@router.get("/{job_id}", response_class=HTMLResponse)
def scan_detail(request: Request, job_id: int, user: User = Depends(get_current_user)):
    with Session(engine) as sess:
        job = sess.get(ScanJob, job_id)
        if not job or job.user_id != user.id:
            raise HTTPException(404, "Zadanie nie znalezione")
        results = sess.exec(select(ScanResult).where(ScanResult.job_id == job.id)).all()
    return templates.TemplateResponse("scan/detail.html", {
        "request": request, "job": job, "results": results, "user": user
    })

@router.get("/history", response_class=HTMLResponse)
def scan_history(request: Request, user: User = Depends(get_current_user)):
    with Session(engine) as sess:
        jobs = sess.exec(
            select(ScanJob).where(ScanJob.user_id == user.id).order_by(ScanJob.created_at.desc())
        ).all()
    return templates.TemplateResponse("scan/history.html", {
        "request": request, "jobs": jobs, "user": user
    })
