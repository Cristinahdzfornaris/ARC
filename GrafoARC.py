import os
import fitz
import spacy
import networkx as nx
from pyvis.network import Network

# Cargar el modelo de spaCy
nlp = spacy.load("en_core_web_md")


PDF_FOLDER = "PDF"


INSTITUTION_KEYWORDS = {
    'university', 'institute', 'instituto', 'universidad', 'laboratorio', 'engineering','osservatorio','instituto'
    'computer', 'research', 'school', 'department', 'data', 'science', 'academy','centre','introduction','universita',
    'learning', 'college', 'center', 'national', 'polytechnic', 'email', 'robotics','departamento','maximum','ai','et','AI'
    'intelligent', 'network', 'physics', 'biology', 'faculty', 'foundation','fisica','collaboration','observatory'
}


def extract_text_safe(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            return " ".join(page.get_text() for page in doc[:2] if page.get_text().strip())
    except Exception as e:
        print(f"Error leyendo {pdf_path}: {str(e)}")
        return ""


def extract_authors(text):
    doc = nlp(text)
    authors = set()
    
    for ent in doc.ents:
        if ent.label_ == "PERSON":  
            name = ent.text.strip()
            name_lower = name.lower()
            

            if any(word in name_lower for word in INSTITUTION_KEYWORDS):
                continue


            if len(name.split()) >= 2 and len(name) > 8:
                authors.add(name.title())

    return list(authors)


def build_network():
    G = nx.Graph()
    pdf_count = 0

    for filename in os.listdir(PDF_FOLDER):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(PDF_FOLDER, filename)
        text = extract_text_safe(pdf_path)

        if not text:
            continue

        authors = extract_authors(text)


        for author in authors:
            G.add_node(author)

        for i in range(len(authors)):
            for j in range(i+1, len(authors)):
                G.add_edge(authors[i], authors[j])

        pdf_count += 1
        if pdf_count % 10 == 0:
            print(f"Procesados {pdf_count} PDFs...")

    return G


def visualize_network(G):
    if G.number_of_nodes() == 0:
        print("No hay nodos para visualizar.")
        return

    net = Network(height="1000px", width="100%", bgcolor="#ffffff", font_color="#2d3436")
    net.from_nx(G)

    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "barnesHut": {
                "springLength": 200,
                "springConstant": 0.05,
                "damping": 0.2
            }
        }
    }
    """)

    net.save_graph("red autores.html")
    print("Visualización generada: author_network.html")

if __name__ == "__main__":
    print("Iniciando construcción de red...")
    author_network = build_network()

    print("\nResultados:")
    print(f"- Autores únicos detectados: {author_network.number_of_nodes()}")
    print(f"- Conexiones de coautoría: {author_network.number_of_edges()}")

    print("\nGenerando visualización...")
    visualize_network(author_network)
