# analisis_citas.py

import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px

def analizar_referencias_citadas(df):
    st.header("Análisis de Referencias")

    if 'referencias' not in df.columns or df['referencias'].isnull().all():
        st.warning("No se encontraron datos de referencias en los artículos cargados.")
        return

    # Aplanar la lista de todas las referencias en una sola
    todas_las_referencias = [ref for sublist in df['referencias'].dropna() for ref in sublist]

    if not todas_las_referencias:
        st.info("Aunque la columna de referencias existe, no se extrajo ninguna cita.")
        return

    st.subheader("Referencias más citadas en el corpus")
    st.write(f"Se encontraron un total de {len(todas_las_referencias)} citas en los {len(df)} artículos.")

    conteo_citas = Counter(todas_las_referencias)
    df_citas = pd.DataFrame(conteo_citas.items(), columns=['Referencia', 'Conteo']).sort_values('Conteo', ascending=False)
    
    top_n = st.slider("Selecciona el número de referencias a mostrar:", 5, 50, 15)

    fig = px.bar(df_citas.head(top_n), 
                 x='Conteo', 
                 y='Referencia', 
                 orientation='h',
                 title=f'Top {top_n} Referencias Más Citadas',
                 labels={'Conteo': 'Número de veces citada', 'Referencia': ''})
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("Tabla completa de citas:")
    st.dataframe(df_citas)