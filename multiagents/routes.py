# multiagents/routes.py

import os
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlmodel import Session
from starlette.templating import Jinja2Templates
from werkzeug.utils import secure_filename  # zainstaluj werkzeug w requirements, lub zastąp własną funkcją

from db import engine
from models import ScanJob, ScanResult
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
    """Lista wszystkich zadań skanowania."""
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
    """Szczegóły jednego zadania wraz z wynikami poszczególnych agentów."""
    with Session(engine) as sess:
        job = sess.get(ScanJob, job_id)
        if not job:
            # można też flashować przez session, ale tutaj uproszczone
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
    """Formularz do przesyłania pliku i uruchamiania analizy."""
    return templates.TemplateResponse(
        "dashboard/scan_form.html",
        {"request": request}
    )

@router.post("/dashboard/scan", response_class=HTMLResponse)
async def scan_upload(request: Request, file: UploadFile = File(...)):
    """
    Przyjmuje plik, zapisuje go na dysku, uruchamia agentów
    i przekierowuje pod szczegóły zadania.
    """
    if not file.filename:
        # opcjonalnie można przekazać błąd do szablonu
        return RedirectResponse(request.url, status_code=303)

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    # 1) Zapisujemy nowe zadanie
    job = ScanJob(filename=filename)
    with Session(engine) as sess:
        sess.add(job)
        sess.commit()
        sess.refresh(job)

        # 2) Uruchamiamy agentów po kolei
        # wczytaj całą zawartość tekstu lub konwertuj PDF jeśli trzeba
        text = ""
        try:
            text = open(filepath, "r", encoding="utf-8", errors="ignore").read()
        except:
            # jeżeli to binarka, zostaw pusty tekst 
            text = ""

        for agent_name, fn in [
            ("email", detect_email),
            ("pesel", detect_pesel),
            ("credit_card", detect_cc),
            ("ml", detect_ml),
        ]:
            matches = fn(text)
            result = ScanResult(
                job_id=job.id,
                agent_name=agent_name,
                matches=matches or []
            )
            sess.add(result)
        sess.commit()

    # po skanowaniu przekieruj do szczegółów
    return RedirectResponse(f"/dashboard/job/{job.id}", status_code=303)
