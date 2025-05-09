from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlmodel import Session, select
from werkzeug.utils import secure_filename
import os

from models import ScanJob, ScanResult
from db import engine
from multiagents.agents.email_agent import detect as detect_email
from multiagents.agents.pesel_agent import detect as detect_pesel
from multiagents.agents.cc_agent import detect as detect_cc
from multiagents.agents.ml_agent import detect as detect_ml

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates/dashboard')

# katalog na uploadowane pliki
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@dashboard_bp.route('/dashboard')
def dashboard_view():
    """Lista wszystkich zadań skanowania."""
    with Session(engine) as sess:
        jobs = sess.exec(
            select(ScanJob).order_by(ScanJob.created_at.desc())
        ).all()
    return render_template('dashboard.html', jobs=jobs)


@dashboard_bp.route('/dashboard/job/<int:job_id>')
def job_detail(job_id: int):
    """Szczegóły jednego zadania wraz z wynikami poszczególnych agentów."""
    with Session(engine) as sess:
        job = sess.get(ScanJob, job_id)
        if not job:
            flash(f"Zadanie o ID {job_id} nie istnieje.", "warning")
            return redirect(url_for('dashboard.dashboard_view'))
        results = sess.exec(
            select(ScanResult).where(ScanResult.job_id == job_id)
        ).all()
    return render_template('job_detail.html', job=job, results=results)


@dashboard_bp.route('/dashboard/scan', methods=['GET', 'POST'])
def scan_upload():
    """
    Formularz do przesyłania pliku i uruchamiania multiagentowej analizy.
    GET: pokazuje formularz, POST: zapisuje plik, wykonuje skan i przekierowuje do szczegółów.
    """
    if request.method == 'POST':
        f = request.files.get('file')
        if not f or f.filename == '':
            flash("Wybierz plik do analizy.", "danger")
            return redirect(request.url)

        filename = secure_filename(f.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        f.save(filepath)

        # 1) Zapisujemy nowe zadanie
        job = ScanJob(filename=filename)
        with Session(engine) as sess:
            sess.add(job)
            sess.commit()
            sess.refresh(job)

            # 2) Uruchamiamy agentów po kolei
            for agent_name, fn in [
                ("email", detect_email),
                ("pesel", detect_pesel),
                ("credit_card", detect_cc),
                ("ml", detect_ml),
            ]:
                matches = fn(filepath)  # każdy agent zwraca listę dopasowań
                result = ScanResult(
                    job_id=job.id,
                    agent_name=agent_name,
                    matches=matches or []
                )
                sess.add(result)
            sess.commit()

        flash(f"Przeskanowano plik '{filename}'.", "success")
        return redirect(url_for('dashboard.job_detail', job_id=job.id))

    # GET
    return render_template('scan_form.html')
