import streamlit as st
import pandas as pd
import networkx as nx
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from analisis_redes import STOP_WORDS_ES 

def generar_nube_palabras(df):
    texto_completo = ' '.join([' '.join(map(str, keywords)) for keywords in df['palabras_clave'].dropna()])
 
    texto_filtrado = ' '.join([word for word in texto_completo.split() if word.lower() not in STOP_WORDS_ES])
    
    if not texto_filtrado.strip():
       
        return
    
    wordcloud = WordCloud(..., collocations=False).generate(texto_filtrado)

from analisis_redes import (
    crear_red_autor_autor, 
    crear_red_autor_institucion,
    crear_red_temas,
    visualizar_red_interactiva, 
    mostrar_metricas_centralidad, 
    normalizar_nombre
)

st.title("Análisis Estructural y Temático de la Red")

# --- Verificación inicial de datos ---
if 'df_papers' not in st.session_state or st.session_state.df_papers.empty:
    st.warning("No hay datos cargados. Por favor, ve a la página de 'Exploración General' para cargar o procesar datos.")
    st.stop()

df = st.session_state.df_papers


st.header("Perspectivas de la Red Científica")
st.markdown("Cada tipo de red ofrece una visión diferente de las interacciones en el corpus científico. Selecciona una para explorarla.")

tipo_red_seleccionada = st.selectbox(
    "Selecciona la perspectiva de análisis:",
    ("Análisis de Colaboración (Autor-Autor)", 
     "Análisis de Afiliación (Autor-Institución)",
     "Análisis Temático (Co-ocurrencia de Temas)")
)

# ==============================================================================
# --- PESTAÑA 1: RED AUTOR-AUTOR (CON ANÁLISIS DE AUTORES SOLITARIOS) ---
# ==============================================================================
if tipo_red_seleccionada == "Análisis de Colaboración (Autor-Autor)":
    st.subheader("Red de Colaboración entre Autores")
    G = crear_red_autor_autor(df)
    
  
    total_autores_df = set(normalizar_nombre(autor) for sublist in df['autores'].dropna() for autor in sublist)
    autores_colaboradores = set(G.nodes())
    autores_solitarios = total_autores_df - autores_colaboradores
    
   
    st.success(f"""
    Esta red social conecta a **{len(autores_colaboradores)}** autores que han colaborado al menos una vez, a través de **{G.number_of_edges()}** lazos de coautoría. 
    Además, se han identificado **{len(autores_solitarios)}** autores que publican de forma individual en este corpus.
    """)
    
   
    st.markdown("""
    **Preguntas Clave respondidas con datos de la red:**
    """)
    if G.number_of_nodes() > 0:
        
        grados = sorted(G.degree(), key=lambda x: x[1], reverse=True)
        betweenness = sorted(nx.betweenness_centrality(G).items(), key=lambda x: x[1], reverse=True)
        lider_grado = grados[0]
        puente_betweenness = betweenness[0]
        num_componentes = nx.number_connected_components(G)

        st.markdown(f"""
        - **¿Quiénes son los líderes?** El autor más central por número de conexiones es **{lider_grado[0].title()}**, con **{lider_grado[1]}** colaboradores distintos.
        - **¿Quiénes son los puentes?** El actor que más frecuentemente conecta a otros grupos es **{puente_betweenness[0].title()}**, al tener el mayor índice de intermediación.
        - **¿Cómo de cohesionada es la red?** La red de colaboración se divide en **{num_componentes}** subgrupos o "islas" de investigación.
        """)
    
    
    with st.expander(f"Ver la lista de los {len(autores_solitarios)} autores que publican individualmente"):
        if autores_solitarios:
            df_solitarios = pd.DataFrame(sorted([a.title() for a in autores_solitarios]), columns=["Autor"])
            st.dataframe(df_solitarios)
        else:
            st.info("Todos los autores en este corpus han colaborado al menos una vez.")
            
    with st.expander("Explorar la Red Completa y Métricas Detalladas"):
        visualizar_red_interactiva(G)
        mostrar_metricas_centralidad(G)

# ==============================================================================
# --- PESTAÑA 2: RED AUTOR-INSTITUCIÓN (CON FORMATO DE CAJA VERDE) ---
# ==============================================================================
elif tipo_red_seleccionada == "Análisis de Afiliación (Autor-Institución)":
    st.subheader("Red de Afiliación Institucional")
    G_bipartita = crear_red_autor_institucion(df)
    autores_nodos = {n for n, d in G_bipartita.nodes(data=True) if d.get("bipartite") == 0}
    instituciones_nodos = {n for n, d in G_bipartita.nodes(data=True) if d.get("bipartite") == 1}

    
    st.success(f"""
    Esta red de afiliación conecta a **{len(autores_nodos)}** autores con **{len(instituciones_nodos)}** instituciones. 
    Analizar esta estructura nos permite identificar qué organizaciones son los principales focos de producción científica y cómo se distribuye el capital humano investigador.
    """)
    
   
    st.markdown("""
    **Preguntas Clave respondidas con datos de la red:**
    """)
    if instituciones_nodos:
        grados_inst = sorted([(inst, G_bipartita.degree(inst)) for inst in instituciones_nodos], key=lambda x: x[1], reverse=True)
        centro_poder = grados_inst[0]
        
        grados_autores = {autor: G_bipartita.degree(autor) for autor in autores_nodos}
        autor_puente = max(grados_autores, key=grados_autores.get)

        st.markdown(f"""
        - **Centros de poder:** La institución que aglutina más talento, conectando con **{centro_poder[1]}** autores distintos, es **{centro_poder[0].title()}**.
        - **Movilidad y puentes institucionales:** El autor con más afiliaciones distintas, actuando como un puente entre instituciones, es **{autor_puente.title()}**, con **{grados_autores[autor_puente]}** lazos institucionales.
        - **Capital humano:** Instituciones como la mencionada son clave, pues albergan a la mayor cantidad de investigadores, convirtiéndose en focos de producción científica.
        """)
        
    with st.expander("Explorar la Red Bipartita Completa"):
        pos = nx.bipartite_layout(G_bipartita, autores_nodos, align='horizontal')
        visualizar_red_interactiva(G_bipartita)

# ==============================================================================
# --- PESTAÑA 3: RED DE TEMAS (CON FORMATO DE CAJA VERDE) ---
# ==============================================================================
elif tipo_red_seleccionada == "Análisis Temático (Co-ocurrencia de Temas)":
    st.subheader("Red de Co-ocurrencia de Temas")
    G_temas = crear_red_temas(df)
    
    
    st.success(f"""
    Este mapa conceptual se articula en torno a **{G_temas.number_of_nodes()}** temas distintos, conectados por **{G_temas.number_of_edges()}** asociaciones. 
    Esta red revela la estructura intelectual del corpus, mostrando qué ideas están en el centro del debate y cuáles se investigan conjuntamente.
    """)

   
    st.markdown("""
    **Preguntas Clave respondidas con datos de la red:**
    """)
    if G_temas.number_of_nodes() > 0:
        # Tema más frecuente (conteo simple)
        todas_palabras = [palabra.lower().strip() for sublist in df['palabras_clave'].dropna() for palabra in sublist]
        conteo_palabras = Counter(todas_palabras)
        tema_mas_frecuente, _ = conteo_palabras.most_common(1)[0]
        
        # Asociación más fuerte (el par que más co-ocurre)
        arista_mas_fuerte = sorted(G_temas.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)[0]
        
        st.markdown(f"""
        - **¿Cuál es el tema central?** El concepto que aparece con mayor frecuencia en los artículos es **"{tema_mas_frecuente.title()}"**.
        - **¿Qué temas se investigan juntos?** La asociación conceptual más fuerte se da entre **"{arista_mas_fuerte[0].title()}"** y **"{arista_mas_fuerte[1].title()}"**, que aparecen juntos en **{arista_mas_fuerte[2]['weight']}** artículos.
        """)
    
    with st.expander("Explorar la Red Temática Completa"):
        visualizar_red_interactiva(G_temas)
# ==============================================================================
# --- SECCIÓN DE PERFIL DE AUTOR INDIVIDUAL (VERSIÓN DEFINITIVA) ---
# ==============================================================================
st.markdown("---")
st.header("Búsqueda y Perfil de Autor Individual")

G_autores_perfil = crear_red_autor_autor(df)
if G_autores_perfil.number_of_nodes() > 0:
    lista_autores_unicos = sorted(list(G_autores_perfil.nodes()))
    autor_seleccionado = st.selectbox(
        "Busca o selecciona un autor para ver su perfil detallado:", 
        lista_autores_unicos, 
        index=None, 
        placeholder="Escribe un nombre para buscar..."
    )

    if autor_seleccionado:
        st.subheader(f"Perfil Detallado de {autor_seleccionado.title()}")

     
       
        with st.spinner("Calculando redes de afiliación..."):
            autor_instituciones_map = {}
            for _, row in df.iterrows():
                autores_norm = [normalizar_nombre(a) for a in row.get('autores', []) if a]
                instituciones_norm = set([normalizar_nombre(i) for i in row.get('afiliaciones', []) if i])
                for autor in autores_norm:
                    autor_instituciones_map.setdefault(autor, set()).update(instituciones_norm)

        # --- Recolección de Datos del Autor Seleccionado ---
        articulos_del_autor = df[df['autores'].apply(lambda autores: autor_seleccionado in [normalizar_nombre(a) for a in autores if a])]
        num_articulos = len(articulos_del_autor)
        
        colaboradores_directos = list(G_autores_perfil.neighbors(autor_seleccionado))
        num_colaboradores = len(colaboradores_directos)
        
      
        instituciones_autor = list(autor_instituciones_map.get(autor_seleccionado, set()))
        num_instituciones = len(instituciones_autor)
        
        palabras_autor = [palabra.lower() for sublist in articulos_del_autor['palabras_clave'].dropna() for palabra in sublist]
        temas_principales = Counter(palabras_autor).most_common(1)
        
        # --- Párrafo de Análisis Personalizado y Justificado ---
        texto_analisis = f"**{autor_seleccionado.title()}** participa en la red con **{num_articulos}** publicación(es). "
        if num_colaboradores > 0:
            grados_colaboradores = {colab: G_autores_perfil.degree(colab) for colab in colaboradores_directos}
            autor_mas_colaborador = max(grados_colaboradores, key=grados_colaboradores.get)
            texto_analisis += f"Ha colaborado con **{num_colaboradores}** colegas. Su colaborador más notable (por ser el más conectado del grupo) es **{autor_mas_colaborador.title()}**, quien tiene **{grados_colaboradores[autor_mas_colaborador]}** conexiones en la red general. "
        else:
            texto_analisis += "Dentro de este corpus, no presenta colaboraciones directas. "
        
        st.markdown(texto_analisis)
        st.markdown("---")
        
        # --- Visualización en Columnas ---
        col1, col2 = st.columns([1.5, 0.8]) 
        
        with col1:
            st.markdown("**Colaboradores y su Contexto Institucional:**")
            if colaboradores_directos:
               
                datos_colaboradores = []
                for colab in colaboradores_directos:
                    
                    inst_colab = list(autor_instituciones_map.get(colab, set()))
                    inst_colab_str = ", ".join(sorted([i.title() for i in inst_colab])) if inst_colab else "N/A"
                    
                    articulos_colab = df[df['autores'].apply(lambda auts: colab in [normalizar_nombre(a) for a in auts if a])]
                    datos_colaboradores.append({
                        "Colaborador": colab.title(),
                        "Grado": G_autores_perfil.degree(colab),
                        "Artículos": len(articulos_colab),
                        "Sus Instituciones": inst_colab_str
                    })
                df_colabs = pd.DataFrame(datos_colaboradores).sort_values("Grado", ascending=False).reset_index(drop=True)
                st.dataframe(df_colabs, use_container_width=True)
            else:
                st.info("Sin colaboradores directos.")

        with col2:
            st.markdown(f"**Afiliaciones de {autor_seleccionado.title()}:**")
            if instituciones_autor:
                st.dataframe(pd.DataFrame(sorted([i.title() for i in instituciones_autor]), columns=["Institución"]), use_container_width=True)
            else:
                st.info("No se registran afiliaciones.")

            st.markdown("**Subgrafo de Colaboraciones:**")
            nodos_subgrafo = [autor_seleccionado] + colaboradores_directos
            subgrafo = G_autores_perfil.subgraph(nodos_subgrafo)
            visualizar_red_interactiva(subgrafo)

     
        st.markdown("**Artículos Publicados por el Autor:**")
        st.dataframe(articulos_del_autor[['titulo']].reset_index(drop=True), use_container_width=True)
        
        st.markdown(f"**Nube de Palabras Clave del Autor:**")
        if palabras_autor:
           
            texto_completo_autor = ' '.join(palabras_autor)
            
      
            palabras_filtradas_autor = [word for word in texto_completo_autor.lower().split() if word not in STOP_WORDS_ES and len(word) > 2]
            texto_filtrado_autor = ' '.join(palabras_filtradas_autor)
            
            if texto_filtrado_autor.strip():
       
                wordcloud = WordCloud(width=800, height=250, background_color='white', collocations=False).generate(texto_filtrado_autor)
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            else:
                st.info("No hay palabras clave relevantes para este autor después de filtrar.")
        else:
            st.info("Sin palabras clave asociadas.")