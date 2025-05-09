import os
import joblib

# Zakładamy, że masz zapisany pipeline/składowy model w model.pkl
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'model.pkl')
_model = joblib.load(MODEL_PATH)

def detect(path: str) -> list[str]:
    """
    Wczytuje zawartość pliku jako tekst i przekazuje do modelu ML,
    który zwraca listę etykiet lub fragmentów uznanych za wrażliwe.
    Zwracamy je jako listę stringów.
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception:
        return []

    # Jeśli pipeline zwraca dla całego dokumentu jedną etykietę,
    # trzeba go dostosować. Tutaj zakładamy, że zwraca listę fragmentów.
    preds = _model.predict([text])
    # Jeśli to pojedyncza etykieta, opakowujemy:
    if isinstance(preds, str):
        return [preds]
    return list(preds)
