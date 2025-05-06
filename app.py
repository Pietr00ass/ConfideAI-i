import os
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware


from auth import get_authorization_url, fetch_user_info
from db import init_db, engine
from models import User
from functions import encrypt_file, decrypt_file, ocr_image, anonymize_image
from sqlmodel import Session

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY","change-me"))
init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def landing(request: Request): return templates.TemplateResponse("landing.html",{"request":request})
@app.get("/about", response_class=HTMLResponse)
def about(request: Request): return templates.TemplateResponse("about.html",{"request":request})
@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request): return templates.TemplateResponse("contact.html",{"request":request})
@app.get("/technology", response_class=HTMLResponse)
def technology(request: Request): return templates.TemplateResponse("technology.html",{"request":request})

@app.get("/auth/login")
def login(request: Request):
    url,state = get_authorization_url()
    request.session["oauth_state"] = state
    return RedirectResponse(url)

@app.get("/auth/callback")
def callback(request: Request, code: str=None, state: str=None):
    if not code or state!=request.session.get("oauth_state"):
        raise HTTPException(400,"Invalid OAuth callback")
    info = fetch_user_info(code, state)
    with Session(engine) as s:
        user = s.query(User).filter(User.email==info["email"]).first()
        if not user:
            user=User(email=info["email"],name=info.get("name"))
            s.add(user); s.commit(); s.refresh(user)
    request.session["user_id"]=user.id
    return RedirectResponse("/dashboard")

def require_user(request):
    uid=request.session.get("user_id")
    if not uid: return None
    with Session(engine) as s: return s.get(User,uid)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    u=require_user(request)
    if not u: return RedirectResponse("/")
    return templates.TemplateResponse("dashboard.html",{"request":request,"user":u})

@app.get("/encrypt", response_class=HTMLResponse)
def encrypt_form(request: Request):
    return templates.TemplateResponse("encrypt.html", {"request": request})

@app.post("/encrypt", response_class=HTMLResponse)
async def encrypt_post(
    request: Request,
    file: UploadFile = File(...),
    delete_orig: bool = Form(False)
):
    # Zapis pliku
    p = os.path.join("uploads", file.filename)
    with open(p, "wb") as f:
        f.write(await file.read())

    # Szyfrujemy
    enc_path, key_path = encrypt_file(p, delete_orig)

    # Renderujemy wynik, pamiętając o przekazaniu `request`
    return templates.TemplateResponse(
        "encrypt_result.html",
        {
            "request": request,
            "enc_path": enc_path,
            "key_path": key_path
        }
    )

@app.get("/ocr", response_class=HTMLResponse)
def ocr_form(request: Request):
    # zwracamy szablon i podajemy obiekt request
    return templates.TemplateResponse("ocr.html", {"request": request})
@app.post("/ocr", response_class=HTMLResponse)
async def ocr_post(request: Request, file: UploadFile = File(...)):
    # zapis pliku
    p = os.path.join("uploads", file.filename)
    with open(p, "wb") as f:
        f.write(await file.read())
    # wykonaj OCR
    txt = ocr_image(p)
    # zwróć wynik w szablonie
    return templates.TemplateResponse("ocr_result.html", {"request": request, "text": txt})

@app.get("/anonymize", response_class=HTMLResponse)
def anon_form(request: Request): return templates.TemplateResponse("anonymize.html",{"request":request})
@app.post("/anonymize", response_class=HTMLResponse)
async def anon_post(request, file:UploadFile=File(...)):
    p="uploads/"+file.filename
    open(p,"wb").write(await file.read())
    ap=anonymize_image(p)
    return templates.TemplateResponse("anonymize_result.html",{"request":request,"anon_path":ap})
