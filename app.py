# app.py (Versión Final con Análisis de Comunidades Integrado)

import streamlit as st
import pandas as pd
import networkx as nx
from collections import Counter
from itertools import combinations
from unidecode import unidecode
from thefuzz import fuzz
from streamlit_agraph import agraph, Node, Edge, Config
import matplotlib.pyplot as plt

# ==============================================================================
# --- CONFIGURACIÓN DE LA PÁGINA ---
# ==============================================================================
st.set_page_config(
    page_title="Análisis de Redes Científicas",
    page_icon="🕸️",
    layout="wide"
)

# ==============================================================================
# --- FUNCIONES DE PROCESAMIENTO Y CACHÉ ---
# ==============================================================================
@st.cache_data
def cargar_y_limpiar_datos(archivo_csv):
    """Carga y preprocesa los datos desde el CSV."""
    try:
        df = pd.read_csv(archivo_csv)
        df['autores'] = df['autores'].fillna('').apply(lambda x: [a.strip() for a in x.split('|') if a.strip()])
        df['afiliaciones'] = df['afiliaciones'].fillna('').apply(lambda x: sorted(list(set([a.strip() for a in x.split('|') if a.strip()]))))
        df['palabras_clave'] = df['palabras_clave'].fillna('').apply(lambda x: sorted(list(set([k.strip().lower() for k in x.split('|') if k.strip()]))))
        df['tematica'] = df['tematica'].fillna('').str.strip()
        df = df[df['autores'].apply(len) > 0].reset_index(drop=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{archivo_csv}'. Asegúrate de que esté en la misma carpeta que 'app.py'.")
        return None

def crear_forma_base(nombre):
    """Crea una versión 'base' limpia de un nombre para comparación."""
    nombre_limpio = nombre.lower()
    reemplazos = {'a´': 'á', 'e´': 'é', 'i´': 'í', 'o´': 'ó', 'u´': 'ú', 'n~': 'ñ'}
    for e, c in reemplazos.items(): nombre_limpio = nombre_limpio.replace(e, c)
    nombre_limpio = unidecode(nombre_limpio)
    nombre_limpio = ''.join(c for c in nombre_limpio if c.isalpha() or c.isspace())
    titulos = ["dr", "dra", "msc", "lic", "prof"]
    partes = nombre_limpio.split()
    partes_sin_titulos = [p for p in partes if p not in titulos]
    return " ".join(partes_sin_titulos)

@st.cache_data
def desambiguar_autores(autores_brutos, umbral=85):
    """Agrupa autores usando similitud de strings."""
    formas_base = {original: crear_forma_base(original) for original in autores_brutos}
    grupos = [[autor] for autor in autores_brutos]
    hubo_fusion = True
    while hubo_fusion:
        hubo_fusion, i = False, 0
        while i < len(grupos):
            j = i + 1
            while j < len(grupos):
                if fuzz.token_set_ratio(formas_base[grupos[i][0]], formas_base[grupos[j][0]]) > umbral:
                    grupos[i].extend(grupos[j]); del grupos[j]; hubo_fusion = True
                else: j += 1
            i += 1
    mapa_desambiguacion = {}
    for grupo in grupos:
        canonico = max(grupo, key=len)
        for v in grupo: mapa_desambiguacion[v] = canonico
    return mapa_desambiguacion

@st.cache_resource
def generar_todos_los_grafos(_df_articulos):
    """Genera todos los grafos y los devuelve en un diccionario."""
    grafos = {}
    autores_brutos = list(set([a for sublist in _df_articulos['autores'] for a in sublist]))
    mapa_nombres = desambiguar_autores(autores_brutos)
    autores_canonicos_nodos = set(mapa_nombres.values())
    
    # Red de Coautoría
    aristas_co = [edge for sl in _df_articulos['autores'] if len(ac := sorted(list(set(mapa_nombres.get(a) for a in sl if a in mapa_nombres)))) > 1 for edge in combinations(ac, 2)]
    G_coautoria = nx.Graph()
    if aristas_co:
        for (u, v), w in Counter(aristas_co).items(): G_coautoria.add_edge(u, v, weight=w)
    grafos['coautoria'] = G_coautoria

    # Red de Palabras Clave
    aristas_kw = [edge for kw_list in _df_articulos['palabras_clave'] if len(kw_list) > 1 for edge in combinations(kw_list, 2)]
    G_keywords = nx.Graph()
    if aristas_kw:
        for (u, v), w in Counter(aristas_kw).items(): G_keywords.add_edge(u, v, weight=w)
    grafos['keywords'] = G_keywords

    # Red Bipartita Autor-Afiliación
    G_afiliacion = nx.Graph()
    for autor in autores_canonicos_nodos: G_afiliacion.add_node(autor, type='Autor')
    for afiliaciones in _df_articulos['afiliaciones']:
        for afil in afiliaciones: G_afiliacion.add_node(afil, type='Afiliacion')
    for _, row in _df_articulos.iterrows():
        autores = set(mapa_nombres.get(a) for a in row['autores'] if a in mapa_nombres)
        for autor in autores:
            for afil in row['afiliaciones']: G_afiliacion.add_edge(autor, afil)
    grafos['afiliacion'] = G_afiliacion

    # Red Bipartita Autor-Temática
    G_tematica = nx.Graph()
    for autor in autores_canonicos_nodos: G_tematica.add_node(autor, type='Autor')
    for tema in _df_articulos['tematica'].unique():
        if tema: G_tematica.add_node(tema, type='Tematica')
    for _, row in _df_articulos.iterrows():
        if row['tematica']:
            autores = set(mapa_nombres.get(a) for a in row['autores'] if a in mapa_nombres)
            for autor in autores: G_tematica.add_edge(autor, row['tematica'])
    grafos['tematica'] = G_tematica
    
    return grafos, mapa_nombres

def dibujar_grafo_interactivo(G, titulo, config, comunidades_map=None):
    """Dibuja un grafo interactivo, con opción para colorear por comunidades."""
    if not G.nodes():
        st.warning(f"La red '{titulo}' está vacía y no se puede dibujar.")
        return

    node_colors = []
    if comunidades_map:
        num_comunidades = len(set(comunidades_map.values()))
        cmap = plt.cm.get_cmap('viridis', num_comunidades)
        for node in G.nodes():
            comm_id = comunidades_map.get(node, -1)
            if comm_id != -1:
                color_rgba = cmap(comm_id / num_comunidades)
                node_colors.append(f'#{int(color_rgba[0]*255):02x}{int(color_rgba[1]*255):02x}{int(color_rgba[2]*255):02x}')
            else:
                node_colors.append("#808080") # Gris para nodos sin comunidad
    else:
        node_colors = ["#A7D3F7"] * G.number_of_nodes()

    nodes = [Node(id=n, label=str(n), size=10 + G.degree(n) * 2, title=f"Grado: {G.degree(n)}", color=color)
             for n, color in zip(G.nodes(), node_colors)]
    edges = [Edge(source=u, target=v, title=f"Peso: {d.get('weight', 1)}", value=d.get('weight', 1))
             for u, v, d in G.edges(data=True)]
    
    st.subheader(titulo)
    agraph(nodes=nodes, edges=edges, config=config)

# ==============================================================================
# --- INTERFAZ PRINCIPAL DE LA APLICACIÓN ---
# ==============================================================================

st.sidebar.title("Análisis de Redes Científicas")


df_articulos = cargar_y_limpiar_datos('datos.csv')

if df_articulos is not None:
    with st.spinner("Procesando datos y generando redes..."):
        grafos, mapa_nombres = generar_todos_los_grafos(df_articulos)
    
    paginas = ["Introducción", "Red de Coautoría", "Red de Palabras Clave", "Red Autor-Afiliación", "Red Autor-Temática"]
    pagina_seleccionada = st.sidebar.radio("Selecciona una sección:", paginas)

    config_fisicas = Config(width=1100, height=800, directed=False, physics=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6")
    
    if pagina_seleccionada == "Introducción":
        st.title("🕸️ Dashboard de Análisis de Redes Científicas")
        st.markdown("Bienvenido. Utiliza la barra lateral para explorar las diferentes redes generadas a partir de un corpus de publicaciones.")
        st.header("Resumen del Dataset")
        n_articulos, n_autores = len(df_articulos), len(set(mapa_nombres.values()))
        n_afiliaciones = len(set(a for sublist in df_articulos['afiliaciones'] for a in sublist))
        col1, col2, col3 = st.columns(3)
        col1.metric("Artículos Analizados", n_articulos)
        col2.metric("Autores Únicos", n_autores)
        col3.metric("Instituciones Únicas", n_afiliaciones)
        st.header("Muestra de Datos Extraídos")
        st.dataframe(df_articulos.head())

    elif pagina_seleccionada in ["Red de Coautoría", "Red de Palabras Clave"]:
        if pagina_seleccionada == "Red de Coautoría":
            st.title("👥 Red de Coautoría")
            G = grafos.get('coautoria')
            entidad = "Autor"; metricas = ["Grado Ponderado", "Intermediación (Betweenness)", "Cercanía (Closeness)", "Vector Propio (Eigenvector)"]
        else:
            st.title("🔑 Red de Co-ocurrencia de Palabras Clave")
            G = grafos.get('keywords')
            entidad = "Palabra Clave"; metricas = ["Grado Ponderado", "Intermediación (Betweenness)"]

        tab1, tab2, tab3 = st.tabs(["Visualización de Comunidades", "Análisis de Métricas", "Explorar Comunidades"])

        with tab1:
            st.markdown(f"Grafo coloreado por **comunidades** (grupos de {entidad.lower()}es fuertemente conectados).")
            if G and G.number_of_nodes() > 0:
                comunidades = nx.community.louvain_communities(G, weight='weight')
                comunidades_map = {node: i for i, comm in enumerate(comunidades) for node in comm}
                dibujar_grafo_interactivo(G, f"Grafo Interactivo de {entidad}es", config_fisicas, comunidades_map=comunidades_map)
            else: st.warning("La red está vacía.")
        
        with tab2:
            st.header(f"Rankings de {entidad}es")
            if G and G.number_of_nodes() > 0:
                df_metricas = pd.DataFrame(index=list(G.nodes()))
                df_metricas['Grado Ponderado'] = dict(G.degree(weight='weight'))
                df_metricas['Intermediación (Betweenness)'] = nx.betweenness_centrality(G, weight='weight', normalized=True)
                if pagina_seleccionada == "Red de Coautoría":
                    df_metricas['Cercanía (Closeness)'] = nx.closeness_centrality(G, distance='weight')
                    df_metricas['Vector Propio (Eigenvector)'] = nx.eigenvector_centrality(G, weight='weight', max_iter=1000)
                metrica_elegida = st.selectbox(f"Selecciona una métrica para el ranking de {entidad}es:", metricas)
                st.dataframe(df_metricas.sort_values(by=metrica_elegida, ascending=False).head(20))
            else: st.warning("La red está vacía.")
        
        with tab3:
            st.header("Composición de las Comunidades")
            if G and G.number_of_nodes() > 0:
                if 'comunidades' not in locals(): # Calcular si no se hizo en la pestaña 1
                    comunidades = nx.community.louvain_communities(G, weight='weight')
                st.info(f"Se detectaron **{len(comunidades)}** comunidades principales.")
                for i, comunidad in enumerate(comunidades):
                    with st.expander(f"Comunidad {i+1} ({len(comunidad)} miembros)"):
                        st.write(sorted(list(comunidad)))
            else: st.warning("La red está vacía.")

    elif pagina_seleccionada in ["Red Autor-Afiliación", "Red Autor-Temática"]:
        if pagina_seleccionada == "Red Autor-Afiliación":
            st.title("🏢 Red Autor-Afiliación"); G = grafos.get('afiliacion'); tipo_nodo_principal = 'Afiliacion'
            color_principal, color_secundario = "#A7D3F7", "#F7A7A6"
        else:
            st.title("🎯 Red Autor-Temática"); G = grafos.get('tematica'); tipo_nodo_principal = 'Tematica'
            color_principal, color_secundario = "#B0F7A6", "#F7A7A6"

        tab1, tab2 = st.tabs(["Exploración del Grafo", "Análisis de Métricas"])
        
        with tab1:
            st.markdown(f"**Instrucciones:** Para evitar la 'bola de pelo', selecciona un(a) **{tipo_nodo_principal}** del menú para ver únicamente a los autores conectados a él/ella.")
            if G and G.number_of_nodes() > 0:
                nodos_principales = sorted([n for n, d in G.nodes(data=True) if d.get('type') == tipo_nodo_principal])
                if not nodos_principales:
                    st.warning(f"No se encontraron nodos de tipo '{tipo_nodo_principal}'.")
                else:
                    seleccion = st.selectbox(f"Filtra la red seleccionando un(a) '{tipo_nodo_principal}':", nodos_principales)
                    if seleccion:
                        vecinos = list(G.neighbors(seleccion))
                        nodos_a_mostrar = vecinos + [seleccion]
                        G_sub = G.subgraph(nodos_a_mostrar)
                        
                        nodes = []
                        for n in G_sub.nodes():
                            if G_sub.nodes[n].get('type') == 'Autor':
                                nodes.append(Node(id=n, label=str(n), size=15, color=color_secundario, title=f"Autor: {n}"))
                            else:
                                nodes.append(Node(id=n, label=str(n), size=25, color=color_principal, title=f"{tipo_nodo_principal}: {n}", shape="database"))
                        edges = [Edge(source=u, target=v) for u, v in G_sub.edges()]
                        agraph(nodes=nodes, edges=edges, config=config_fisicas)
            else: st.warning("La red está vacía.")

        with tab2:
            st.header(f"Ranking de {tipo_nodo_principal}es por Grado")
            st.markdown(f"Un(a) {tipo_nodo_principal.lower()} con un grado alto está conectado/a a muchos autores, indicando su importancia o popularidad en el dataset.")
            if G and G.number_of_nodes() > 0:
                nodos_principales = {n for n, d in G.nodes(data=True) if d.get('type') == tipo_nodo_principal}
                if nodos_principales:
                    grados = {n: G.degree(n) for n in nodos_principales}
                    df_grados = pd.DataFrame(grados.items(), columns=[tipo_nodo_principal, 'Número de Autores Asociados'])
                    st.dataframe(df_grados.sort_values(by='Número de Autores Asociados', ascending=False).head(20))
                else: st.warning(f"No se encontraron nodos de tipo '{tipo_nodo_principal}'.")
            else: st.warning("La red está vacía.")