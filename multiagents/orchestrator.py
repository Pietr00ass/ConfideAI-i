
from .agents.email_agent import detect_emails
from .agents.pesel_agent import detect_pesel
from .agents.credit_card_agent import detect_credit_cards
from .agents.ml_agent import detect_sensitive_ml

def analyze_text(text):
    return {
        "emails": detect_emails(text),
        "pesel": detect_pesel(text),
        "credit_cards": detect_credit_cards(text),
        "ml_predictions": detect_sensitive_ml(text)
    }
