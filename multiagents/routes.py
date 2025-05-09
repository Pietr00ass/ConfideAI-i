# multiagents/routes.py

import os
import io
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from starlette.templating import Jinja2Templates
from your_project.models import ScanJob, ScanResult  # dostosuj import
from your_project.db import engine                   # dostosuj import
from multiagents.agents.email_agent import detect as detect_email
from multiagents.agents.pesel_agent import detect as detect_pesel
from multiagents.agents.cc_agent import detect as detect_cc
from multiagents.agents.ml_agent import detect as detect_ml

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# katalog na uploadowane pliki
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request):
    with Session(engine) as sess:
        jobs = sess.exec(
            select(ScanJob).order_by(ScanJob.created_at.desc())
        ).all()
    return templates.TemplateResponse(
        "dashboard/dashboard.html",
        {"request": request, "jobs": jobs}
    )

@router.get("/dashboard/job/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    with Session(engine) as sess:
        job = sess.get(ScanJob, job_id)
        if not job:
            raise HTTPException(404, f"Zadanie o ID {job_id} nie istnieje.")
        results = sess.exec(
            select(ScanResult).where(ScanResult.job_id == job_id)
        ).all()
    return templates.TemplateResponse(
        "dashboard/job_detail.html",
        {"request": request, "job": job, "results": results}
    )

@router.get("/dashboard/scan", response_class=HTMLResponse)
def scan_form(request: Request):
    return templates.TemplateResponse(
        "dashboard/scan_form.html",
        {"request": request}
    )

@router.post("/dashboard/scan", response_class=HTMLResponse)
async def scan_upload(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "Nie wybrano pliku.")

    # Bezpieczna nazwa pliku
    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Zapis pliku
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Utwórz zadanie w DB
    job = ScanJob(filename=filename)
    with Session(engine) as sess:
        sess.add(job)
        sess.commit()
        sess.refresh(job)

        # Wczytaj plik jako tekst, jeśli to możliwe
        try:
            text = content.decode('utf-8', errors='ignore')
        except:
            text = ""

        # Uruchom agentów
        for name, fn in [
            ("email", detect_email),
            ("pesel", detect_pesel),
            ("credit_card", detect_cc),
            ("ml", detect_ml),
        ]:
            matches = fn(text)
            result = ScanResult(job_id=job.id, agent_name=name, matches=matches or [])
            sess.add(result)
        sess.commit()

    return RedirectResponse(f"/dashboard/job/{job.id}", status_code=303)
