# pages/1_🔎_Exploracion_General.py

import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import StringIO
from analisis_redes import STOP_WORDS_ES 



def generar_nube_palabras(df):

    texto_completo = ' '.join([' '.join(map(str, keywords)) for keywords in df['palabras_clave'].dropna()])

    palabras_filtradas = [word for word in texto_completo.lower().split() if word not in STOP_WORDS_ES and len(word) > 2]
    texto_filtrado = ' '.join(palabras_filtradas)
    
    if not texto_filtrado.strip():
        st.warning("No hay suficientes palabras clave relevantes para generar una nube de palabras.")
        return
    

    wordcloud = WordCloud(width=800, height=400, background_color='white', collocations=False).generate(texto_filtrado)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)

    

from procesamiento import procesar_archivos_pdf
from analisis_redes import normalizar_nombre

# --- Funciones Auxiliares ---
def convertir_columnas_a_listas(df):
    columnas_lista = ['autores', 'afiliaciones', 'palabras_clave', 'referencias']
    for col in columnas_lista:
        if col in df.columns and pd.notna(df[col]).any():
            df[col] = df[col].apply(lambda x: x.split('|') if isinstance(x, str) else ([] if pd.isna(x) else x))
    return df

def generar_nube_palabras(df):

    texto = ' '.join([' '.join(map(str, keywords)) for keywords in df['palabras_clave'].dropna()])
    if not texto.strip():
        st.warning("No hay suficientes palabras clave para generar una nube de palabras.")
        return
    
    wordcloud = WordCloud(width=800, height=400, background_color='white', collocations=False).generate(texto)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)


st.title("Exploración General de la Red Científica")

# --- Sección de Carga de Datos ---

st.header("Carga y Gestión de Datos")

with st.expander("Cargar archivo CSV pre-procesado"):
    uploaded_csv = st.file_uploader("Sube un archivo CSV", type="csv", key="csv_uploader_general")
    if uploaded_csv:
        df_cargado = pd.read_csv(uploaded_csv)
        st.session_state.df_papers = convertir_columnas_a_listas(df_cargado)
        st.success(f"¡Éxito! Se cargaron {len(st.session_state.df_papers)} registros.")

with st.expander("Procesar nuevos PDFs", expanded=True):
    motor_ia = st.selectbox("Elige el motor de IA:", ("LM Studio (Local)", "Google Gemini"))
    uploaded_pdfs = st.file_uploader("Sube PDFs para procesar", type="pdf", accept_multiple_files=True, key="pdf_uploader_general")
    if st.button("Iniciar Procesamiento") and uploaded_pdfs:
        with st.spinner(f"Procesando con {motor_ia}..."):
            df_procesado = procesar_archivos_pdf(uploaded_pdfs, motor_ia)
            
            if not df_procesado.empty:
                df_actual = st.session_state.df_papers
                st.session_state.df_papers = pd.concat([df_actual, df_procesado], ignore_index=True).drop_duplicates(subset=['id_articulo'], keep='last')
                st.success(f"¡Procesamiento completo!")


# --- Sección de Análisis General ---
st.header("Análisis General de la Red Científica")

if not st.session_state.df_papers.empty:
    df = st.session_state.df_papers
    
    total_articulos = len(df)
   
    autores_unicos = set(normalizar_nombre(autor) for sublist in df['autores'].dropna() for autor in sublist)
    instituciones_unicas = set(normalizar_nombre(inst) for sublist in df['afiliaciones'].dropna() for inst in sublist)
    
    total_autores = len(autores_unicos)
    total_instituciones = len(instituciones_unicas)
    
    st.subheader("Estadísticas Globales")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Artículos", f"{total_articulos}")
    col2.metric("Autores Únicos", f"{total_autores}")
    col3.metric("Instituciones Únicas", f"{total_instituciones}")

    
    st.markdown(f"""
    Se realizó un análisis exhaustivo de un total de **{total_articulos}** artículos científicos, en el que participaron **{total_autores}** autores y **{total_instituciones}** instituciones.
    La estructura de colaboración observada revela que, en promedio, cada artículo es elaborado por **{round(df['autores'].str.len().mean(), 2)}** autores y cuenta con la participación de **{round(df['afiliaciones'].str.len().mean(), 2)}** instituciones.
    """)
    
    st.subheader("Temas y Tendencias Principales")
    generar_nube_palabras(df)
    
    st.subheader("Descargar Datos Procesados")
    
    st.info("""
    **¿Qué archivo CSV se descarga?**

    El botón de descarga siempre te proporcionará un archivo CSV con la **versión más completa y actualizada de los datos que están en la sesión actual.**

    - **Si solo procesas PDFs:** El CSV contendrá los datos de esos PDFs.
    - **Si solo subes un CSV:** El CSV descargado será idéntico al que subiste.
    - **Si subes un CSV y LUEGO procesas nuevos PDFs:** La aplicación **combina** los datos. El CSV que descargues contendrá **tanto los datos de tu CSV original como los de los nuevos PDFs que acabas de procesar**, todo en un único archivo y sin duplicados.

    Este comportamiento te permite enriquecer y ampliar tu conjunto de datos de forma incremental.
    """)
    
    df_para_guardar = df.copy()
    columnas_lista = ['autores', 'afiliaciones', 'palabras_clave', 'referencias']
    for col in columnas_lista:
         if col in df_para_guardar.columns:
            df_para_guardar[col] = df_para_guardar[col].apply(lambda x: '|'.join(map(str, x)) if isinstance(x, list) else x)
    csv_data = df_para_guardar.to_csv(index=False).encode('utf-8')
    st.download_button("Descargar datos como CSV", csv_data, "extraccion_completa.csv", "text/csv")

else:
    st.warning("Por favor, carga datos para ver el análisis.")