from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import SessionLocal
from app.models import Ayuntamiento

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def process_login(request: Request, codigo: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    ayto = db.query(Ayuntamiento).filter_by(codigo=codigo).first()

    if ayto and ayto.password == password:
        # Guardamos el ID del ayuntamiento en sesión (cookies)
        response = RedirectResponse(url="/data-input", status_code=303)
        response.set_cookie(key="ayto_id", value=str(ayto.id))
        return response
    else:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Código o contraseña incorrectos"}
        )

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("ayto_id")
    return response
