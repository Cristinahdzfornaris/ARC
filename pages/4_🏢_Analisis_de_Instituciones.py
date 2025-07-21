# pages/4_🏢_Analisis_de_Instituciones.py

import streamlit as st
import pandas as pd
import networkx as nx
import streamlit as st
import pandas as pd
import networkx as nx
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from analisis_redes import STOP_WORDS_ES
from analisis_redes import visualizar_red_interactiva, normalizar_nombre
from analisis_redes import (
    visualizar_red_interactiva, 
    normalizar_nombre,
    crear_red_autor_autor 
)


def crear_red_institucion_institucion(df):
    G = nx.Graph()
    
    pesos_aristas = {}
    
    for _, row in df.iterrows():
        instituciones = row.get("afiliaciones", [])
        if isinstance(instituciones, list) and len(instituciones) > 1:
            instituciones_normalizadas = list(set([normalizar_nombre(inst) for inst in instituciones if inst]))
            
            for i in range(len(instituciones_normalizadas)):
                for j in range(i + 1, len(instituciones_normalizadas)):
                    
                    nodo1, nodo2 = sorted((instituciones_normalizadas[i], instituciones_normalizadas[j]))
                    if nodo1 != nodo2:
                        arista = (nodo1, nodo2)
                        pesos_aristas[arista] = pesos_aristas.get(arista, 0) + 1
                        
    
    for arista, peso in pesos_aristas.items():
        G.add_edge(arista[0], arista[1], weight=peso)
        
    return G

st.title("Análisis Detallado de Instituciones")

if 'df_papers' not in st.session_state or st.session_state.df_papers.empty:
    st.warning("No hay datos cargados. Por favor, ve a la página de 'Exploración General'.")
    st.stop()

df = st.session_state.df_papers
G_inst = crear_red_institucion_institucion(df)

st.header("Red de Colaboración Institucional")
st.markdown("En esta red, cada nodo representa una institución y están conectadas si sus investigadores han colaborado en al menos un artículo. El grosor de la línea indica la intensidad de la colaboración.")

visualizar_red_interactiva(G_inst)

st.header("Resumen de Instituciones")


instituciones_unicas = list(G_inst.nodes())
datos_instituciones = []

for inst in instituciones_unicas:
    # Contar total de colaboraciones (grado ponderado)
    total_colaboraciones = G_inst.degree(inst, weight='weight')
    
    # Contar número de instituciones distintas con las que colabora
    colaboradores_distintos = G_inst.degree(inst)
    
    # Contar número de artículos en los que participa
    articulos_participantes = df[df['afiliaciones'].apply(lambda afs: inst in [normalizar_nombre(a) for a in afs])]
    
    datos_instituciones.append({
        "Institución": inst.title(),
        "Total de Colaboraciones": int(total_colaboraciones),
        "Instituciones Colaboradoras": colaboradores_distintos,
        "Artículos Publicados": len(articulos_participantes)
    })

df_inst_stats = pd.DataFrame(datos_instituciones).sort_values("Total de Colaboraciones", ascending=False).reset_index(drop=True)

st.dataframe(df_inst_stats)

# --- Texto de Análisis Descriptivo ---
st.header("Análisis Descriptivo de la Red Institucional")

total_instituciones = len(G_inst.nodes())
total_colaboraciones = sum(d['weight'] for u, v, d in G_inst.edges(data=True))
promedio_colaboradores = df_inst_stats['Instituciones Colaboradoras'].mean()
institucion_mas_activa = df_inst_stats.iloc[0]

st.markdown(f"""
La red interinstitucional se articula a través de **{total_instituciones}** organizaciones, las cuales han forjado **{total_colaboraciones}** lazos de cooperación. El promedio de **{promedio_colaboradores:.2f}** instituciones colaboradoras por cada organización sugiere que la colaboración no es un hecho aislado, sino una estrategia extendida en el ecosistema científico analizado.

La institución que emerge como el pilar central de esta red es **{institucion_mas_activa['Institución']}**, dominando el panorama con **{institucion_mas_activa['Total de Colaboraciones']}** colaboraciones totales y una participación en **{institucion_mas_activa['Artículos Publicados']}** publicaciones. Su alta centralidad no solo refleja su productividad, sino también su rol como un **puente estratégico**, conectando potencialmente a otras instituciones que de otro modo permanecerían aisladas.
""")
# ==============================================================================
# --- NUEVO: PERFIL DE INSTITUCIÓN INDIVIDUAL  ---
# ==============================================================================
st.markdown("---")
st.header("Búsqueda y Perfil de Institución")

if G_inst.number_of_nodes() > 0:

    G_autores = crear_red_autor_autor(df)
    
    lista_instituciones_unicas = sorted(list(G_inst.nodes()))
    inst_seleccionada = st.selectbox(
        "Busca o selecciona una institución para ver su perfil:",
        lista_instituciones_unicas,
        index=None,
        placeholder="Escribe un nombre..."
    )

    if inst_seleccionada:
        st.subheader(f"Perfil Detallado de {inst_seleccionada.title()}")

        # --- 1. Recolección de Datos de la Institución ---
        articulos_inst = df[df['afiliaciones'].apply(lambda afs: inst_seleccionada in [normalizar_nombre(a) for a in afs if a])]
        autores_inst_norm = sorted(list(set(normalizar_nombre(aut) for sublist in articulos_inst['autores'].dropna() for aut in sublist)))
        
        # Colaboradores institucionales y su peso
        colaboradores_inst = sorted(G_inst.neighbors(inst_seleccionada), 
                                    key=lambda x: G_inst[inst_seleccionada][x]['weight'], 
                                    reverse=True)
        
        palabras_inst = [palabra.lower() for sublist in articulos_inst['palabras_clave'].dropna() for palabra in sublist]
        temas_principales_inst = Counter(palabras_inst).most_common(5)


        autores_top = sorted([autor for autor in autores_inst_norm if autor in G_autores.nodes()], 
                             key=lambda x: G_autores.degree(x), 
                             reverse=True)[:5]
        

        texto_analisis = f"**{inst_seleccionada.title()}** es una organización influyente en la red, con participación directa en **{len(articulos_inst)}** artículos y albergando a **{len(autores_inst_norm)}** autores. "
        if colaboradores_inst:
            colab_principal = colaboradores_inst[0]
            peso_colab = G_inst[inst_seleccionada][colab_principal]['weight']
            texto_analisis += f"Su socio de colaboración más fuerte es **{colab_principal.title()}**, con quien comparte **{peso_colab}** co-publicaciones. "
        if autores_top:
            texto_analisis += f"Entre su personal destacan figuras como **{autores_top[0].title()}**. "
        if temas_principales_inst:
             texto_analisis += f"Sus principales líneas de investigación giran en torno a **'{temas_principales_inst[0][0].title()}'**."

        st.markdown(texto_analisis)
        st.markdown("---")
        st.markdown(f"**Capital Humano: Autores Afiliados a {inst_seleccionada.title()}**")
        if autores_inst_norm:
            datos_autores = []
            for autor in autores_inst_norm:
                if autor in G_autores.nodes():
                    articulos_autor = df[df['autores'].apply(lambda auts: autor in [normalizar_nombre(a) for a in auts if a])]
                    temas_autor = Counter([p.lower() for sublist in articulos_autor['palabras_clave'].dropna() for p in sublist]).most_common(1)
                    
                    datos_autores.append({
                        "Autor": autor.title(),
                        "Grado en Red": G_autores.degree(autor),
                        "Nº Artículos": len(articulos_autor),
                        "Tema Principal": temas_autor[0][0].title() if temas_autor else "N/A"
                    })
            df_autores_inst = pd.DataFrame(datos_autores).sort_values("Grado en Red", ascending=False).reset_index(drop=True)
            st.dataframe(df_autores_inst, use_container_width=True)
        else:
            st.info("No hay autores afiliados registrados en el corpus.")
        
        # --- 3. Visualización en Columnas ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Autores Top de {inst_seleccionada.title()}**")
            st.write("(Clasificados por su número total de conexiones en la red)")
            if autores_top:
                datos_autores_top = [{"Autor": a.title(), "Conexiones Totales": G_autores.degree(a)} for a in autores_top]
                st.dataframe(pd.DataFrame(datos_autores_top), use_container_width=True)
            else:
                st.info("No hay autores afiliados en la red de colaboración.")

            st.markdown("**Colaboradores Institucionales Más Frecuentes:**")
            if colaboradores_inst:
                datos_colab_inst = [{"Institución Colaboradora": i.title(), "Nº de Co-publicaciones": G_inst[inst_seleccionada][i]['weight']} for i in colaboradores_inst[:10]] # Top 10
                st.dataframe(pd.DataFrame(datos_colab_inst), use_container_width=True)
            else:
                st.info("No registra colaboraciones con otras instituciones.")
        
        with col2:
            st.markdown("**Principales Temas de Investigación:**")
            if palabras_inst:

                texto_completo_inst = ' '.join(palabras_inst)
                

                palabras_filtradas_inst = [word for word in texto_completo_inst.lower().split() if word not in STOP_WORDS_ES and len(word) > 2]
                texto_filtrado_inst = ' '.join(palabras_filtradas_inst)

                if texto_filtrado_inst.strip():

                    wordcloud = WordCloud(width=400, height=250, background_color='white', collocations=False).generate(texto_filtrado_inst)
                    fig, ax = plt.subplots()
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                else:
                    st.info("No hay palabras clave relevantes para esta institución después de filtrar.")
            else:
                st.info("No hay palabras clave asociadas a esta institución.")



            st.markdown("**Índice de Colaboración de la Institución:**")
            

            articulos_colaborativos = 0
            for _, row in articulos_inst.iterrows():
                if len(row.get('autores', [])) > 1:
                    articulos_colaborativos += 1
            
            total_articulos_inst = len(articulos_inst)
            ratio_colaboracion = (articulos_colaborativos / total_articulos_inst) * 100 if total_articulos_inst > 0 else 0
            
  
            st.progress(int(ratio_colaboracion), text=f"{ratio_colaboracion:.1f}% de sus artículos son en coautoría")
            st.write(
                """
                Esta métrica mide el porcentaje de la producción científica de la institución que se realiza en equipo.
                - Un **alto índice** sugiere una cultura de trabajo colaborativo, común en proyectos que requieren diversas especialidades.
                - Un **bajo índice** puede indicar un enfoque en áreas donde la investigación individual es más frecuente.
                """
            )


else:
    st.info("La red de instituciones está vacía.")