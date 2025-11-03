from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import SessionLocal
from app.models import Ayuntamiento, DatosAyuntamiento
import pandas as pd

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/data-input", response_class=HTMLResponse)
def show_dashboard(request: Request):
    ayto_id = request.cookies.get("ayto_id")
    if not ayto_id:
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    ayto = db.query(Ayuntamiento).filter_by(id=ayto_id).first()
    datos = db.query(DatosAyuntamiento).filter_by(ayto_id=ayto_id).first()

    return templates.TemplateResponse("data_input.html", {
        "request": request,
        "ayto": ayto,
        "datos": datos
    })


@router.post("/data-input")
def update_data(
    request: Request,
    p1: str = Form(...),
    p2: str = Form(...),
    p3: str = Form(...),
    notas: str = Form(...),
):
    ayto_id = request.cookies.get("ayto_id")
    if not ayto_id:
        return RedirectResponse(url="/login", status_code=303)

    db = SessionLocal()
    datos = db.query(DatosAyuntamiento).filter_by(ayto_id=ayto_id).first()
    ayto = db.query(Ayuntamiento).filter_by(id=ayto_id).first()

    datos.p1 = p1
    datos.p2 = p2
    datos.p3 = p3
    datos.notas = notas
    db.commit()

    # Sincronizar también con el Excel
    df = pd.read_excel("data/ENCUESTAS_datosIA.xlsx")
    mask = df["Municipio"].str.lower() == ayto.nombre.lower()
    df.loc[mask, ["P1. Formación", "P2. Infraestructura", "P3. Servicios"]] = [p1, p2, p3]
    df.to_excel("data/ENCUESTAS_datosIA.xlsx", index=False)

    db.close()
    return RedirectResponse(url="/data-input", status_code=303)
