import pandas as pd
from app.database import SessionLocal, engine, Base
from app.models import Ayuntamiento

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

# Cargar el Excel
df = pd.read_excel("data/ENCUESTAS_datosIA.xlsx", engine="openpyxl")

# Crear la sesión
db = SessionLocal()

# Vaciar la tabla antes de cargar (opcional)
db.query(Ayuntamiento).delete()

# Insertar ayuntamientos con código
for i, row in enumerate(df.itertuples(), start=1):
    codigo = f"{i:03d}"  # genera '001', '002', ...
    nombre = getattr(row, "Ayuntamiento")  # asegúrate de que esta columna exista en tu Excel
    password = "1234"  # Contraseña provisional para todos

    ayto = Ayuntamiento(codigo=codigo, nombre=nombre, password=password)
    db.add(ayto)

db.commit()
db.close()

print("✅ Ayuntamientos importados correctamente.")
