# ==============================================================================
# ARCHIVO: app.py
# Propósito: Página de Inicio y Bienvenida de la Aplicación Multi-Página.
# ==============================================================================

import streamlit as st
import pandas as pd


st.set_page_config(
    layout="wide",
    page_title="Exploración de la Red Científica",
    page_icon="🔬" 
)



st.title("🔬 Exploración de la Red Científica")
st.markdown("---")

st.header("Bienvenido al Analizador de Redes de Colaboración Científica")

st.markdown("""
### ¿Por qué Analizar una Red Científica?

Un conjunto de artículos científicos es más que una simple lista de publicaciones; es un reflejo de una **red social** donde los investigadores y las instituciones interactúan, colaboran y construyen conocimiento. Analizar esta red nos permite responder preguntas clave que un simple lector no podría:

-   **¿Quiénes son los líderes?** Podemos identificar a los autores más influyentes, no solo por cuánto publican, sino por cuán conectados están y cuán cruciales son para el flujo de información.
-   **¿Cómo se agrupa la ciencia?** Detectamos "comunidades" o clústeres de investigación que nos muestran cómo se organizan los científicos, revelando laboratorios, grupos con intereses comunes o afinidades geográficas.
-   **¿Qué instituciones son los pilares de la investigación?** Analizamos qué universidades o centros actúan como "hubs" que conectan a diferentes actores de la red.
-   **¿Cuáles son los temas candentes?** A través de las palabras clave, podemos visualizar las tendencias temáticas y las áreas de mayor interés en el corpus.

### ¿Cómo Usar esta Herramienta?

1.  **Vaya a `1_🔎_Exploracion_General` en el menú de la izquierda para Cargar sus Datos:** Este es el primer y más importante paso. Puede subir un archivo CSV con datos ya procesados o procesar un lote de PDFs usando un modelo de IA local (LM Studio) o una API online (Google Gemini). Una vez cargados, los datos estarán disponibles para todas las demás secciones.
2.  **Explore las Diferentes Páginas de Análisis:** Cada página en el menú de navegación le ofrece una perspectiva única de la red.
3.  **Utilice los Filtros y Selectores:** Dentro de cada página de análisis, encontrará filtros y menús desplegables. Estos son fundamentales para **profundizar en el análisis**. Por ejemplo:
    -   **Filtrar por autor** le permite pasar de una vista global a un análisis de "ego-red", centrando el universo en un solo actor y sus conexiones directas.
    -   **Seleccionar una comunidad** le permite aislar un subgrupo de investigación y analizar su dinámica interna, sus temas de especialización y sus miembros más relevantes.

Este proyecto fue desarrollado como parte de la asignatura de Análisis de Redes Complejas.
""")

st.info("Para comenzar, por favor, seleccione una página del menú de navegación que se encuentra en la barra lateral izquierda.")


if 'df_papers' not in st.session_state:
    st.session_state.df_papers = pd.DataFrame()