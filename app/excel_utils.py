import pandas as pd
import os

EXCEL_PATH = "data/ENCUESTAS_datosIA.xlsx"

def load_excel_columns():
    """
    Carga los nombres de las columnas del Excel una sola vez al inicio de la aplicación.
    Filtra las columnas para incluir solo las que son preguntas o datos clave (empezando por P).
    """
    # 1. Verificar que el archivo existe
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Error: No se encontró el archivo Excel en {EXCEL_PATH}. Comprueba la ruta.")
        return []
        
    try:
        # 2. Leer solo la primera fila (encabezados) para mayor velocidad
        # Se asume que el archivo es grande y leerlo completo ralentiza el inicio.
        df = pd.read_excel(EXCEL_PATH, engine="openpyxl", nrows=1) 
        
        # 3. Limpiar los nombres de las columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # 4. Definir columnas a excluir (campos de identificación)
        excluded_cols = [
            "AYUNTAMIENTO", 
            "Municipio", # Si usas este en el Excel
            "Código", # Si tienes una columna de código de ayuntamiento
            "Nivel de digitalización (%)" # Se puede mostrar, pero quizás no actualizar directamente
        ]
        
        # 5. Filtrar las columnas editables:
        # - Deben empezar por 'P' o ser una columna que se quiera actualizar.
        # - No deben estar en la lista de excluidas.
        p_columns = [
            c for c in df.columns 
            if c.strip().upper().startswith("P") and c not in excluded_cols
        ]
        
        # Añadir las columnas que, a pesar de no empezar por P, quieres que sean editables.
        # Por ahora, solo usamos las 'P's para tener una lista limpia de preguntas.
        
        print(f"✅ Columnas editables cargadas: {p_columns[:5]}... ({len(p_columns)} en total)")
        return p_columns
        
    except Exception as e:
        print(f"❌ Error crítico al cargar columnas del Excel: {e}")
        return []

# La lista de columnas se carga una sola vez al importar este módulo
COLUMNAS_P = load_excel_columns()

# Si quieres que todas las columnas (excepto el municipio) sean editables, 
# la lógica de filtrado deberá ser más compleja.
# Por ahora, nos centramos en las preguntas (P).
