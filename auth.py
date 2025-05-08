import os
import json
import smtplib
from itsdangerous import URLSafeTimedSerializer
from email.message import EmailMessage
from authlib.integrations.requests_client import OAuth2Session

# ---- KONFIG ----
SECRET_KEY     = os.getenv("SECRET_KEY")
SENDER_EMAIL   = os.getenv("SENDER_EMAIL")
SENDER_PASS    = os.getenv("SENDER_PASS")
APP_URL        = os.getenv("APP_URL")  # np. https://twoja-domena.com

# ---- SERIALIZER (token email) ----
serializer = URLSafeTimedSerializer(SECRET_KEY)

def send_verification_email(recipient: str):
    token = serializer.dumps(recipient, salt="email-confirm")
    link = f"{APP_URL}/auth/confirm_email?token={token}"
    msg = EmailMessage()
    msg["Subject"] = "Potwierdź swój adres e-mail w ConfideAI"
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = recipient
    msg.set_content(f"Kliknij, aby potwierdzić adres:\n\n{link}")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)

def confirm_email_token(token: str, expiration=3600):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=expiration)
        return email
    except:
        return None

# ---- GOOGLE OAuth2 ----
CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI  = f"{APP_URL}/auth/callback"

AUTH_URI  = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
USER_URI  = "https://www.googleapis.com/oauth2/v3/userinfo"

def get_authorization_url():
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

def fetch_user_info(code: str, state: str):
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
