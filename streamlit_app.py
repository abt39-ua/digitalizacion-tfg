# Importaciones necesarias
import streamlit as st
import pandas as pd
import numpy as np

# ----------------------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------------------

# Ruta al archivo Excel (debe estar en la carpeta 'data' en el repo)
EXCEL_PATH = "data/ENCUESTAS_datosIA.xlsx"
# Nombre de la columna que contiene los nombres de los Ayuntamientos
MUNICIPIO_COL = "AYUNTAMIENTO"

# ----------------------------------------------------------------------
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ----------------------------------------------------------------------

@st.cache_data
def load_data():
    """Carga el Excel y extrae el DataFrame y las columnas de encuesta (P)."""
    try:
        # 1. Cargar el Excel
        df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
        
        # 2. Normalizar nombres de columnas a mayúsculas para evitar errores (AYUNTAMIENTO vs Ayuntamiento)
        df.columns = df.columns.str.upper().str.strip()

        # 3. Verificar si la columna principal existe después de la normalización
        if MUNICIPIO_COL not in df.columns:
            st.error(f"¡Error Crítico! No se encontró la columna '{MUNICIPIO_COL}' en el Excel.")
            st.warning("Columnas encontradas (normalizadas):")
            st.code(list(df.columns))
            # Devolvemos un DataFrame vacío y una lista vacía para manejar el error
            return pd.DataFrame(), [] 

        # 4. Obtener las columnas de encuesta
        p_columns_raw = [col for col in df.columns if col.startswith("P") and not col.startswith("PONDER")]
        
        # 5. Limpieza y filtrado de columnas P
        # Filtramos columnas que parecen ser solo contadores repetidos
        p_columns_clean = [
            col for col in p_columns_raw
            if not col.strip().upper().endswith("Nº")
            and not col.strip().upper() == "P6. FORMACIÓN CONJUNTO" # Si hay 7 P6 repetidas, ignoramos la base
            and not col.strip().upper() == "P7. FORMACIÓN A PRECISAR" # Si hay 7 P7 repetidas, ignoramos la base
        ]

        # Convertir a lista y devolver
        return df, p_columns_clean

    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo Excel en la ruta: {EXCEL_PATH}. Asegúrate de subirlo.")
        return pd.DataFrame(), []
    except Exception as e:
        st.error(f"Error desconocido al cargar los datos: {e}")
        return pd.DataFrame(), []

# ----------------------------------------------------------------------
# INTERFAZ DE STREAMLIT
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="Encuesta de Digitalización Municipal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Encuesta de Digitalización Municipal")

# Cargar datos (siempre devuelve una tupla)
data, p_columns = load_data()

# Comprobar si la carga fue exitosa
if data.empty and not p_columns:
    st.warning("No se pudieron cargar los datos o la columna de Ayuntamientos no es correcta. Revisa el log de Streamlit.")
    st.stop() # Detiene la ejecución si hay error en la carga

# Obtener la lista de nombres de municipios
municipios = data[MUNICIPIO_COL].dropna().unique().tolist()

# ----------------------------------------------------------------------
# SELECCIÓN Y FORMULARIO
# ----------------------------------------------------------------------

# 1. Selector de Municipio
st.header("1. Selecciona tu Ayuntamiento")
municipio_seleccionado = st.selectbox(
    "Ayuntamiento:",
    options=['--- Seleccionar ---'] + municipios,
    index=0
)

if municipio_seleccionado != '--- Seleccionar ---':
    st.subheader(f"Datos actuales de: {municipio_seleccionado}")

    # Obtener la fila del municipio seleccionado
    # Usamos .iloc[0] porque sabemos que el municipio es único
    fila_actual = data[data[MUNICIPIO_COL] == municipio_seleccionado].iloc[0]

    # 2. Formulario de Actualización
    st.header("2. Actualizar una Respuesta de Encuesta (Solo para Demo)")
    st.info("Nota: En esta demo pública, la actualización solo se muestra en pantalla y no se guarda en el Excel.")

    with st.form("actualizar_datos"):
        # Selector de la columna (pregunta) a actualizar
        columna_a_actualizar = st.selectbox(
            "Selecciona la Pregunta (Columna) a actualizar:",
            options=['--- Seleccionar ---'] + p_columns
        )

        valor_actual = "No disponible / Sin respuesta"
        if columna_a_actualizar != '--- Seleccionar ---':
            # Intentar obtener el valor actual para mostrarlo
            try:
                valor_actual = fila_actual[columna_a_actualizar]
                if pd.isna(valor_actual):
                    valor_actual = "Sin respuesta previa"
                else:
                    valor_actual = str(valor_actual)
            except KeyError:
                valor_actual = "Columna no encontrada"

            st.markdown(f"**Valor Actual:** `{valor_actual}`")
        
        # Campo de entrada para el nuevo valor
        nuevo_valor = st.text_area(
            "Introduce el Nuevo Valor/Respuesta:",
            value=""
        )

        submitted = st.form_submit_button("Simular Actualización y Mostrar")

    if submitted and municipio_seleccionado != '--- Seleccionar ---' and columna_a_actualizar != '--- Seleccionar ---':
        
        # Simulación de la actualización
        st.success(f"¡Simulación Exitosa! El dato ha sido 'actualizado'.")

        # Mostrar la tabla de resumen
        st.markdown(f"### Resultado Simulado para {municipio_seleccionado}")
        
        # Crear un DataFrame para mostrar solo la fila actualizada
        df_display = pd.DataFrame(fila_actual).T
        
        # Aplicar el nuevo valor
        df_display.at[df_display.index[0], columna_a_actualizar] = nuevo_valor
        
        # Estilizar el valor que acaba de ser modificado
        def highlight_change(val, column):
            """Resalta la celda modificada."""
            is_modified = val == nuevo_valor and column == columna_a_actualizar
            return f'background-color: #ffd700; color: black; font-weight: bold' if is_modified else ''

        st.dataframe(
            df_display.style.apply(
                lambda x: [highlight_change(v, x.name) for v in x], axis=1
            ),
            use_container_width=True
        )
        
        st.caption("Recuerda: Esta es una simulación. El Excel original no se ha modificado en el servidor.")

# ----------------------------------------------------------------------
# DASHBOARD DE DATOS GENERALES
# ----------------------------------------------------------------------
st.sidebar.header("Datos Generales (Dashboard)")

if not data.empty:
    
    # 1. Total de Ayuntamientos
    st.sidebar.metric("Ayuntamientos en la Encuesta", len(municipios))

    # 2. Resumen de columnas (solo las P)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Preguntas Disponibles")
    st.sidebar.text(f"Se encontraron {len(p_columns)} preguntas para el formulario.")

    # 3. Visualización simple de datos
    st.header("Dashboard de Respuestas de Encuesta")

    # Mostrar las primeras filas del DataFrame (sin las columnas irrelevantes)
    if municipios:
        st.dataframe(
            data[[MUNICIPIO_COL] + p_columns].head(10).style.set_properties(**{'font-size': '8pt'}),
            use_container_width=True
        )
        st.caption("Primeras 10 filas de datos de las columnas 'P'.")
