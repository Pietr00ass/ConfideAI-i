# multiagents/routes.py

import os
from fastapi import (
    APIRouter, Request, UploadFile, File, HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from starlette.templating import Jinja2Templates
from werkzeug.utils import secure_filename  # albo zamień na własną funkcję, jeśli nie chcesz dodawać werkzeug

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
        return RedirectResponse(request.url, status_code=303)

    # zabezpieczenie nazwy pliku
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

        # 2) Wczytaj tekst (jeśli to możliwe) i uruchamiamy agentów
        try:
            text = open(filepath, "r", encoding="utf-8", errors="ignore").read()
        except:
            text = ""

        for agent_name, fn in [
            ("email", detect_email),
            ("pesel", detect_pesel),
            ("credit_card", detect_cc),
            ("ml", detect_ml),
        ]:
            matches = fn(text) or []
            result = ScanResult(
                job_id=job.id,
                agent_name=agent_name,
                matches=matches
            )
            sess.add(result)
        sess.commit()

    # po skanowaniu przekieruj do szczegółów
    return RedirectResponse(f"/dashboard/job/{job.id}", status_code=303)
