import streamlit as st
import pandas as pd
import json
import os

# ----------------------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------------------
EXCEL_PATH = "data/ENCUESTAS_datosIA.xlsx"
# Usamos un nombre normalizado en minúsculas para la columna de Ayuntamientos
MUNICIPIO_COL_NORM = "ayuntamiento"

# ----------------------------------------------------------------------
# FUNCIONES DE CARGA Y NORMALIZACIÓN DE DATOS
# ----------------------------------------------------------------------

@st.cache_data
def load_data():
    """Carga el Excel y normaliza los nombres de las columnas para evitar errores."""
    try:
        df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    except FileNotFoundError:
        st.error(f"Error: No se encuentra el archivo Excel en la ruta: {EXCEL_PATH}")
        return pd.DataFrame()

    # 1. Normalizar nombres de columnas: strip y lower()
    df.columns = [str(c).strip().lower() for c in df.columns]

    # 2. Verificar si la columna normalizada existe
    if MUNICIPIO_COL_NORM not in df.columns:
        st.error(f"Error: La columna '{MUNICIPIO_COL_NORM.upper()}' no se encuentra en el Excel. Columnas encontradas: {list(df.columns)}")
        return pd.DataFrame()

    # Filtra y prepara las columnas P* (ahora también en minúsculas)
    p_columns_norm = [c for c in df.columns if c.startswith("p")]

    return df, p_columns_norm

# ----------------------------------------------------------------------
# PÁGINA PRINCIPAL DE STREAMLIT
# ----------------------------------------------------------------------

st.set_page_config(page_title="Gestión de Datos de Digitalización", layout="wide")
st.title("Encuesta de Digitalización Municipal")
st.markdown("---")

# Cargar los datos y las columnas P*
data = load_data()
if data.empty:
    st.stop()

df_municipios, p_columns = data

# ----------------------------------------------------------------------
# LÓGICA DE LOGIN/SELECCIÓN DE AYUNTAMIENTO (SIMULADA)
# ----------------------------------------------------------------------

# 1. Obtener la lista de nombres de ayuntamientos normalizados para el desplegable
ayuntamiento_names = df_municipios[MUNICIPIO_COL_NORM].unique()

# 2. Desplegable de selección (simula el login)
selected_ayto_norm = st.selectbox(
    "Seleccione su Ayuntamiento (Simulación de Login)",
    options=["--- Seleccione ---"] + list(ayuntamiento_names),
    index=0
)

if selected_ayto_norm == "--- Seleccione ---":
    st.info("Por favor, seleccione un Ayuntamiento para continuar.")
    st.stop()

# Obtener la fila de datos para el Ayuntamiento seleccionado
current_data_row = df_municipios[df_municipios[MUNICIPIO_COL_NORM] == selected_ayto_norm].iloc[0]

# Extraer el nombre original (para mostrar en el título)
# Buscamos la columna original que mejor coincida para mostrarla
ayto_name_display = current_data_row[MUNICIPIO_COL_NORM].title()
st.header(f"Ayuntamiento: {ayto_name_display}")
st.subheader("Entrada y Actualización de Datos")


# ----------------------------------------------------------------------
# FORMULARIO DE ENTRADA DE DATOS
# ----------------------------------------------------------------------

with st.form("data_input_form"):
    st.markdown("### Actualizar hasta tres variables (P*)")

    cols = st.columns(3)
    form_data = {}

    # Generar 3 pares de campos de selección y valor
    for i in range(1, 4):
        with cols[i-1]:
            # Campo para seleccionar la columna P*
            col_key = f"col{i}"
            val_key = f"val{i}"
            
            # El valor actual se obtiene de la fila del DataFrame
            current_val = current_data_row.get(p_columns[0]) if p_columns else ""

            selected_col = st.selectbox(
                f"Columna {i} (P*)",
                options=[""] + p_columns,
                key=f"select_{i}"
            )
            
            if selected_col:
                # Si hay una columna seleccionada, obtenemos el valor actual
                current_val_for_input = current_data_row.get(selected_col, "")
                
                # Campo para introducir el nuevo valor
                new_val = st.text_input(
                    f"Valor actual de {selected_col}: `{current_val_for_input}`",
                    value=str(current_val_for_input),
                    key=f"input_{i}"
                )
                
                # Almacenar en el diccionario de datos del formulario
                form_data[selected_col] = new_val

    submitted = st.form_submit_button("Guardar Cambios")

# ----------------------------------------------------------------------
# LÓGICA DE PROCESAMIENTO
# ----------------------------------------------------------------------

if submitted:
    # 1. Leer el DataFrame de nuevo para asegurarnos de que estamos actualizando la versión más reciente
    # Nota: Si se usan múltiples usuarios en el futuro, esto debería ser una base de datos real.
    # Para la demo de Streamlit, reescribir el Excel es la forma más simple.
    df_current, _ = load_data()
    
    # 2. Encontrar el índice de la fila a actualizar (usando el nombre normalizado)
    row_index = df_current[df_current[MUNICIPIO_COL_NORM] == selected_ayto_norm].index[0]

    # 3. Aplicar las actualizaciones
    updated_count = 0
    for col, val in form_data.items():
        if col and val:
            # Actualizar el valor en el DataFrame
            df_municipios.loc[row_index, col] = val
            updated_count += 1
    
    # 4. Guardar los cambios de nuevo en el archivo Excel (DEMO ÚNICAMENTE)
    try:
        df_municipios.to_excel(EXCEL_PATH, index=False, header=True)
        # Forzar recarga de cache para que se muestre el nuevo valor
        st.cache_data.clear()
        
        st.success(f"✅ ¡Datos guardados y actualizados para {ayto_name_display}! ({updated_count} campos actualizados)")
        st.experimental_rerun()
        
    except Exception as e:
        st.error(f"Error al guardar los datos en el Excel: {e}")

# ----------------------------------------------------------------------
# MOSTRAR EL NIVEL DE DIGITALIZACIÓN (SIMULADO)
# ----------------------------------------------------------------------

# Muestra el nivel de digitalización que se encuentra en la columna "nivel de digitalización (%)"
# Nota: La lógica de cálculo debería estar fuera de la app de entrada de datos
try:
    nivel_digitalizacion_key = "nivel de digitalización (%)"
    # Asegúrate de que la columna exista antes de intentar acceder a ella
    if nivel_digitalizacion_key in current_data_row.index:
        nivel = current_data_row[nivel_digitalizacion_key]
        if pd.isna(nivel):
             st.info("Nivel de Digitalización: Sin datos.")
        else:
             st.metric(
                label="Nivel de Digitalización Actual (Simulado)",
                value=f"{nivel:.2f}%",
                help="Este valor es el que se encuentra actualmente en la hoja de cálculo."
            )
    else:
        st.warning(f"La columna '{nivel_digitalizacion_key.upper()}' no se encontró para mostrar el indicador.")

except Exception as e:
    st.error(f"Error al mostrar el nivel de digitalización: {e}")
    st.error("Revisa si el nombre de la columna 'Nivel de digitalización (%)' es el correcto en tu Excel.")
