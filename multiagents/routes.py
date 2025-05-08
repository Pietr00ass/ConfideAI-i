
from flask import Blueprint, render_template
from models.analysis import SensitiveDataAnalysis

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard_view():
    results = SensitiveDataAnalysis.query.order_by(SensitiveDataAnalysis.analysis_date.desc()).all()
    return render_template('dashboard/dashboard.html', results=results)
