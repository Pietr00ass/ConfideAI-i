import os
import smtplib
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from email.message import EmailMessage
from authlib.integrations.requests_client import OAuth2Session

# ---- KONFIGURACJA ----
SECRET_KEY     = os.getenv("SECRET_KEY", "")
SENDER_EMAIL   = os.getenv("SENDER_EMAIL", "")
SENDER_PASS    = os.getenv("SENDER_PASS", "")
APP_URL        = os.getenv("APP_URL", "").rstrip("/")  # usuń końcowy '/'

# ---- SERIALIZATOR (token e-mail) ----
serializer = URLSafeTimedSerializer(SECRET_KEY)
RESET_SALT = "password-reset"

def send_verification_email(recipient: str):
    """Wysyła mail z linkiem potwierdzającym adres e-mail."""
    token = serializer.dumps(recipient, salt="email-confirm")
    link = f"{APP_URL}/auth/confirm_email?token={token}"
    
    msg = EmailMessage()
    msg["Subject"] = "Potwierdź swój adres e-mail w ConfideAI"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = recipient
    msg.set_content(
        f"Cześć!\n\n"
        f"Aby potwierdzić swój adres e-mail dla ConfideAI, kliknij poniższy link:\n\n"
        f"{link}\n\n"
        f"Link jest aktywny przez 1 godzinę."
    )

    # wysyłka przez SMTP Gmail SSL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)

def confirm_email_token(token: str, expiration: int = 3600) -> str | None:
    """
    Weryfikuje token. Zwraca e-mail, jeśli poprawny i nie wygasł,
    w przeciwnym razie None.
    """
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=expiration)
        return email
    except SignatureExpired:
        # token wygasł
        return None
    except BadSignature:
        # niepoprawny token
        return None
    except Exception:
        return None
        
# ---- PRZYKŁAD FUNKCJI WYSYŁAJĄCEJ MAIL RESETU HASŁA ----
def send_password_reset_email(recipient: str):
    token = serializer.dumps(recipient, salt=RESET_SALT)
    link = f"{APP_URL}/auth/reset_password?token={token}"
    msg = EmailMessage()
    msg["Subject"] = "Reset hasła w ConfideAI"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = recipient
    msg.set_content(
        f"Aby zresetować hasło, kliknij poniższy link (ważny 1h):\n\n{link}"
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)

# ---- FUNKCJA WERYFIKUJĄCA TOKEN RESETU ----
def confirm_reset_token(token: str, expiration: int = 3600) -> str | None:
    try:
        email = serializer.loads(token, salt=RESET_SALT, max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None

# ---- GOOGLE OAUTH2 ----
CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI  = f"{APP_URL}/auth/callback"  # obcięty APP_URL już bez '/'

AUTH_URI  = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
USER_URI  = "https://www.googleapis.com/oauth2/v3/userinfo"

def get_authorization_url() -> tuple[str, str]:
    """
    Zwraca (url, state) do przekierowania użytkownika na Google OAuth.
    """
    oauth = OAuth2Session(
        CLIENT_ID, CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI
    )
    url, state = oauth.create_authorization_url(
        AUTH_URI,
        access_type="offline",
        prompt="consent"
    )
    return url, state

def fetch_user_info(code: str, state: str) -> dict:
    """
    Po otrzymaniu kodu i stanu od Google pobiera dane użytkownika.
    """
    oauth = OAuth2Session(
        CLIENT_ID, CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI,
        state=state
    )
    oauth.fetch_token(
        TOKEN_URI,
        grant_type="authorization_code",
        code=code,
        client_secret=CLIENT_SECRET
    )
    return oauth.get(USER_URI).json()
