import os
import pandas as pd
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Importamos la configuración actualizada
from app.database import Base, DATABASE_URL 
from app.models import Ayuntamiento, DatosAyuntamiento

# -----------------------------------------------------
# CONFIGURACIÓN
# -----------------------------------------------------
EXCEL_PATH = "data/ENCUESTAS_datosIA.xlsx"
MUNICIPIO_COL = "AYUNTAMIENTO" # ¡Columna correcta según tu Excel!

# -----------------------------------------------------
# 1️⃣ Elimina la base de datos anterior si existe
# -----------------------------------------------------
if DATABASE_URL.startswith("sqlite:///"):
    # Extraemos la ruta del archivo SQLite
    db_path = DATABASE_URL.replace("sqlite:///", "")
    # Comprobamos y creamos el directorio 'data' si no existe
    data_dir = os.path.dirname(db_path)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"📁 Creado directorio: {data_dir}")

    if os.path.exists(db_path):
        print(f"🧹 Borrando base de datos anterior: {db_path}")
        os.remove(db_path)
    else:
        print("ℹ️ No se encontró una base de datos previa, se creará una nueva.")
else:
    print("⚠️ Advertencia: no se puede borrar la base de datos (no es SQLite).")

# -----------------------------------------------------
# 2️⃣ Crear la base de datos y las tablas
# -----------------------------------------------------
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# -----------------------------------------------------
# 3️⃣ Cargar el Excel
# -----------------------------------------------------
print(f"📖 Leyendo Excel: {EXCEL_PATH}")
# Leer el Excel y limpiar los nombres de las columnas de espacios
df = pd.read_excel(EXCEL_PATH)
df.columns = [str(c).strip() for c in df.columns] 
print(f"✅ {len(df)} filas cargadas desde el Excel.")

# -----------------------------------------------------
# 4️⃣ Crear los registros
# -----------------------------------------------------
for idx, row in df.iterrows():
    # USAMOS LA COLUMNA CORRECTA: 'AYUNTAMIENTO'
    nombre = str(row.get(MUNICIPIO_COL) or "").strip()
    
    if not nombre or nombre.lower() in ["nan", "sin nombre", ""]:
        print(f"⚠️ Fila {idx}: sin nombre de municipio (valor: '{row.get(MUNICIPIO_COL)}'), saltando.")
        continue
    
    # Intenta obtener el nivel de digitalización, por si es la columna que usas en el Excel
    nivel_digitalizacion_excel = row.get("Nivel de digitalización (%)") 
    
    # Convertir a float de forma segura
    try:
        nivel = float(nivel_digitalizacion_excel) if nivel_digitalizacion_excel else 0.0
    except ValueError:
        nivel = 0.0

    # Crea el ayuntamiento principal
    ayto = Ayuntamiento(
        # Usamos el nombre para el código también (podrías querer un slug aquí)
        codigo=nombre.lower().replace(" ", "_"), 
        nombre=nombre,
        password="1234",  # Contraseña temporal
        # Guardamos el nivel en la tabla principal
        nivel_digitalizacion=nivel, 
    )
    db.add(ayto)
    db.flush()  # Para obtener su ID

    # Crea el registro asociado con todos los datos del Excel
    # Pasamos solo las columnas no NaN a JSON para tener un JSON más limpio
    data_for_json = row.dropna().to_dict()
    data_json = json.dumps(data_for_json, ensure_ascii=False)
    
    datos = DatosAyuntamiento(
        ayto_id=ayto.id,
        nivel_digitalizacion=nivel,
        data_json=data_json,
    )
    db.add(datos)

    print(f"✅ Añadido: {nombre} (ID: {ayto.id})")

# -----------------------------------------------------
# 5️⃣ Guardar y cerrar
# -----------------------------------------------------
db.commit()
db.close()
print("\n🎉 Sincronización completada con éxito. Base de datos regenerada.")
