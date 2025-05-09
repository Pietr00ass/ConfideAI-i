import re

def detect(path: str) -> list[str]:
    """
    Wczytuje zawartość pliku jako tekst i wyszukuje sekwencje cyfr
    wyglądające jak numery kart kredytowych (13–16 cyfr, z opcjonalnymi spacjami lub myślnikami).
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception:
        return []

    # prosty regex na 13–16 cyfr z opcjonalnym separatorem
    pattern = r'\b(?:\d[ -]*?){13,16}\b'
    return re.findall(pattern, text)
