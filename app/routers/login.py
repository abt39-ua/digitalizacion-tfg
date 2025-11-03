from fastapi import APIRouter, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Ayuntamiento

router = APIRouter()

@router.post("/login")
def login(
    codigo: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    ayto = db.query(Ayuntamiento).filter_by(codigo=codigo).first()
    if not ayto or ayto.password != password:
        return {"error": "Código o contraseña incorrectos"}

    # Aquí guardas la sesión o generas cookie
    response = RedirectResponse(url="/data_input", status_code=303)
    return response
