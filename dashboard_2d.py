import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import networkx as nx
import sys
import os
import webbrowser
from threading import Timer

# Asegurar que se puede importar la configuración central
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from configuraciones.configuraciones import NODOS_CAPAS, ARISTAS, CONFIG_VISUAL, DESCRIPCIONES_NODOS

app = dash.Dash(__name__)
server = app.server

# Construir grafo y cargar parámetros centralizados
G = nx.DiGraph()
for nodo, capa in NODOS_CAPAS.items():
    G.add_node(nodo, layer=capa)
for origen, destino, costo, etiqueta in ARISTAS:
    G.add_edge(origen, destino, weight=costo, label=etiqueta)

# Mapeo de Nodos a sus correspondientes Áreas de Negocio Principales
MAPEO_NODOS_AREAS = {
    # Facturación
    "Facturación": "Facturación",
    "Verificar Contrato": "Facturación",
    "Revisar Historial": "Facturación",
    "Tramitar Devolución": "Facturación",
    "Explicar Cobro": "Facturación",
    
    # Técnicos
    "Técnicos": "Técnicos",
    "Verificar Estado Pago": "Técnicos",
    "Soporte Nivel 1": "Técnicos",
    "Corte de servicio por no pago": "Técnicos",
    "Reinicio Remoto": "Técnicos",
    "Soporte Nivel 2": "Técnicos",
    "Derivar a Terreno": "Técnicos",
    
    # Ventas
    "Ventas": "Ventas",
    "Perfilamiento": "Ventas",
    "Oferta Básica": "Ventas",
    "Oferta Premium": "Ventas",
    "Venta no concretada": "Ventas",
    "Cliente nuevo (mejor caso de exito)": "Ventas",
    "Venta de equipo o accesorio (exito medio)": "Ventas",
    
    # Postventa
    "Postventa": "Postventa",
    "Negociar Descuento": "Postventa",
    "Procesar Baja": "Postventa",
    "Nuevo plan": "Postventa",
    "Recambio de equipo": "Postventa"
}

# Coordenadas perfectas diseñadas con una desalineación horizontal estratégica para evitar solapamientos físicos
COORDENADAS_MANUALES = {
    "Llamada Entrante": (0, 0),
    
    # Capa 1 (x = 22) - Muy espaciados
    "Facturación": (22, 25),
    "Técnicos": (22, 8),
    "Ventas": (22, -8),
    "Postventa": (22, -25),
    
    # Capa 2 (x = 46 con desalineación estratégica para romper verticalidades en el flujo de Soporte)
    "Verificar Contrato": (46, 30),
    "Revisar Historial": (46, 15),
    "Soporte Nivel 1": (48, 0),             # Desplazado a la derecha
    "Verificar Estado Pago": (38, -15),      # Desplazado a la izquierda para que la conexión a Soporte Nivel 1 sea diagonal
    "Perfilamiento": (46, -30),
    "Negociar Descuento": (46, -45),
    
    # Capa 3 (Desalineación horizontal avanzada en X para erradicar solapamientos y líneas verticales puras)
    # Sub-columna Soporte / Facturación
    "Tramitar Devolución": (69, 35),
    "Explicar Cobro": (69, 20),
    "Corte de servicio por no pago": (56, -20), # Posición de pre-error de morosidad diagonal
    "Reinicio Remoto": (65, 5),              # Desplazado a la izquierda
    "Soporte Nivel 2": (73, -10),            # Desplazado a la derecha
    "Derivar a Terreno": (65, -25),          # Desplazado a la izquierda para crear diagonales desde Soporte Nivel 2
    
    # Sub-columna Comercial / Ventas / Postventa
    "Oferta Básica": (75, 30),               # Desplazado a la izquierda
    "Oferta Premium": (83, 15),              # Desplazado a la derecha
    "Cliente nuevo (mejor caso de exito)": (85, 0), # Desplazado a la derecha (destino de Oferta Premium)
    "Venta de equipo o accesorio (exito medio)": (73, -15), # Desplazado a la izquierda (destino de Oferta Básica)
    "Nuevo plan": (80, -30),
    "Recambio de equipo": (80, -45),
    "Venta no concretada": (78, -60),        # Centro-izquierda, recibe de ambas Ofertas creando hermosas diagonales
    "Procesar Baja": (80, -75),
    
    # Capa 4 (x = 100) - Cierres finales absolutos alineados y muy holgados
    "Éxito Comercial (Venta)": (100, 30),
    "Éxito (Contención)": (100, 10),
    "Fracaso (Fuga)": (100, -10),
    "Escalamiento SERNAC": (100, -40)
}

def layout_arbol_2d(G):
    return {nodo: COORDENADAS_MANUALES.get(nodo, (0, 0)) for nodo in G.nodes()}

pos_2d = layout_arbol_2d(G)

# Ruta inicial por defecto: Rama de Facturación
camino_inicial_facturacion = [
    "Llamada Entrante",
    "Facturación",
    "Revisar Historial",
    "Explicar Cobro",
    "Éxito (Contención)"
]

# Ruta por defecto al abrir la página: Rama Técnica óptima (reinicio remoto)
camino_inicial_tecnico = [
    "Llamada Entrante",
    "Técnicos",
    "Soporte Nivel 1",
    "Reinicio Remoto",
    "Éxito (Contención)"
]

def calcular_costo_camino(camino):
    costo = 0
    for i in range(len(camino) - 1):
        if G.has_edge(camino[i], camino[i+1]):
            costo += G[camino[i]][camino[i+1]]['weight']
    return costo

def crear_figura(caminos_verde=None, caminos_rojo=None, caminos_amarillo=None, caminos_naranja=None):
    # Inicialización por defecto en el inicio de la app
    if caminos_verde is None and caminos_rojo is None and caminos_amarillo is None and caminos_naranja is None:
        caminos_naranja = [camino_inicial_tecnico]

    color_nodos = {}
    color_aristas = {}
    
    HEX_VERDE = '#2b9348'
    HEX_ROJO = '#d90429'
    HEX_AMARILLO = '#ffb703'
    HEX_NARANJA = '#fb8500'

    # Precedencia de pintado: Amarillo ➔ Rojo ➔ Verde (Verde brilla con máxima prioridad)
    if caminos_naranja:
        for c in caminos_naranja:
            for n in c:
                color_nodos[n] = HEX_NARANJA
            for i in range(len(c) - 1):
                color_aristas[(c[i], c[i+1])] = HEX_NARANJA

    if caminos_amarillo:
        for c in caminos_amarillo:
            for n in c:
                color_nodos[n] = HEX_AMARILLO
            for i in range(len(c) - 1):
                color_aristas[(c[i], c[i+1])] = HEX_AMARILLO

    if caminos_rojo:
        for c in caminos_rojo:
            for n in c:
                color_nodos[n] = HEX_ROJO
            for i in range(len(c) - 1):
                color_aristas[(c[i], c[i+1])] = HEX_ROJO

    if caminos_verde:
        for c in caminos_verde:
            for n in c:
                color_nodos[n] = HEX_VERDE
            for i in range(len(c) - 1):
                color_aristas[(c[i], c[i+1])] = HEX_VERDE

    edge_traces = []
    mid_x_act, mid_y_act, mid_text_act = [], [], []
    mid_x_ina, mid_y_ina, mid_text_ina = [], [], []

    # 1. Trazado de Aristas
    for edge in G.edges(data=True):
        origen = edge[0]
        destino = edge[1]
        costo = edge[2]['weight']
        etiqueta = edge[2]['label']

        x0, y0 = pos_2d[origen]
        x1, y1 = pos_2d[destino]

        mx, my = (x0+x1)/2, (y0+y1)/2
        es_activa = (origen, destino) in color_aristas
        # Desplazamiento leve de los textos del peso para evitar que solapen
        if es_activa:
            mid_x_act.append(mx)
            mid_y_act.append(my + 1.2)
            mid_text_act.append(f"<b>{costo}</b>")
        else:
            mid_x_ina.append(mx)
            mid_y_ina.append(my + 1.2)
            mid_text_ina.append(f"{costo}")
        
        # Detección de arista cruzada inter-área
        es_cruzada = (MAPEO_NODOS_AREAS.get(origen) != MAPEO_NODOS_AREAS.get(destino) and 
                      MAPEO_NODOS_AREAS.get(origen) is not None and 
                      MAPEO_NODOS_AREAS.get(destino) is not None)
        
        color_arista = color_aristas.get((origen, destino), None)
        es_ruta = color_arista is not None
        
        if es_ruta:
            if es_cruzada:
                color_final = "#fb8500"  # Naranja Vibrante Premium
                ancho_arista = 8.5       # Más grueso para destacar visualmente
            else:
                color_final = color_arista
                ancho_arista = 7.5
        else:
            if es_cruzada:
                color_final = "#cfd8dc"  # Gris azulado sutil para denotar el enganche latente
                ancho_arista = 2.0
            else:
                color_final = "#e9ecef"
                ancho_arista = 1.5
        
        prefijo_hover = "⚡ <b>[ENGANCHE INTER-ÁREA]</b><br>" if es_cruzada else ""
        hover_txt = f"{prefijo_hover}<b>{origen} ➔ {destino}</b><br>Acción: {etiqueta}<br>Costo: {costo}"
        
        trace = go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines',
            line=dict(color=color_final, width=ancho_arista),
            hoverinfo='text',
            hovertext=hover_txt,
            showlegend=False
        )
        edge_traces.append(trace)

    # 2. Pesos/Costos en medio de aristas — activos visibles, inactivos casi invisibles
    trace_weights_act = go.Scatter(
        x=mid_x_act, y=mid_y_act,
        mode='text',
        text=mid_text_act,
        textposition='middle center',
        textfont=dict(color='black', size=13, family='Arial Black'),
        hoverinfo='none',
        showlegend=False
    )
    trace_weights_ina = go.Scatter(
        x=mid_x_ina, y=mid_y_ina,
        mode='text',
        text=mid_text_ina,
        textposition='middle center',
        textfont=dict(color='rgba(180,180,180,0.35)', size=11, family='Arial'),
        hoverinfo='none',
        showlegend=False
    )

    # 3. Nodos 2D
    node_x, node_y = [], []
    hover_texts, node_colors, text_labels, text_colors, border_colors, border_widths = [], [], [], [], [], []

    for nodo in G.nodes():
        x, y = pos_2d[nodo]
        node_x.append(x)
        node_y.append(y)
        text_labels.append(nodo)
        
        descripcion = DESCRIPCIONES_NODOS.get(nodo, "Sin descripción disponible.")
        hover_text = f"<b>{nodo}</b><br><i>{descripcion}</i><br><br><i>(Clic para aislar y analizar esta rama)</i>"
        hover_texts.append(hover_text)
        
        es_final_exito_comercial = (nodo == "Éxito Comercial (Venta)")
        es_final_exito_contencion = (nodo == "Éxito (Contención)")
        es_final_error = (nodo in ["Fracaso (Fuga)", "Escalamiento SERNAC"])
        
        color_nodo = color_nodos.get(nodo, None)
        es_resaltado = color_nodo is not None
        
        if es_resaltado:
            node_colors.append(color_nodo)
            text_colors.append("black")
            border_colors.append("black")
            border_widths.append(2.5)
        else:
            if es_final_exito_comercial:
                node_colors.append("#38b000") # Verde vibrante
                border_colors.append("#2b9348")
            elif es_final_exito_contencion:
                node_colors.append("#48cae4") # Azul suave / Contención
                border_colors.append("#00b4d8")
            elif es_final_error:
                node_colors.append("#fcd5ce") # Rojo suave
                border_colors.append("#fec89a")
            else:
                node_colors.append("#f8f9fa")
                border_colors.append("#dee2e6")
            text_colors.append("#6c757d")
            border_widths.append(1.5)

    trace_nodes = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(
            size=35, # Círculos más pequeños y estilizados para erradicar traslapes por completo
            color=node_colors,
            line=dict(width=border_widths, color=border_colors)
        ),
        text=text_labels,
        textposition="top center",
        textfont=dict(size=12, color=text_colors, family='Arial Black'),
        hoverinfo='text',
        hovertext=hover_texts,
        showlegend=False
    )

    fig = go.Figure(data=edge_traces + [trace_weights_ina, trace_weights_act, trace_nodes])
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=40, r=40, b=40, t=40),
        clickmode='event+select',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='closest'
    )
    return fig

# Diseño moderno responsivo
app.layout = html.Div([
    html.Div([
        html.H1("Mesa de ayuda soporte en linea", 
                style={'color': '#1d3557', 'margin': '0', 'fontSize': '28px', 'fontWeight': '800'}),
        html.P("Optimización de la atención al cliente con inteligencia artificial", 
                style={'color': '#457b9d', 'margin': '5px 0 0 0', 'fontSize': '16px', 'fontStyle': 'italic'}),
        html.P("Este simulador interactivo modela el flujo de decisiones en una mesa de ayuda en línea utilizando el algoritmo de búsqueda inteligente A*. El sistema traza la ruta óptima de atención priorizando la resolución ágil y de menor esfuerzo para el cliente, maximizando la tasa de éxito comercial y de soporte, y previniendo de forma proactiva desvíos ineficientes hacia la fuga de clientes (Fracaso) o reclamos formales (Escalamiento SERNAC).",
                style={'color': '#6c757d', 'margin': '12px auto 0 auto', 'fontSize': '14px', 'maxWidth': '75%', 'lineHeight': '1.6', 'fontWeight': '500'}),
        html.P("Análisis de Flujo Técnico",
                style={'color': '#1d3557', 'margin': '14px auto 4px auto', 'fontSize': '15px', 'maxWidth': '75%', 'fontWeight': '700', 'letterSpacing': '0.5px', 'textTransform': 'uppercase'}),
        html.P("El flujo prioriza el reinicio remoto como acción estratégica antes de derivar a servicio técnico en terreno. Esta decisión responde a una doble arista de riesgo: despachar un técnico sin agotar las opciones remotas eleva el costo operativo y el tiempo de resolución, y si el técnico llega sin resolver el problema, el cliente enfrenta una experiencia fallida que incrementa la probabilidad de fuga o de escalar a un reclamo formal ante SERNAC. Las aristas intermedias del árbol —diagnóstico inicial, verificación de señal, reinicio remoto y confirmación de servicio— representan los puntos de control que el algoritmo A* evalúa para construir el camino de menor costo total. Puntos clave: (1) el reinicio remoto tiene costo operativo bajo y alta tasa de resolución en primer contacto; (2) la derivación a terreno solo se activa cuando las acciones remotas han sido agotadas; (3) el sistema pondera el riesgo de Fracaso y Escalamiento SERNAC como nodos de mayor costo, orientando siempre la ruta hacia la resolución efectiva y la retención del cliente.",
                style={'color': '#457b9d', 'margin': '10px auto 0 auto', 'fontSize': '13px', 'maxWidth': '75%', 'lineHeight': '1.7', 'fontWeight': '400', 'fontStyle': 'italic', 'borderTop': '1px solid #e9ecef', 'paddingTop': '10px'})
    ], style={
        'textAlign': 'center', 
        'fontFamily': 'Outfit, Inter, sans-serif', 
        'padding': '20px 10px', 
        'backgroundColor': '#ffffff',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.05)',
        'borderRadius': '0 0 16px 16px',
        'marginBottom': '20px'
    }),
    
    # Contenedor de Información Superior
    html.Div(id='output-clic', style={
        'fontFamily': 'Outfit, Inter, sans-serif', 
        'padding': '20px', 
        'backgroundColor': '#ffffff', 
        'borderRadius': '12px',
        'width': '85%', 
        'margin': '0 auto 20px auto', 
        'minHeight': '80px', 
        'boxShadow': '0 4px 12px rgba(0,0,0,0.08)',
        'borderLeft': '8px solid #fb8500',
        'transition': 'all 0.3s ease'
    }),
    
    # Gráfico del Árbol 2D
    html.Div([
        dcc.Graph(
            id='grafico-2d',
            figure=crear_figura(),
            style={'height': '72vh', 'width': '100%'}
        )
    ], style={
        'backgroundColor': '#ffffff', 
        'borderRadius': '16px', 
        'width': '95%', 
        'margin': '0 auto', 
        'boxShadow': '0 4px 20px rgba(0,0,0,0.05)',
        'padding': '15px'
    })
], style={'backgroundColor': '#f1faee', 'minHeight': '100vh', 'margin': '-8px', 'paddingBottom': '30px'})

@app.callback(
    [Output('grafico-2d', 'figure'),
     Output('output-clic', 'children'),
     Output('output-clic', 'style')],
    [Input('grafico-2d', 'clickData')]
)
def actualizar_grafo(clickData):
    # Si no hay clic, iniciar con la rama Técnica por defecto
    if clickData is None:
        costo_init = calcular_costo_camino(camino_inicial_tecnico)
        ruta_str = " ➔ ".join(camino_inicial_tecnico)

        mensaje_bienvenida = html.Div([
            html.Div([
                html.Span("Selecciona cualquier nodo del árbol para aislar y analizar su rama correspondiente.",
                          style={'fontWeight': 'bold', 'fontSize': '18px', 'color': '#1d3557'}),
            ], style={'marginBottom': '10px'}),
            html.Div([
                html.Strong("Rama Activa por Defecto (Técnicos):", style={'color': '#fb8500'}),
                html.Span(f" {ruta_str}", style={'color': '#1d3557', 'marginLeft': '10px', 'fontWeight': '600'}),
                html.Span(f" 💵 Costo Total: {costo_init}", style={'color': '#e63946', 'fontWeight': 'bold', 'marginLeft': '15px'})
            ])
        ])

        style_caja = {
            'fontFamily': 'Outfit, Inter, sans-serif',
            'padding': '20px',
            'backgroundColor': '#ffffff',
            'borderRadius': '12px',
            'width': '85%',
            'margin': '0 auto 20px auto',
            'minHeight': '80px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.08)',
            'borderLeft': '8px solid #fb8500'
        }
        return crear_figura(caminos_naranja=[camino_inicial_tecnico]), mensaje_bienvenida, style_caja
    
    try:
        punto = clickData['points'][0]
        nodo_sel = punto.get('text', None)
        
        if not nodo_sel or "<b>" in str(nodo_sel):
            return dash.no_update, dash.no_update, dash.no_update
            
        caminos_destacados = []
        is_default_view = False
        
        es_exito = nodo_sel in ["Éxito Comercial (Venta)", "Éxito (Contención)"]
        es_error = nodo_sel in ["Fracaso (Fuga)", "Escalamiento SERNAC"]
        
        # 1. CASO NODO RAÍZ ("Llamada Entrante"): Volver a Facturación por defecto
        if nodo_sel == "Llamada Entrante":
            caminos_destacados = [camino_inicial_facturacion]
            is_default_view = True
            
        # 2. CASO ÉXITO (Ticket Cerrado): Todas las rutas puras válidas hacia el éxito, para clasificarse por valor comercial
        elif es_exito:
            areas = ["Facturación", "Técnicos", "Ventas", "Postventa"]
            for area in areas:
                if area in G:
                    caminos_area = list(nx.all_simple_paths(G, area, nodo_sel))
                    if caminos_area:
                        for p in caminos_area:
                            camino_completo = ["Llamada Entrante"] + p
                            
                            # Filtro de pureza de rama
                            es_valido = True
                            for nodo_int in camino_completo[1:-1]:
                                if MAPEO_NODOS_AREAS.get(nodo_int) != area:
                                    es_valido = False
                                    break
                                    
                            if es_valido:
                                caminos_destacados.append(camino_completo)
                            
        # 3. CASO CASOS DE ERROR/FRACASO: Rutas de error coherentes por rama
        elif es_error:
            todos_caminos = list(nx.all_simple_paths(G, "Llamada Entrante", nodo_sel))
            for c in todos_caminos:
                if len(c) > 2:
                    area_inicio = c[1]
                    # Filtro de pureza de rama
                    es_valido = True
                    for nodo_int in c[1:-1]:
                        if MAPEO_NODOS_AREAS.get(nodo_int) != area_inicio:
                            es_valido = False
                            break
                    if es_valido:
                        caminos_destacados.append(c)
                else:
                    caminos_destacados.append(c)
            
        # 4. CASO NODO INTERMEDIO O ÁREA PRINCIPAL: Filtrado inteligente (Pureza hacia atrás, libertad hacia adelante)
        else:
            # Función auxiliar para contar saltos inter-área en un camino completo
            def contar_saltos_interarea(camino):
                saltos = 0
                for i in range(len(camino) - 1):
                    origen, destino = camino[i], camino[i+1]
                    area_orig = MAPEO_NODOS_AREAS.get(origen)
                    area_dest = MAPEO_NODOS_AREAS.get(destino)
                    if area_orig is not None and area_dest is not None and area_orig != area_dest:
                        saltos += 1
                return saltos

            # Encontrar el área de negocio principal para aislar estrictamente
            area_principal = MAPEO_NODOS_AREAS.get(nodo_sel, None)
            
            if area_principal:
                # Caminos desde el inicio al nodo intermedio
                caminos_izq = list(nx.all_simple_paths(G, "Llamada Entrante", nodo_sel))
                
                # Filtrar caminos de la izquierda de forma inteligente:
                # - Aceptar pureza estricta (todos los nodos intermedios pertenecen al área principal del nodo seleccionado)
                # - O si el camino de la izquierda representa un salto directo inter-área de entrada corta (longitud <= 3)
                caminos_izq_validos = []
                for c_izq in caminos_izq:
                    es_izq_valido = True
                    for nodo_int in c_izq[1:-1]:
                        if MAPEO_NODOS_AREAS.get(nodo_int) != area_principal:
                            es_izq_valido = False
                            break
                    if not es_izq_valido and len(c_izq) <= 3:
                        # Si el origen es Postventa, permitimos el enganche de entrada
                        if c_izq[1] == "Postventa" and area_principal == "Técnicos":
                            es_izq_valido = True
                    if es_izq_valido:
                        caminos_izq_validos.append(c_izq)
                
                # Caminos desde el nodo intermedio a los extremos finales lógicos (Capa 4)
                finales = ["Éxito Comercial (Venta)", "Éxito (Contención)", "Fracaso (Fuga)", "Escalamiento SERNAC"]
                caminos_der = []
                for F in finales:
                    if F in G:
                        caminos_der.extend(list(nx.all_simple_paths(G, nodo_sel, F)))
                
                # Combinar y aplicar filtrado inteligente adaptativo
                for c_izq in caminos_izq_validos:
                    # Límite dinámico de saltos:
                    # - 1 salto si el área consultada es Postventa o si el flujo de entrada proviene de Postventa
                    # - 0 saltos para aislar estrictamente las ramas de Facturación, Técnicos y Ventas
                    es_flujo_desde_postventa = (len(c_izq) > 1 and c_izq[1] == "Postventa")
                    limite_saltos = 1 if (es_flujo_desde_postventa or area_principal == "Postventa") else 0
                    
                    for c_der in caminos_der:
                        camino_completo = c_izq + c_der[1:]
                        if contar_saltos_interarea(camino_completo) <= limite_saltos:
                            caminos_destacados.append(camino_completo)
            else:
                caminos_destacados = [[nodo_sel]]

        # Función para evaluar la prioridad de negocio (a mayor retorno/valor comercial, mejor)
        def evaluar_prioridad_negocio(camino, costo_cam):
            if camino[-1] == "Escalamiento SERNAC":
                return -100 - costo_cam
            if camino[-1] == "Fracaso (Fuga)":
                return -50 - costo_cam
                
            if "Cliente nuevo (mejor caso de exito)" in camino:
                return 1000 - costo_cam   # Máxima prioridad comercial
            if "Nuevo plan" in camino or "Recambio de equipo" in camino:
                return 800 - costo_cam    # Prioridad alta (retención / evitar fuga)
            if "Venta de equipo o accesorio (exito medio)" in camino:
                return 600 - costo_cam    # Prioridad media (venta cruzada)
                
            return 300 - costo_cam        # Prioridad básica (soporte técnico / facturación administrativa)

        # Calcular costos y clasificar caminos según su prioridad de negocio
        caminos_con_costo = []
        for c in caminos_destacados:
            costo = calcular_costo_camino(c)
            prioridad = evaluar_prioridad_negocio(c, costo)
            caminos_con_costo.append((c, costo, prioridad))
            
        # Ordenar por prioridad de negocio descendente (el de mayor prioridad comercial va primero)
        caminos_con_costo.sort(key=lambda x: x[2], reverse=True)
        
        # Si por alguna razón no se encontraron caminos, usar por defecto el nodo solo
        if not caminos_con_costo:
            caminos_con_costo = [([nodo_sel], 0, 0)]
            
        # Determinar de forma dinámica si todos los caminos terminan en fracaso/error (por ejemplo, Procesar Baja, Venta no concretada)
        es_camino_error_puro = caminos_destacados and all(c[-1] in ["Fracaso (Fuga)", "Escalamiento SERNAC"] for c in caminos_destacados)

        # CLASIFICACIÓN DE CAMINOS POR OPTIMALIDAD (Verde: Mejor, Rojo: Peor, Amarillo: Intermedios)
        caminos_verde = []
        caminos_rojo = []
        caminos_amarillo = []
        caminos_naranja = []
        
        n_caminos = len(caminos_con_costo)
        
        if is_default_view:
            # Vista inicial por defecto se mantiene en naranja
            caminos_naranja = [c[0] for c in caminos_con_costo]
            color_destacado_str = 'naranja'
            border_color = '#fb8500'
        elif es_error or es_camino_error_puro:
            # Si se selecciona un nodo de error/fracaso global o pre-error puro, TODOS los caminos se marcan en ROJO absoluto
            caminos_rojo = [c[0] for c in caminos_con_costo]
            color_destacado_str = 'rojo'
            border_color = '#d90429'
        else:
            if n_caminos == 1:
                caminos_verde = [caminos_con_costo[0][0]]
                color_destacado_str = 'verde'
                border_color = '#2b9348'
            elif n_caminos == 2:
                caminos_verde = [caminos_con_costo[0][0]]
                caminos_rojo = [caminos_con_costo[1][0]]
                color_destacado_str = 'verde'
                border_color = '#2b9348'
            else:
                caminos_verde = [caminos_con_costo[0][0]]
                caminos_rojo = [caminos_con_costo[-1][0]]
                caminos_amarillo = [c[0] for c in caminos_con_costo[1:-1]]
                color_destacado_str = 'verde'
                border_color = '#2b9348'
            
        # Actualizar figura llamando a crear_figura con las listas correspondientes
        fig = crear_figura(
            caminos_verde=caminos_verde if caminos_verde else None,
            caminos_rojo=caminos_rojo if caminos_rojo else None,
            caminos_amarillo=caminos_amarillo if caminos_amarillo else None,
            caminos_naranja=caminos_naranja if caminos_naranja else None
        )
        
        # Construir panel superior
        items_caminos = []
        for idx, item in enumerate(caminos_con_costo):
            camino = item[0]
            costo = item[1]
            ruta_str = " ➔ ".join(camino)
            
            if is_default_view:
                etiqueta_ruta = "Ruta Óptima:" if idx == 0 else f"Ruta Alternativa {idx}:"
                color_etiqueta = '#fb8500'
            elif es_error or es_camino_error_puro:
                # Para casos de error/fracaso global o pre-error puro, todas son rutas de fracaso
                etiqueta_ruta = f"🚨 Ruta de Fracaso {idx + 1}:"
                color_etiqueta = '#d90429'
            else:
                if idx == 0:
                    etiqueta_ruta = "🟢 Ruta Óptima (Mejor opción comercial):"
                    color_etiqueta = '#2b9348'
                elif idx == n_caminos - 1:
                    etiqueta_ruta = "🔴 Peor Opción (Menor valor comercial):"
                    color_etiqueta = '#d90429'
                else:
                    etiqueta_ruta = f"🟡 Ruta Alternativa {idx} (Opción comercial media):"
                    color_etiqueta = '#f5a623'

            estilo_costo = {'color': '#e63946', 'fontWeight': 'bold', 'marginLeft': '15px'}
            estilo_ruta = {'color': '#1d3557', 'fontWeight': '600', 'marginLeft': '10px'}
            estilo_etiqueta = {'color': color_etiqueta, 'fontWeight': '800'}
                
            items_caminos.append(html.Div([
                html.Span(etiqueta_ruta, style=estilo_etiqueta),
                html.Span(f" {ruta_str}", style=estilo_ruta),
                html.Span(f" 💵 Costo Total: {costo}", style=estilo_costo)
            ], style={'padding': '8px 0', 'borderBottom': '1px solid #f1f3f5' if idx < n_caminos-1 else 'none'}))
            
        # Encabezado del contenedor de información
        header_text = f"Destino Seleccionado: {nodo_sel}"
        if es_exito:
            header_icon = "🏆"
            header_subtitle = "Mejores rutas puras hacia el éxito absoluto (Mejor: Verde, Peor: Rojo, Medias: Amarillo)"
        elif es_error or es_camino_error_puro:
            header_icon = "🚨"
            header_subtitle = "Caminos de fracaso o pre-error que conducen inevitablemente a Fuga o SERNAC"
        elif nodo_sel == "Llamada Entrante":
            header_icon = "📞"
            header_subtitle = "Inicio del flujo de atención. Mostrando rama por defecto (Facturación)"
        else:
            header_icon = "📍"
            header_subtitle = f"Flujo y derivaciones asociadas al nodo '{nodo_sel}'"
            
        mensaje = html.Div([
            html.Div([
                html.Span(f"{header_icon} ", style={'fontSize': '24px', 'marginRight': '8px'}),
                html.Strong(header_text, style={'fontSize': '22px', 'color': '#1d3557'}),
                html.P(header_subtitle, style={'color': '#7f8c8d', 'margin': '4px 0 12px 32px', 'fontSize': '14px', 'fontWeight': '500'})
            ]),
            html.Div(items_caminos, style={'maxHeight': '180px', 'overflowY': 'auto', 'paddingLeft': '32px'})
        ])
        
        style_caja = {
            'fontFamily': 'Outfit, Inter, sans-serif', 
            'padding': '20px', 
            'backgroundColor': '#ffffff', 
            'borderRadius': '12px',
            'width': '85%', 
            'margin': '0 auto 20px auto', 
            'minHeight': '80px', 
            'boxShadow': '0 4px 12px rgba(0,0,0,0.08)',
            'borderLeft': f'8px solid {border_color}'
        }
        
        return fig, mensaje, style_caja
    except Exception as e:
        import traceback
        print("Error en callback dashboard_2d:", e)
        traceback.print_exc()
        return dash.no_update, dash.no_update, dash.no_update

def abrir_navegador():
    webbrowser.open_new('http://127.0.0.1:8051/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8051))
    is_production = os.environ.get("RENDER", False)
    if not is_production and not os.environ.get("WERKZEUG_RUN_MAIN"):
        Timer(2.0, abrir_navegador).start()
    app.run(debug=not is_production, host="0.0.0.0", port=port)