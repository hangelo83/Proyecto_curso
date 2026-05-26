import plotly.graph_objects as go
import networkx as nx
import numpy as np
import sys
import os
import webbrowser

# Asegurar que se puede importar desde la carpeta de configuraciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from configuraciones.configuraciones import NODOS_CAPAS, ARISTAS, CONFIG_VISUAL

def layout_cono(G):
    """
    Calcula posiciones 3D para el grafo en forma de cono jerárquico.
    El nivel superior está en la punta, y los niveles inferiores se abren en círculo.
    """
    pos = {}
    capas = {}
    for node, data in G.nodes(data=True):
        capa = data.get('layer', 0)
        if capa not in capas:
            capas[capa] = []
        capas[capa].append(node)
        
    for capa, nodos in capas.items():
        z = -capa * 2.5  # Bajamos en el eje Z por cada capa
        n = len(nodos)
        if n == 1:
            pos[nodos[0]] = (0, 0, z)
        else:
            # Distribución circular para nodos en el mismo nivel
            theta = np.linspace(0, 2*np.pi, n, endpoint=False)
            r = capa * 2.0  # El radio del círculo aumenta mientras más abajo estamos
            for i, nodo in enumerate(nodos):
                x = r * np.cos(theta[i])
                y = r * np.sin(theta[i])
                pos[nodo] = (x, y, z)
    return pos

def generar_grafico_3d():
    # Inicializar grafo
    G = nx.DiGraph()

    # Agregar nodos y aristas desde la configuración centralizada
    for nodo, capa in NODOS_CAPAS.items():
        G.add_node(nodo, layer=capa)

    for origen, destino, costo, etiqueta in ARISTAS:
        G.add_edge(origen, destino, weight=costo, label=etiqueta)

    # Calcular layout 3D
    pos_3d = layout_cono(G)
    
    # Calcular el costo acumulado g(n) y la ruta desde el inicio usando Dijkstra (lógica base de A*)
    inicio = "Llamada Entrante"
    caminos = nx.single_source_dijkstra_path(G, inicio, weight='weight')
    costos = nx.single_source_dijkstra_path_length(G, inicio, weight='weight')

    # Preparar datos para las aristas (líneas) en Plotly
    edge_x = []
    edge_y = []
    edge_z = []
    for edge in G.edges():
        x0, y0, z0 = pos_3d[edge[0]]
        x1, y1, z1 = pos_3d[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    trace_edges = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(color=CONFIG_VISUAL["edge_color"], width=4),
        hoverinfo='none',
        name='Saltos de Atención'
    )

    # Preparar datos para los nodos y la interactividad (hover con suma de costos)
    node_x = []
    node_y = []
    node_z = []
    hover_texts = []
    node_colors = []
    text_labels = []

    for nodo in G.nodes():
        x, y, z = pos_3d[nodo]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        text_labels.append(nodo)
        
        # Lógica interactiva: Construir el texto flotante con la suma total y el camino
        camino_str = " ➔ ".join(caminos.get(nodo, [nodo]))
        costo_total = costos.get(nodo, 0)
        
        hover_text = (
            f"<b>{nodo}</b><br><br>"
            f"💰 <b>Costo Acumulado Total:</b> {costo_total}<br>"
            f"🛣️ <b>Camino Óptimo hasta aquí:</b><br>{camino_str}"
        )
        hover_texts.append(hover_text)
        
        # Colores según tipo de nodo
        if "Éxito" in nodo:
            node_colors.append(CONFIG_VISUAL["node_color_success"])
        elif "Fracaso" in nodo or "SERNAC" in nodo:
            node_colors.append(CONFIG_VISUAL["node_color_fail"])
        else:
            node_colors.append(CONFIG_VISUAL["node_color_default"])

    trace_nodes = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        marker=dict(
            size=15,
            color=node_colors,
            line=dict(width=2, color='white')
        ),
        text=text_labels,
        textposition="top center",
        hoverinfo='text',
        hovertext=hover_texts,
        name='Estados de Conversación'
    )

    # Configuración de la escena 3D y renderizado
    fig = go.Figure(data=[trace_edges, trace_nodes])
    fig.update_layout(
        title="Modelo de Búsqueda - Árbol de Decisiones 3D Interactivo",
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, title=''),
            yaxis=dict(showbackground=False, showticklabels=False, title=''),
            zaxis=dict(showbackground=False, showticklabels=False, title='')
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    # Guardar como HTML interactivo
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arbol_decision_atencion_3D.html")
    fig.write_html(html_path)
    print(f"Grafico 3D interactivo generado con exito en: {html_path}")
    
    # Intentar abrir automáticamente en el navegador web predeterminado
    webbrowser.open(f"file://{html_path}")

if __name__ == "__main__":
    generar_grafico_3d()
