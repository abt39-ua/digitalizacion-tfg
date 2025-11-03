from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import pandas as pd

from app.database import get_db
from app.models import Ayuntamiento

app = FastAPI()

# Configuración de plantillas y estáticos
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ------------------------------------------------------
# Página principal
# ------------------------------------------------------
@app.get("/")
def index(request: Request):
    return RedirectResponse(url="/login")


# ------------------------------------------------------
# Login
# ------------------------------------------------------
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "msg": None})


@app.post("/login")
def login(request: Request, codigo: str = Form(...), db: Session = Depends(get_db)):
    ayto = db.query(Ayuntamiento).filter_by(codigo=codigo).first()
    if not ayto:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "msg": "Código incorrecto. Inténtelo de nuevo."}
        )

    response = RedirectResponse(url="/data_input", status_code=303)
    response.set_cookie(key="codigo", value=codigo)
    return response


# ------------------------------------------------------
# Cerrar sesión
# ------------------------------------------------------
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("codigo")
    return response


# ------------------------------------------------------
# Página principal de datos (Data Input)
# ------------------------------------------------------
@app.get("/data_input")
def data_input(request: Request, db: Session = Depends(get_db)):
    codigo = request.cookies.get("codigo")
    if not codigo:
        return RedirectResponse("/login")

    ayto = db.query(Ayuntamiento).filter_by(codigo=codigo).first()
    if not ayto:
        return RedirectResponse("/login")

    # Nivel de digitalización (si existe en la BD o en el Excel)
    nivel_digitalizacion = getattr(ayto, "nivel_digitalizacion", None)
    if not nivel_digitalizacion:
        nivel_digitalizacion = "No definido"

    # Leer columnas del Excel
    try:
        df = pd.read_excel("data/ENCUESTAS_datosIA.xlsx")
        p_columns = list(df.columns)
    except Exception as e:
        p_columns = []
        print(f"⚠️ Error al leer el Excel: {e}")

    return templates.TemplateResponse(
        "data_input.html",
        {
            "request": request,
            "ayto": ayto,
            "nivel_digitalizacion": nivel_digitalizacion,
            "p_columns": p_columns,
            "msg": None
        }
    )


# ------------------------------------------------------
# Procesar formulario (guardar datos)
# ------------------------------------------------------
@app.post("/data_input")
def update_data(
    request: Request,
    col1: str = Form(None),
    val1: str = Form(None),
    col2: str = Form(None),
    val2: str = Form(None),
    col3: str = Form(None),
    val3: str = Form(None),
    db: Session = Depends(get_db)
):
    codigo = request.cookies.get("codigo")
    if not codigo:
        return RedirectResponse("/login")

    ayto = db.query(Ayuntamiento).filter_by(codigo=codigo).first()
    if not ayto:
        return RedirectResponse("/login")

    # Leer Excel y actualizar (solo en memoria, de momento)
    df = pd.read_excel("data/ENCUESTAS_datosIA.xlsx")

    if codigo in df["Código"].astype(str).values:
        row_index = df[df["Código"].astype(str) == codigo].index[0]
        for col, val in [(col1, val1), (col2, val2), (col3, val3)]:
            if col and col in df.columns:
                df.at[row_index, col] = val

        df.to_excel("data/ENCUESTAS_datosIA.xlsx", index=False)
        msg = "Datos actualizados correctamente."
    else:
        msg = "No se encontró el municipio en el Excel."

    nivel_digitalizacion = getattr(ayto, "nivel_digitalizacion", None) or "No definido"
    p_columns = list(df.columns)

    return templates.TemplateResponse(
        "data_input.html",
        {
            "request": request,
            "ayto": ayto,
            "nivel_digitalizacion": nivel_digitalizacion,
            "p_columns": p_columns,
            "msg": msg
        }
    )
