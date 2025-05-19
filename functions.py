import os, logging, secrets, cv2, pytesseract
from passlib.context import CryptContext
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import spacy
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def ocr_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, lang='pol')

def encrypt_file(input_path, delete_original=False):
    key = secrets.token_bytes(32)
    iv  = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    data = open(input_path,'rb').read()
    ct = encryptor.update(data)+encryptor.finalize()
    enc_path = input_path + '.enc'
    open(enc_path,'wb').write(iv+ct)
    key_path = input_path + '.key'
    open(key_path,'wb').write(key)
    if delete_original: os.remove(input_path)
    return enc_path, key_path

def decrypt_file(enc_path, key_path, delete_encrypted=False):
    key = open(key_path,'rb').read()
    raw = open(enc_path,'rb').read()
    iv, ct = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    data = cipher.decryptor().update(ct)+cipher.decryptor().finalize()
    out = enc_path.replace('.enc','.dec')
    open(out,'wb').write(data)
    if delete_encrypted:
        os.remove(enc_path)
        os.remove(key_path)
    return out

def anonymize_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, lang='pol')
    nlp = spacy.load("pl_core_news_sm")
    doc = nlp(text)
    boxes = pytesseract.image_to_boxes(img, lang='pol').splitlines()
    for ent in doc.ents:
        for box in boxes:
            b = box.split()
            if len(b)==6 and b[0] in ent.text:
                x,y,w,h = map(int, b[1:5])
                cv2.rectangle(img, (x, img.shape[0]-y), (w, img.shape[0]-h), (0,0,0), -1)
    out = image_path.rsplit('.',1)[0] + "_anon." + image_path.rsplit('.',1)[1]
    cv2.imwrite(out, img)
    return out

# inicjalizacja kontekstu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Zwraca zhashowane hasło."""
    return pwd_context.hash(password)

def summarize_analysis(emails: list[str], pesels: list[str], credit_cards: list[str], ml_preds: dict) -> str:
    """
    Proste podsumowanie: policzy, ile czego znalazło i zwróci kilka linijek tekstu.
    Później możesz tu wstawić wywołanie do GPT lub innej AI.
    """
    parts = []
    parts.append(f"🔍 Znalazłem {len(emails)} e-maili.")
    parts.append(f"🆔 Znalazłem {len(pesels)} numerów PESEL.")
    parts.append(f"💳 Znalazłem {len(credit_cards)} kart kredytowych.")
    if ml_preds:
        parts.append(f"🤖 ML dokonało {len(ml_preds)} predykcji.")
    return "\n".join(parts)
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Sprawdza zgodność hasła jawnego z hash’em."""
    return pwd_context.verify(plain_password, hashed_password)
