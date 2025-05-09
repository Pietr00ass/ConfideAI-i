import re

def detect(path: str) -> list[str]:
    """
    Wczytuje zawartość pliku i wyszukuje numery PESEL (11 cyfr).
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception:
        return []

    pattern = r'\b\d{11}\b'
    return re.findall(pattern, text)
