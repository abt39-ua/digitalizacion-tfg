# Importaciones necesarias
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px # Importamos Plotly para gráficos interactivos

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
# SELECCIÓN Y FORMULARIO (Mantenido para la demo)
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
        
        # ----------------------------------------------------------------------
        # ANÁLISIS GRÁFICO (NUEVA SECCIÓN)
        # ----------------------------------------------------------------------
        
        st.markdown("---")
        st.header("3. Análisis Gráfico de Respuestas")

        col1, col2 = st.columns(2)
        
        # Nombres de columna que usaremos (aseguramos mayúsculas y eliminamos espacios extra)
        P1_COL = "P1. FORMACIÓN"
        P8_COL = "P8. FIBRA OPTICA" # <--- CORRECCIÓN AQUI
        P3_COL = "P3. Nº FUNCIONARIOS"

        # Gráfico 1: P1. Formación (Gráfico de Barras)
        if P1_COL in data.columns:
            with col1:
                st.subheader(f"{P1_COL}: ¿Existe Plan de Formación?")
                # Contar ocurrencias, renombrar el índice para la leyenda y resetear el índice para Plotly
                df_counts = data[P1_COL].value_counts().reset_index()
                df_counts.columns = ['Respuesta', 'Conteo']
                
                fig_bar = px.bar(
                    df_counts,
                    x='Respuesta',
                    y='Conteo',
                    title=f'Distribución de Respuestas {P1_COL}',
                    color='Respuesta',
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            col1.warning(f"Columna '{P1_COL}' no encontrada para el análisis. Columnas disponibles: {', '.join(data.columns)}")

        # Gráfico 2: P8. Fibra Optica (Gráfico Circular/Pie Chart)
        if P8_COL in data.columns:
            with col2:
                st.subheader(f"{P8_COL}: ¿Dispone de Fibra Óptica?")
                # Contar ocurrencias (ignorando NaN y convirtiendo a string)
                # NOTA: Usamos P8_COL
                df_pie = data[P8_COL].astype(str).str.upper().value_counts().reset_index()
                df_pie.columns = ['Respuesta', 'Conteo']
                
                fig_pie = px.pie(
                    df_pie,
                    values='Conteo',
                    names='Respuesta',
                    title=f'Proporción de {P8_COL}',
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            col2.warning(f"Columna '{P8_COL}' no encontrada para el análisis. Columnas disponibles: {', '.join(data.columns)}")


        # Gráfico 3: P3. Nº funcionarios (Histograma para datos numéricos)
        # Intentamos convertir la columna a numérica y solo si tiene éxito, dibujamos
        if P3_COL in data.columns:
            st.markdown("---")
            st.subheader(f"Distribución de la Variable {P3_COL} (Nº de Funcionarios)")
            
            # Limpieza y conversión a numérico
            data['P3_NUM'] = pd.to_numeric(data[P3_COL], errors='coerce')
            
            # Filtrar valores no válidos (NaN) después de la conversión
            df_hist = data.dropna(subset=['P3_NUM'])
            
            if not df_hist.empty:
                fig_hist = px.histogram(
                    df_hist,
                    x='P3_NUM',
                    nbins=10, # Número de contenedores/barras
                    title='Conteo de Ayuntamientos por Rango de Funcionarios'
                )
                fig_hist.update_layout(xaxis_title="Número de Funcionarios")
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.warning(f"No hay suficientes datos numéricos válidos en '{P3_COL}' para generar el histograma.")
        else:
            st.warning(f"Columna '{P3_COL}' no encontrada para el análisis. Columnas disponibles: {', '.join(data.columns)}")
