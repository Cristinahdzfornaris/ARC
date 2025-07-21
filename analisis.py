import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from networkx.algorithms import community as nx_comm

def construir_red(datos, tipo_red):
    """Construye un grafo de NetworkX a partir de los datos."""
    G = nx.Graph()
    if tipo_red == "Autor-Autor":
        for _, row in datos.iterrows():
            autores = row["autores"]
            for i in range(len(autores)):
                for j in range(i + 1, len(autores)):
                    G.add_edge(autores[i], autores[j])
    elif tipo_red == "Autor-Institución":
        for _, row in datos.iterrows():
            autores = row["autores"]
            instituciones = row["instituciones"]
            for autor in autores:
                for institucion in instituciones:
                    G.add_edge(autor, institucion)
    return G

def analizar_red(datos, tipo_red):
    """Realiza el análisis de la red y muestra los resultados."""
    if datos.empty:
        st.warning("No se pudieron extraer datos de los PDFs. Intenta con otros archivos.")
        return

    G = construir_red(datos, tipo_red)

    if G.number_of_nodes() == 0:
        st.warning("La red está vacía. No se pueden realizar análisis.")
        return

    st.header("Análisis de la Red")

    # Visualización del grafo
    st.subheader("Visualización del Grafo")
    fig, ax = plt.subplots(figsize=(12, 12))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=1500,
            edge_color='gray', font_size=10, ax=ax)
    st.pyplot(fig)

    # Métricas de Centralidad
    st.subheader("Métricas de Centralidad")
    degree_centrality = nx.degree_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)

    df_centrality = pd.DataFrame({
        "Nodo": list(G.nodes()),
        "Centralidad de Grado": list(degree_centrality.values()),
        "Closeness": list(closeness_centrality.values()),
        "Betweenness": list(betweenness_centrality.values())
    }).sort_values(by="Centralidad de Grado", ascending=False)

    st.dataframe(df_centrality)

    # Detección de Comunidades
    st.subheader("Detección de Comunidades")
    communities = nx_comm.greedy_modularity_communities(G)
    st.write(f"Número de comunidades detectadas: {len(communities)}")

    community_dict = {}
    for i, community in enumerate(communities):
        for node in community:
            community_dict[node] = i

    node_color = [community_dict.get(node) for node in G.nodes()]

    fig_comm, ax_comm = plt.subplots(figsize=(12, 12))
    nx.draw(G, pos, with_labels=True, node_color=node_color, node_size=1500,
            edge_color='gray', font_size=10, cmap=plt.cm.viridis, ax=ax_comm)
    st.pyplot(fig_comm)


    # Nodos Influyentes y Puentes
    st.subheader("Nodos Influyentes y Puentes")
    st.write("**Nodos más influyentes (mayor centralidad de grado):**")
    st.write(df_centrality.head())

    st.write("**Nodos puente (mayor centralidad de intermediación - betweenness):**")
    df_betweenness = df_centrality.sort_values(by="Betweenness", ascending=False)
    st.write(df_betweenness.head())