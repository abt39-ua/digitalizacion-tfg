from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Ayuntamiento, DatosAyuntamiento

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Opciones de ejemplo (puedes adaptarlas a tu Excel)
OPCIONES_P1 = ["Básico", "Intermedio", "Avanzado"]
OPCIONES_P2 = ["Limitada", "Adecuada", "Excelente"]
OPCIONES_P3 = ["Escasos", "Moderados", "Amplios"]


@router.get("/data_input")
def data_input(request: Request, db: Session = Depends(get_db)):
    ayto_id = request.session.get("ayto_id")
    if not ayto_id:
        return RedirectResponse(url="/login", status_code=303)

    ayto = db.query(Ayuntamiento).filter(Ayuntamiento.id == ayto_id).first()
    if not ayto:
        return RedirectResponse(url="/login", status_code=303)

    datos = db.query(DatosAyuntamiento).filter(DatosAyuntamiento.ayto_id == ayto_id).first()
    if not datos:
        datos = DatosAyuntamiento(ayto_id=ayto_id)
        db.add(datos)
        db.commit()
        db.refresh(datos)

    return templates.TemplateResponse("data_input.html", {
        "request": request,
        "nivel_digitalizacion": datos.nivel_digitalizacion or "Sin definir",
        "opciones_p1": OPCIONES_P1,
        "opciones_p2": OPCIONES_P2,
        "opciones_p3": OPCIONES_P3,
        "datos": datos
    })


@router.post("/update_data")
def update_data(
    request: Request,
    p1: str = Form(...),
    p1_notas: str = Form(""),
    p2: str = Form(...),
    p2_notas: str = Form(""),
    p3: str = Form(...),
    p3_notas: str = Form(""),
    db: Session = Depends(get_db)
):
    ayto_id = request.session.get("ayto_id")
    if not ayto_id:
        return RedirectResponse(url="/login", status_code=303)

    datos = db.query(DatosAyuntamiento).filter(DatosAyuntamiento.ayto_id == ayto_id).first()
    if datos:
        datos.p1 = p1
        datos.p1_notas = p1_notas
        datos.p2 = p2
        datos.p2_notas = p2_notas
        datos.p3 = p3
        datos.p3_notas = p3_notas
        db.commit()

    return RedirectResponse(url="/data_input", status_code=303)
