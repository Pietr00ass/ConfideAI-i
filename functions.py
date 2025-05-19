import os
import logging
import secrets
import io

import cv2
import pytesseract
import spacy
import openai
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from PIL import Image

# ---- Konfiguracja OpenAI ----
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---- Haszowanie haseł ----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Zwraca zhashowane hasło."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Sprawdza zgodność hasła jawnego z hashem."""
    return pwd_context.verify(plain_password, hashed_password)

# ---- OCR ----
def ocr_image(image_path: str) -> str:
    """Zwraca tekst odczytany z obrazu za pomocą Tesseract."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, lang='pol')

# ---- Szyfrowanie plików ----
def encrypt_file(input_path: str, delete_original: bool = False) -> tuple[str, str]:
    key = secrets.token_bytes(32)
    iv  = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    data = open(input_path, 'rb').read()
    ct = encryptor.update(data) + encryptor.finalize()

    enc_path = input_path + '.enc'
    open(enc_path, 'wb').write(iv + ct)
    key_path = input_path + '.key'
    open(key_path, 'wb').write(key)

    if delete_original:
        os.remove(input_path)

    return enc_path, key_path

def decrypt_file(enc_path: str, key_path: str, delete_encrypted: bool = False) -> str:
    key = open(key_path, 'rb').read()
    raw = open(enc_path, 'rb').read()
    iv, ct = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    data = cipher.decryptor().update(ct) + cipher.decryptor().finalize()

    out_path = enc_path.replace('.enc', '.dec')
    open(out_path, 'wb').write(data)

    if delete_encrypted:
        os.remove(enc_path)
        os.remove(key_path)

    return out_path

# ---- Anonimizacja obrazu ----
def anonymize_image(image_path: str) -> str:
    """
    Wykrywa jednostki nazwane (PESEL itp.) przez spaCy i zamazuje je na obrazie.
    Zwraca ścieżkę do anonimizowanego pliku.
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang='pol')
    nlp = spacy.load("pl_core_news_sm")
    doc = nlp(text)
    boxes = pytesseract.image_to_boxes(img, lang='pol').splitlines()

    for ent in doc.ents:
        for box in boxes:
            parts = box.split()
            if len(parts) == 6 and parts[0] in ent.text:
                x, y, w, h = map(int, parts[1:5])
                # Zamazujemy prostokąt
                cv2.rectangle(
                    img,
                    (x, img.shape[0] - y),
                    (w, img.shape[0] - h),
                    (0, 0, 0),
                    thickness=-1
                )

    out_path = image_path.rsplit('.', 1)[0] + "_anon." + image_path.rsplit('.', 1)[1]
    cv2.imwrite(out_path, img)
    return out_path

# ---- Podsumowanie analizy z AI ----
def summarize_analysis(
    emails: list[str],
    pesels: list[str],
    credit_cards: list[str],
    ml_preds: dict[str, str]
) -> str:
    """
    Tworzy prompt na podstawie wyników i pyta GPT-3.5 o  krótkie streszczenie.
    W razie błędu API – zwraca prostą, lokalną wersję.
    """
    # 1) Lokalna wersja, gdyby AI nie odpowiedziało
    local_summary = (
        f"🔍 Znalazłem {len(emails)} e-maili.\n"
        f"🆔 Znalazłem {len(pesels)} numerów PESEL.\n"
        f"💳 Znalazłem {len(credit_cards)} kart kredytowych.\n"
        + (f"🤖 ML dokonało {len(ml_preds)} predykcji.\n" if ml_preds else "")
    )

    # 2) Budujemy prompt
    prompt = (
        "Podsumuj w kilku zdaniach wyniki analizy dokumentu:\n"
        + f"- E-maile: {emails or 'brak'}\n"
        + f"- PESEL-e: {pesels or 'brak'}\n"
        + f"- Karty: {credit_cards or 'brak'}\n"
        + (f"- Predykcje ML: {ml_preds}\n" if ml_preds else "")
        + "\nChciałbym krótkie, zwięzłe podsumowanie."
    )

    # 3) Zapytanie do OpenAI
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logging.warning(f"[WARN] summarize_analysis AI error: {e}")
        return local_summary
