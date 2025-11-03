from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Definición de la URL de la base de datos
# He renombrado la variable a DATABASE_URL para que funcione con sync_excel_to_db.py
DATABASE_URL = "sqlite:///./data/ayuntamientos.db"

# 2. Creación del motor
# connect_args={"check_same_thread": False} es necesario solo para SQLite
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Declarar base
Base = declarative_base()

# Dependencia para obtener una sesión en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
