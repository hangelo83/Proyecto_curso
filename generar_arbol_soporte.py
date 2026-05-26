import matplotlib.pyplot as plt
import networkx as nx
import sys
import os

# Asegurar que se puede importar desde la carpeta de configuraciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from configuraciones.configuraciones import NODOS_CAPAS, ARISTAS, CONFIG_VISUAL

def crear_grafico_arbol():
    """
    Genera un gráfico en forma de árbol basándose en la configuración definida,
    plasmando la búsqueda de la ruta óptima.
    """
    # Inicializar el grafo dirigido
    G = nx.DiGraph()

    # Agregar nodos con su respectivo atributo de "capa" para el layout
    for nodo, capa in NODOS_CAPAS.items():
        G.add_node(nodo, layer=capa)

    # Agregar aristas con sus atributos (costo y etiqueta)
    for origen, destino, costo, etiqueta in ARISTAS:
        G.add_edge(origen, destino, weight=costo, label=etiqueta)

    # Configurar el tamaño de la figura
    plt.figure(figsize=CONFIG_VISUAL["figsize"])

    # Utilizar un layout multipartito para forzar la estructura de árbol/niveles
    pos = nx.multipartite_layout(G, subset_key="layer", align="horizontal")

    # Modificar ligeramente las posiciones para que parezca un árbol jerárquico de arriba a abajo
    # nx.multipartite_layout orienta de izquierda a derecha por defecto.
    # Rotamos 90 grados para que caiga de arriba hacia abajo
    pos_arbol = {nodo: (coords[1], -coords[0]) for nodo, coords in pos.items()}

    # Asignar colores a los nodos dependiendo de su estado
    node_colors = []
    for nodo in G.nodes():
        if "Éxito" in nodo:
            node_colors.append(CONFIG_VISUAL["node_color_success"])
        elif "Fracaso" or "SERNAC" in nodo and "Reclamo SERNAC" == nodo:
            if "Fracaso" in nodo or "SERNAC" in nodo:
                node_colors.append(CONFIG_VISUAL["node_color_fail"])
            else:
                node_colors.append(CONFIG_VISUAL["node_color_default"])
        else:
            node_colors.append(CONFIG_VISUAL["node_color_default"])

    # Dibujar los nodos
    nx.draw_networkx_nodes(
        G, pos_arbol, 
        node_size=CONFIG_VISUAL["node_size"], 
        node_color=node_colors,
        edgecolors="black"
    )

    # Dibujar las aristas
    nx.draw_networkx_edges(
        G, pos_arbol, 
        arrowstyle="-|>", 
        arrowsize=CONFIG_VISUAL["arrowsize"], 
        edge_color=CONFIG_VISUAL["edge_color"],
        width=2
    )

    # Dibujar las etiquetas de los nodos
    nx.draw_networkx_labels(
        G, pos_arbol, 
        font_size=CONFIG_VISUAL["font_size"], 
        font_weight=CONFIG_VISUAL["font_weight"]
    )

    # Dibujar las etiquetas de las aristas (Costo y Descripción)
    edge_labels = nx.get_edge_attributes(G, "label")
    nx.draw_networkx_edge_labels(
        G, pos_arbol, 
        edge_labels=edge_labels, 
        font_size=9, 
        font_color="red",
        label_pos=0.5
    )

    # Título y ajustes finales
    plt.title("Modelo de Búsqueda A* - Optimización de Atención al Cliente", fontsize=16, fontweight="bold")
    plt.axis("off") # Ocultar ejes
    plt.tight_layout()

    # Guardar la imagen generada
    output_path = "arbol_decision_atencion.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✅ Gráfico generado exitosamente y guardado como: {output_path}")
    
    # Mostrar el gráfico en pantalla
    plt.show()

if __name__ == "__main__":
    crear_grafico_arbol()
