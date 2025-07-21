

import re

STOP_WORDS_ES = [
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con", "una",
    "su", "al", "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este", "ha", "me", "si", "sin",
    "sobre", "este", "entre", "cuando", "también", "era", "muy", "hasta", "desde", "nos", "mi",
    "qué", "e", "son", "fue", "ser", "es", "han", "está", "estos", "estas"
]
def normalizar_nombre(nombre):
    """
    Limpia y estandariza un nombre de autor o institución, manejando correctamente
    múltiples apellidos o nombres en formato 'Apellidos, Nombres'.
    Ej: "García Márquez, Gabriel J." -> "gabriel j garcia marquez"
    """
    if not isinstance(nombre, str) or not nombre:
        return ""


    nombre = nombre.lower().strip()
    

    nombre = nombre.replace('.', '').replace('-', ' ')
    
  
    if ',' in nombre:
        partes = nombre.split(',', 1) 
        if len(partes) == 2:
            nombres = partes[1].strip()
            apellidos = partes[0].strip()
          
            nombre = f"{nombres} {apellidos}"
    
 
    nombre = re.sub(r'[^a-z\s]', '', nombre)
    
 
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    
    return nombre
    
    
import streamlit as st
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
def crear_red_temas(df):
    """
    Crea una red donde los nodos son palabras clave (temas) y se conectan
    si aparecen juntas en el mismo artículo. El peso de la arista indica
    cuántas veces han co-ocurrido.
    """
    G = nx.Graph()
    pesos_aristas = {}
    
    for _, row in df.iterrows():
        temas = row.get("palabras_clave", [])
        if isinstance(temas, list) and len(temas) > 1:
           
            temas_normalizados = list(set([tema.lower().strip() for tema in temas if tema]))
            
            for i in range(len(temas_normalizados)):
                
                G.add_node(temas_normalizados[i])
                for j in range(i + 1, len(temas_normalizados)):
                    
                    nodo1, nodo2 = sorted((temas_normalizados[i], temas_normalizados[j]))
                    if nodo1 != nodo2:
                        arista = (nodo1, nodo2)
                        pesos_aristas[arista] = pesos_aristas.get(arista, 0) + 1
                        
    # Añadir las aristas con sus pesos al grafo
    for arista, peso in pesos_aristas.items():
        G.add_edge(arista[0], arista[1], weight=peso)
        
    return G
def crear_red_autor_autor(df):
    G = nx.Graph()
    

    for _, row in df.iterrows():
        autores = row.get("autores", [])
        if isinstance(autores, list) and len(autores) > 1:
            # 1. Normalizamos la lista de autores
            autores_normalizados = [normalizar_nombre(autor) for autor in autores]
            

            autores_unicos = list(set(autores_normalizados))
            
          
            for i in range(len(autores_unicos)):
                for j in range(i + 1, len(autores_unicos)):
                  
                    if autores_unicos[i] and autores_unicos[j]:
                        G.add_edge(autores_unicos[i], autores_unicos[j])
    return G


def crear_red_autor_institucion(df):
    """Crea una red bipartita que conecta autores con sus instituciones."""
    B = nx.Graph()
    for _, row in df.iterrows():
        autores = row.get("autores", [])
        instituciones = row.get("afiliaciones", [])
        
        if autores and instituciones:
            autores_norm = [normalizar_nombre(a) for a in autores if a]
            instituciones_norm = [normalizar_nombre(i) for i in instituciones if i]
            
            
            for autor in autores_norm:
                B.add_node(autor, bipartite=0, tipo='Autor')
            for inst in instituciones_norm:
                B.add_node(inst, bipartite=1, tipo='Institución')
            
            
            for autor in autores_norm:
                for inst in instituciones_norm:
                    B.add_edge(autor, inst)
    return B


def visualizar_red_interactiva(G):
    if not G.nodes:
        st.warning("La red está vacía. No hay nada que visualizar.")
        return

    pos = nx.spring_layout(G, k=0.5, iterations=50) 

    # Nodos
    node_x, node_y = [], []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>Grado: {G.degree(node)}")
    
    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text,
                            textposition="top center",
                            hoverinfo='text',
                            marker=dict(showscale=True, colorscale='YlGnBu', size=10,
                                        colorbar=dict(thickness=15, title='Conexiones', xanchor='left', titleside='right')))
    # Aristas
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'),
                            hoverinfo='none', mode='lines')

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Red de Coautoría Interactiva', showlegend=False, hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    st.plotly_chart(fig, use_container_width=True)

def mostrar_metricas_centralidad(G):
    if not G.nodes:
        st.warning("La red está vacía. No se pueden calcular métricas.")
        return

    dc = nx.degree_centrality(G)
    bc = nx.betweenness_centrality(G)
    cc = nx.closeness_centrality(G)

    df_metrics = pd.DataFrame({
        'Nodo': list(G.nodes()),
        'Grado': [G.degree(n) for n in G.nodes()],
        'Centralidad de Grado': [dc.get(n, 0) for n in G.nodes()],
        'Intermediación (Betweenness)': [bc.get(n, 0) for n in G.nodes()],
        'Cercanía (Closeness)': [cc.get(n, 0) for n in G.nodes()],
    }).sort_values('Grado', ascending=False).reset_index(drop=True)

    st.dataframe(df_metrics)