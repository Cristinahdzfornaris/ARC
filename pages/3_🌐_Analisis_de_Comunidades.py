# pages/3_🌐_Analisis_de_Comunidades.py

import streamlit as st
import pandas as pd
import networkx as nx
from networkx.algorithms import community as nx_comm
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from analisis_redes import crear_red_autor_autor, visualizar_red_interactiva, normalizar_nombre
from analisis_redes import crear_red_autor_autor, visualizar_red_interactiva
from analisis_redes import STOP_WORDS_ES
st.title("Análisis de Comunidades de Investigación")
from collections import Counter

if 'df_papers' not in st.session_state or st.session_state.df_papers.empty:
    st.warning("No hay datos cargados. Por favor, ve a la página de 'Exploración General'.")
    st.stop()

df = st.session_state.df_papers
G = crear_red_autor_autor(df)

st.header("Detección y Visualización de Comunidades")


with st.spinner("Detectando comunidades en la red..."):
    comunidades = list(nx_comm.greedy_modularity_communities(G))
    st.success(f"¡Detección completa! Se encontraron {len(comunidades)} comunidades.")

# Colorear el grafo
pos = nx.spring_layout(G, seed=42)
colores_nodos = {}
for i, comm in enumerate(comunidades):
    for nodo in comm:
        colores_nodos[nodo] = i

node_trace = go.Scatter(x=[pos[n][0] for n in G.nodes()], y=[pos[n][1] for n in G.nodes()],
                        mode='markers', hoverinfo='text',
                        text=[f"{n.title()}<br>Comunidad: {colores_nodos[n]}" for n in G.nodes()],
                        marker=dict(color=[colores_nodos[n] for n in G.nodes()],
            size=10, colorscale='Viridis', showscale=False) )
edge_trace = go.Scatter(x=[pos[edge[0]][0] if edge[0] in pos else None for edge in G.edges()],
                        y=[pos[edge[0]][1] if edge[0] in pos else None for edge in G.edges()],
                        line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')

fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(showlegend=False, hovermode='closest',
               margin=dict(b=0,l=0,r=0,t=0)))
st.plotly_chart(fig, use_container_width=True)


# --- Bloque de Análisis Descriptivo para Comunidades ---
num_comunidades = len(comunidades)
tamanos_comunidades = [len(c) for c in comunidades]
comunidad_mas_grande = max(tamanos_comunidades) if tamanos_comunidades else 0
comunidad_mas_pequena = min(tamanos_comunidades) if tamanos_comunidades else 0
promedio_tamano_comunidad = sum(tamanos_comunidades) / num_comunidades if num_comunidades > 0 else 0




st.markdown(f"""
El análisis de modularidad ha revelado la existencia de **{num_comunidades}** comunidades o clústeres de investigación. La distribución de tamaños es heterogénea, con la comunidad más grande agrupando a **{comunidad_mas_grande}** miembros y la más pequeña conteniendo solo **{comunidad_mas_pequena}**. El tamaño medio de **{promedio_tamano_comunidad:.2f}** autores por comunidad refuerza la idea de una estructura social organizada en grupos de trabajo.

La detección de estas comunidades es fundamental, ya que nos permite ir más allá del análisis individual y entender la **meso-escala** de la red. Cada comunidad representa un posible laboratorio, un grupo de investigación con intereses temáticos comunes o una red de colaboración geográfica. Explorar cada comunidad nos permite identificar sus líderes, sus temas de especialización y su nivel de cohesión interna.
""")


# ==============================================================================
# --- SECCIÓN DE EXPLORACIÓN DE COMUNIDAD (VERSIÓN PRO) ---
# ==============================================================================
st.header("Explorar Comunidad Específica")


comunidades_ordenadas = sorted(comunidades, key=len, reverse=True)
opciones_comunidad = {f"Comunidad {i+1} ({len(comm)} miembros)": comm for i, comm in enumerate(comunidades_ordenadas)}

comm_seleccionada_key = st.selectbox("Selecciona una comunidad para analizar:", opciones_comunidad.keys())

if comm_seleccionada_key:
    comm_seleccionada_nodos = opciones_comunidad[comm_seleccionada_key]
    subgrafo_comm = G.subgraph(comm_seleccionada_nodos)
    
    st.subheader(f"Análisis Detallado de la {comm_seleccionada_key}")
    
    
    densidad = nx.density(subgrafo_comm)
    clustering_promedio = nx.average_clustering(subgrafo_comm)
    
    df_comm = df[df['autores'].apply(lambda autores: any(normalizar_nombre(a) in comm_seleccionada_nodos for a in autores))]
    
    
    instituciones_comm = Counter([normalizar_nombre(i) for sublist in df_comm['afiliaciones'].dropna() for i in sublist])
    inst_dominante_info = instituciones_comm.most_common(1)[0] if instituciones_comm else ("N/A", 0)
    
    
    grados_internos = sorted(subgrafo_comm.degree(), key=lambda x: x[1], reverse=True)
    autor_central_comm = grados_internos[0] if grados_internos else ("N/A", 0)

   
    st.markdown(f"""
    Esta comunidad agrupa a **{len(comm_seleccionada_nodos)}** autores. Su **densidad es de {densidad:.2f}**, indicando su nivel de conexión interna. 
    El autor más central *dentro* de este grupo es **{autor_central_comm[0].title()}** con **{autor_central_comm[1]}** colaboraciones internas.
    Institucionalmente, la organización con mayor presencia en este clúster es **{inst_dominante_info[0].title()}**, con **{inst_dominante_info[1]}** apariciones de sus autores.
    """)
    
    
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        st.markdown("**Miembros Clave de la Comunidad:**")
        st.write("Autores ordenados por su número de conexiones totales en la red.")
        
        
        datos_autores_comm = []
        for autor in comm_seleccionada_nodos:
            if autor in G.nodes():
                articulos_autor = df[df['autores'].apply(lambda auts: autor in [normalizar_nombre(a) for a in auts if a])]
                temas_autor = Counter([p.lower() for sublist in articulos_autor['palabras_clave'].dropna() for p in sublist]).most_common(1)
                
                datos_autores_comm.append({
                    "Autor": autor.title(),
                    "Grado Total": G.degree(autor),
                    "Grado Interno": subgrafo_comm.degree(autor),
                    "Nº Artículos": len(articulos_autor),
                    "Tema Principal": temas_autor[0][0].title() if temas_autor else "N/A"
                })
        df_autores_comm = pd.DataFrame(datos_autores_comm).sort_values("Grado Total", ascending=False).reset_index(drop=True)
        st.dataframe(df_autores_comm, use_container_width=True, height=400)

    with col2:
        st.markdown("**Red Interna de la Comunidad:**")
        visualizar_red_interactiva(subgrafo_comm)
        
    st.markdown("**Instituciones Participantes:**")
    st.write("Organizaciones con mayor número de autores en esta comunidad.")
    if instituciones_comm:
            df_inst_comm = pd.DataFrame(instituciones_comm.most_common(10), columns=["Institución", "Nº de Autores Afiliados"])
            df_inst_comm["Institución"] = df_inst_comm["Institución"].apply(lambda x: x.title())
            st.dataframe(df_inst_comm, use_container_width=True)
    else:
            st.info("No hay datos de afiliación para esta comunidad.")

    
    st.markdown("**Líneas de Trabajo Principales de la Comunidad:**")
    texto_comm = ' '.join([' '.join(map(str, keywords)) for keywords in df_comm['palabras_clave'].dropna()])
    palabras_filtradas_comm = [word for word in texto_comm.lower().split() if word not in STOP_WORDS_ES and len(word) > 2]
    texto_filtrado_comm = ' '.join(palabras_filtradas_comm)
    
    if texto_filtrado_comm.strip():
        wordcloud = WordCloud(width=800, height=250, background_color='white', collocations=False).generate(texto_filtrado_comm)
        fig_wc, ax_wc = plt.subplots()
        ax_wc.imshow(wordcloud, interpolation='bilinear')
        ax_wc.axis('off')
        st.pyplot(fig_wc)
    else:
        st.write("No hay palabras clave relevantes para esta comunidad.")