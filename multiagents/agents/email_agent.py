import re

def detect(path_or_text):
    """
    Jeśli przekazujesz ścieżkę do pliku, odczytaj go jako tekst;
    w przeciwnym razie oczekuj już zwykłego stringa.
    """
    text = ""
    if isinstance(path_or_text, str) and os.path.exists(path_or_text):
        with open(path_or_text, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    else:
        text = path_or_text
    return re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
