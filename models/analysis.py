
from db import db
from datetime import datetime

class SensitiveDataAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    emails = db.Column(db.Text)
    pesel_numbers = db.Column(db.Text)
    credit_cards = db.Column(db.Text)
    ml_predictions = db.Column(db.Text)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
