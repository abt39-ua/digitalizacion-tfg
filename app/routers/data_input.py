# app/routers/data_input.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Ayuntamiento, DatosAyuntamiento
from app.excel_utils import COLUMNAS_P # 👈 1. Importamos la lista de columnas
import pandas as pd
import json

router = APIRouter()
# Asumo que tus templates están en 'app/templates' como indicaste
templates = Jinja2Templates(directory="app/templates")

# Ya no se necesita esta constante, la ruta está en excel_utils
# EXCEL_PATH = "data/ENCUESTAS_datosIA.xlsx" 
MUNICIPIO_COL = "AYUNTAMIENTO"  # ajusta si tu columna tiene otro nombre exacto

def get_current_ayto(request: Request, db: Session):
    ayto_id = request.cookies.get("ayto_id")
    if not ayto_id:
         return None
    return db.query(Ayuntamiento).filter(Ayuntamiento.id == int(ayto_id)).first()

@router.get("/data-input", response_class=HTMLResponse)
def get_data_input(request: Request):
    db = SessionLocal()
    ayto = get_current_ayto(request, db)
    if not ayto:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

  # obtener o crear registro DatosAyuntamiento
    datos = db.query(DatosAyuntamiento).filter_by(ayto_id=ayto.id).first()
    if not datos:
        datos = DatosAyuntamiento(ayto_id=ayto.id, data_json="{}")
        db.add(datos)
        db.commit()
        db.refresh(datos)

  # leer Excel para obtener lista de columnas P* - ELIMINADO
  # Ahora usamos la lista cargada al inicio
    p_columns = COLUMNAS_P

  # cargar JSON actual (si lo hay)
    current = {}
    if datos.data_json:
        try:
            # El JSON que guardamos en la BBDD es la fuente de la verdad
            current = json.loads(datos.data_json)
        except Exception:
            current = {}

    contexto = {
        "request": request,
        "ayto": ayto,
        # Asegúrate de que esta variable sea la que usas en el template para el Campo 1
        "col1_name": request.query_params.get("col1", ""), 
        "nivel_digitalizacion": datos.nivel_digitalizacion if datos.nivel_digitalizacion is not None else "Sin definir",
        "p_columns": p_columns, # 👈 Usamos la lista cargada
        "current": current,
        "msg": request.query_params.get("msg") # Leer mensaje si viene de un redirect
    }
    db.close()
    return templates.TemplateResponse("data_input.html", contexto)


@router.post("/data-input")
def post_data_input(
    request: Request,
    col1: str = Form(...),
    val1: str = Form(""),
    col2: str = Form(None),
    val2: str = Form(""),
    col3: str = Form(None),
    val3: str = Form(""),
):
    db = SessionLocal()
    ayto = get_current_ayto(request, db)
    if not ayto:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

    # obtener o crear registro datos
    datos = db.query(DatosAyuntamiento).filter_by(ayto_id=ayto.id).first()
    if not datos:
        datos = DatosAyuntamiento(ayto_id=ayto.id, data_json="{}")
        db.add(datos)
        db.commit()
        db.refresh(datos)

    # actualizar JSON local
    current = {}
    try:
        current = json.loads(datos.data_json) if datos.data_json else {}
    except Exception:
        current = {}

    # 1. Aplicar los nuevos valores
    if col1:
        current[col1] = val1
    if col2:
        current[col2] = val2
    if col3:
        current[col3] = val3

    # 2. Guardar JSON en BD
    datos.data_json = json.dumps(current, ensure_ascii=False)
    
    # 3. Actualizar nivel_digitalizacion si se ha modificado la columna "Nivel de digitalización (%)"
    # Se usa 'Nivel de digitalización (%)' para que sea más fácil de identificar.
    NIVEL_COL = "Nivel de digitalización (%)"
    if NIVEL_COL in current:
        try:
            datos.nivel_digitalizacion = float(current.get(NIVEL_COL) or datos.nivel_digitalizacion)
        except Exception:
        # Si falla la conversión a float, no hacemos nada y dejamos el valor anterior
            pass
        
    db.commit()
  
  # ----------------------------------------------------
  # 4. 🔥 ELIMINAR EL CÓDIGO INSEGURO DE REESCRITURA DEL EXCEL
  #    Tu base de datos (SQLite) es ahora la única fuente de la verdad.
  # ----------------------------------------------------

    db.close()

    # 5. Redirigir para evitar que el usuario vuelva a enviar el formulario.
    #    Pasamos un mensaje de éxito por URL.
    return RedirectResponse(url="/data-input?msg=Datos guardados correctamente", status_code=303)
