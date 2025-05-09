from sqlmodel import Session, select
from models import ScanJob, ScanResult
from db import engine
from multiagents.agents import email_agent, pesel_agent, cc_agent, ml_agent
from flask import Blueprint, render_template
from models.analysis import SensitiveDataAnalysis

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard_view():
    results = SensitiveDataAnalysis.query.order_by(SensitiveDataAnalysis.analysis_date.desc()).all()
    return render_template('dashboard/dashboard.html', results=results)

def scan_file(path: str):
    # 1) Zapisz job
    job = ScanJob(filename=path)
    with Session(engine) as sess:
        sess.add(job); sess.commit(); sess.refresh(job)
        job_id = job.id

        # 2) Wykonaj analizę każdym agentem
        for name, fn in [
            ("email", email_agent.detect),
            ("pesel", pesel_agent.detect),
            ("credit_card", cc_agent.detect),
            ("ml", ml_agent.detect),
        ]:
            matches = fn(path)  # zwraca listę dopasowań
            result = ScanResult(job_id=job_id, agent_name=name, matches=matches)
            sess.add(result)
        sess.commit()
    return job

def get_job(job_id: int):
    with Session(engine) as sess:
        job = sess.get(ScanJob, job_id)
        results = sess.exec(
            select(ScanResult).where(ScanResult.job_id == job_id)
        ).all()
    return job, results

def list_jobs():
    with Session(engine) as sess:
        return sess.exec(select(ScanJob).order_by(ScanJob.created_at.desc())).all()
