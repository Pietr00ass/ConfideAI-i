import os
from fastapi import (
    FastAPI, Request, UploadFile, File, Form, HTTPException, Depends
)
from fastapi.responses import (
    HTMLResponse, RedirectResponse, JSONResponse
)
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from auth import (
    get_authorization_url,
    fetch_user_info,
    send_verification_email,
    confirm_email_token,
    send_password_reset_email,
    confirm_reset_token
)
from db import init_db, engine
from models import User, AnalysisResult
from functions import (
    encrypt_file,
    decrypt_file,
    ocr_image,
    anonymize_image,
    hash_password,
    verify_password
)
from sqlmodel import Session, select, SQLModel, create_engine, func
from datetime import date, timedelta
from fastapi import Depends


app = FastAPI(debug=True)

# --- Sessions & DB ---
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-me")
)
init_db()

# --- Static / Templates ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Helpers ---
def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Musisz być zalogowany")
    with Session(engine) as sess:
        user = sess.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Nieprawidłowa sesja")
    return user
    
def require_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with Session(engine) as sess:
        return sess.get(User, user_id)

# --- Public Pages ---
@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/technology", response_class=HTMLResponse)
def technology(request: Request):
    return templates.TemplateResponse("technology.html", {"request": request})

@app.get("/auth/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/auth/register", response_class=HTMLResponse)
def register_submit(request: Request,
                    email: str = Form(...),
                    password: str = Form(...)):
    # haszujemy
    hashed = hash_password(password)
    # zapis do DB
    with Session(engine) as sess:
        user = User(email=email, password=hashed, is_active=False)
        sess.add(user)
        sess.commit()
    # wysyłamy mail
    send_verification_email(email)
    return templates.TemplateResponse(
        "register_sent.html",
        {"request": request, "email": email}
    )
@app.get("/auth/confirm_email", response_class=HTMLResponse)
def confirm_email(request: Request, token: str):
    email = confirm_email_token(token)
    if not email:
        return templates.TemplateResponse("register_failed.html", {"request": request})
    with Session(engine) as sess:
        statement = select(User).where(User.email == email)
        user = sess.exec(statement).one_or_none()
        if user:
            user.is_active = True
            sess.add(user)
            sess.commit()
    return templates.TemplateResponse("register_success.html", {"request": request})
@app.get("/analysis/new", response_class=HTMLResponse)
def analysis_new_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("analysis_new.html", {"request": request})

@app.post("/analysis/new")
async def analysis_new_submit(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    # TODO: zapisz plik, wywołaj analizę
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, user: User = Depends(get_current_user)):
    reports = []  # TODO: pobierz z bazy lub folderu
    return templates.TemplateResponse(
        "reports.html",
        {"request": request, "reports": reports}
    )

@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request, user: User = Depends(get_current_user)):
    logs = []  # TODO: pobierz logi z bazy
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "logs": logs}
    )
@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user}
    )

@app.post("/settings", response_class=HTMLResponse)
def settings_submit(
    request: Request,
    name: str = Form(...),
    password: str = Form(None),
    user: User = Depends(get_current_user)
):
    if password:
        user.password = hash_password(password)
    user.name = name
    with Session(engine) as sess:
        sess.add(user)
        sess.commit()
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user, "success": "Zapisano zmiany."}
    )

@app.get("/support", response_class=HTMLResponse)
def support_page(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("support.html", {"request": request})

@app.post("/support", response_class=HTMLResponse)
def support_submit(
    request: Request,
    subject: str = Form(...),
    message: str = Form(...),
    user: User = Depends(get_current_user)
):
    # TODO: zapisz ticket lub wyślij mail
    return templates.TemplateResponse(
        "support.html",
        {"request": request, "success": "Dziękujemy za zgłoszenie."}
    )

# --- Google OAuth / Auth0 ---
@app.get("/auth/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/auth/login", response_class=HTMLResponse)
def login_submit(request: Request,
                 email: str = Form(...),
                 password: str = Form(...)):
    with Session(engine) as sess:
        statement = select(User).where(User.email == email)
        user = sess.exec(statement).one_or_none()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Nieprawidłowy e-mail lub hasło."}
        )
    if not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Konto nieaktywne. Potwierdź e-mail."}
        )
    # ustawiamy sesję
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

                     
@app.get("/auth/callback")
def auth_callback(request: Request, code: str = None, state: str = None):
    if not code or state != request.session.get("oauth_state"):
        raise HTTPException(400, "Invalid OAuth callback")
    info = fetch_user_info(code, state)
    with Session(engine) as sess:
        user = sess.query(User).filter(User.email == info["email"]).first()
        if not user:
            user = User(email=info["email"], name=info.get("name"))
            sess.add(user)
            sess.commit()
            sess.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard")

# 1. Formularz “Zapomniałeś hasła?”
@app.get("/auth/forgot_password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/auth/forgot_password", response_class=HTMLResponse)
def forgot_password_submit(request: Request, email: str = Form(...)):
    send_password_reset_email(email)
    return templates.TemplateResponse(
        "forgot_sent.html",
        {"request": request, "email": email}
    )

# 2. Strona resetu hasła (GET – pokazujemy formularz z tokenem)
@app.get("/auth/reset_password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    email = confirm_reset_token(token)
    if not email:
        return templates.TemplateResponse("reset_invalid.html", {"request": request})
    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "token": token}
    )

# 3. Obsługa POST – faktyczna zmiana hasła
@app.post("/auth/reset_password", response_class=HTMLResponse)
def reset_password_submit(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
):
    email = confirm_reset_token(token)
    if not email:
        return templates.TemplateResponse("reset_invalid.html", {"request": request})
    # hashujemy i zapisujemy nowe hasło
    hashed = hash_password(new_password)
    with Session(engine) as sess:
        user = sess.exec(select(User).where(User.email == email)).one_or_none()
        if user:
            user.password = hashed
            sess.add(user)
            sess.commit()
    return templates.TemplateResponse("reset_success.html", {"request": request})


# --- Protected Dashboard ---
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request,
              user: User = Depends(get_current_user)):
    # 1) Pobierz wszystkie wyniki dla użytkownika
    with Session(engine) as sess:
        records = sess.exec(
            select(AnalysisResult)
            .where(AnalysisResult.user_id == user.id)
            .order_by(AnalysisResult.created_at.desc())
        ).all()

    # 2) Przygotuj listę dla Jinja2
    results_list = [{
        "filename": r.filename,
        "analysis_date": r.created_at.strftime("%Y-%m-%d %H:%M"),
        "emails": r.emails,
        "pesel_numbers": r.pesel_numbers,
        "credit_cards": r.credit_cards,
        "ml_predictions": r.ml_predictions
    } for r in records]

    # 3) Statystyki
    files_processed = len(records)
    sensitive_items = sum(
        len(r.emails) + len(r.pesel_numbers) + len(r.credit_cards)
        for r in records
    )

    # 4) Trend: ostatnie 7 dni
    today = date.today()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d")
             for i in reversed(range(7))]
    counts = []
    with Session(engine) as sess:
        for d in dates:
            cnt = sess.exec(
                select(func.count())
                .select_from(AnalysisResult)
                .where(
                    AnalysisResult.user_id == user.id,
                    func.date(AnalysisResult.created_at) == d
                )
            ).one()
            counts.append(cnt)

    # 5) Render
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": {
            "files_processed": files_processed,
            "sensitive_items": sensitive_items,
            "dates": dates,
            "counts": counts,
        },
        "results": results_list
    })

# --- HTML Forms (render) ---
@app.get("/encrypt", response_class=HTMLResponse)
def encrypt_form(request: Request):
    return templates.TemplateResponse("encrypt.html", {"request": request})

@app.post("/encrypt", response_class=HTMLResponse)
async def encrypt_post(
    request: Request,
    file: UploadFile = File(...),
    delete_orig: bool = Form(False)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    enc_path, key_path = encrypt_file(filepath, delete_orig)
    return templates.TemplateResponse(
        "encrypt_result.html",
        {"request": request, "enc_path": enc_path, "key_path": key_path}
    )

@app.get("/ocr", response_class=HTMLResponse)
def ocr_form(request: Request):
    return templates.TemplateResponse("ocr.html", {"request": request})

@app.post("/ocr", response_class=HTMLResponse)
async def ocr_post(
    request: Request,
    file: UploadFile = File(...)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    text = ocr_image(filepath)
    return templates.TemplateResponse(
        "ocr_result.html",
        {"request": request, "text": text}
    )

@app.get("/anonymize", response_class=HTMLResponse)
def anon_form(request: Request):
    return templates.TemplateResponse("anonymize.html", {"request": request})

@app.post("/anonymize", response_class=HTMLResponse)
async def anon_post(
    request: Request,
    file: UploadFile = File(...)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    anon_path = anonymize_image(filepath)
    return templates.TemplateResponse(
        "anonymize_result.html",
        {"request": request, "anon_path": anon_path}
    )

# --- JSON API Endpoints (for real-time progress) ---
@app.post("/api/encrypt", response_class=JSONResponse)
async def api_encrypt(
    file: UploadFile = File(...),
    delete_orig: bool = Form(False)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    enc_path, key_path = encrypt_file(filepath, delete_orig)
    return {"enc_path": enc_path, "key_path": key_path}

@app.post("/api/ocr", response_class=JSONResponse)
async def api_ocr(file: UploadFile = File(...)):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    text = ocr_image(filepath)
    return {"text": text}

@app.post("/api/anonymize", response_class=JSONResponse)
async def api_anonymize(file: UploadFile = File(...)):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    anon_path = anonymize_image(filepath)
    return {"anon_path": anon_path}
    
