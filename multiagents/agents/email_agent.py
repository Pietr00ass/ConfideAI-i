import re

def detect(path: str) -> list[str]:
    """
    Wczytuje zawartość pliku i wyszukuje adresy e-mail.
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception:
        return []

    pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    return re.findall(pattern, text)
