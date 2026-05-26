# configuraciones/configuraciones.py

# Definición de las capas para dar estructura de árbol (jerarquía de izquierda a derecha)
NODOS_CAPAS = {
    # Nivel 0
    "Llamada Entrante": 0,
    
    # Nivel 1: Áreas Principales
    "Facturación": 1, 
    "Técnicos": 1, 
    "Ventas": 1,
    "Postventa": 1,
    
    # Nivel 2: Diagnóstico Inicial
    "Verificar Contrato": 2, 
    "Revisar Historial": 2,
    "Soporte Nivel 1": 2,
    "Verificar Estado Pago": 2, 
    "Perfilamiento": 2,
    "Negociar Descuento": 2,
    
    # Nivel 3: Acciones de Resolución, éxitos medios y derivaciones a fuga
    "Tramitar Devolución": 3, 
    "Explicar Cobro": 3,
    "Corte de servicio por no pago": 3, # Nuevo nodo de morosidad
    "Reinicio Remoto": 3,
    "Soporte Nivel 2": 3,
    "Derivar a Terreno": 3,
    "Plan Básico": 3,
    "Plan Premium": 3,
    "Venta no concretada": 3, # Se une a Fracaso (Fuga)
    "Procesar Baja": 3,
    "Cliente nuevo (mejor caso de exito)": 3, # Venta Exitosa (Capa 3)
    "Venta de equipo o accesorio (exito medio)": 3, # Venta Exitosa Media (Capa 3)
    "Nuevo plan": 3, # Postventa Exitosa (Capa 3)
    "Recambio de equipo": 3, # Postventa Exitosa (Capa 3)
    
    # Nivel 4: Únicos Cierres Finales
    "Éxito (Contención)": 4, 
    "Éxito Comercial (Venta)": 4,
    "Fracaso (Fuga)": 4,
    "Escalamiento SERNAC": 4
}

# Aristas del grafo. Formato: (Origen, Destino, Costo/Peso, Etiqueta)
ARISTAS = [
    # Derivaciones Iniciales
    ("Llamada Entrante", "Facturación", 1, "Duda de Cobro"),
    ("Llamada Entrante", "Técnicos", 2, "Sin Servicio"),
    ("Llamada Entrante", "Ventas", 1, "Contratar"),
    ("Llamada Entrante", "Postventa", 5, "Quiero cancelar"),
    
    # --- Rama Facturación ---
    ("Facturación", "Verificar Contrato", 2, "Revisar SLAs"),
    ("Facturación", "Revisar Historial", 1, "Ver boletas previas"),
    
    ("Verificar Contrato", "Tramitar Devolución", 8, "Multa/Costo Empresa"),
    ("Verificar Contrato", "Escalamiento SERNAC", 30, "No aplica devolución"),
    
    ("Revisar Historial", "Explicar Cobro", 3, "Detalle tarifario"),
    ("Explicar Cobro", "Éxito (Contención)", 0, "Acepta explicación"),
    ("Explicar Cobro", "Postventa", 2, "Se molesta por cobro"), # Salto transeúnte
    
    ("Tramitar Devolución", "Éxito (Contención)", 0, "Solución rápida"),
    
    # --- Rama Técnicos ---
    ("Técnicos", "Soporte Nivel 1", 2, "Diagnóstico inicial"),
    ("Técnicos", "Verificar Estado Pago", 1, "Regla de Negocio"),
    
    ("Verificar Estado Pago", "Soporte Nivel 1", 0, "Cliente al día"),
    ("Verificar Estado Pago", "Corte de servicio por no pago", 2, "Morosidad detectada"),
    ("Corte de servicio por no pago", "Explicar Cobro", 3, "Explicar motivos"),
    ("Corte de servicio por no pago", "Facturación", 2, "Derivar a Pago"),
    ("Corte de servicio por no pago", "Fracaso (Fuga)", 5, "Rechaza pagar deuda"),
    
    ("Soporte Nivel 1", "Reinicio Remoto", 2, "Probar reinicio"),
    ("Reinicio Remoto", "Éxito (Contención)", 0, "Servicio OK"),
    
    ("Soporte Nivel 1", "Soporte Nivel 2", 5, "Falla Compleja"),
    ("Soporte Nivel 2", "Reinicio Remoto", 1, "Último intento"),
    ("Soporte Nivel 2", "Derivar a Terreno", 20, "Falla Física (Costo Alto)"),
    ("Derivar a Terreno", "Éxito (Contención)", 0, "Técnico en casa"),
    ("Derivar a Terreno", "Escalamiento SERNAC", 40, "Técnico no llegó"),
    
    # --- Rama Ventas ---
    ("Ventas", "Perfilamiento", 2, "Análisis de uso"),
    ("Perfilamiento", "Plan Básico", 5, "Bajo Presupuesto"),
    ("Perfilamiento", "Plan Premium", 2, "Venta Cruzada"),
    
    ("Plan Básico", "Venta de equipo o accesorio (exito medio)", 2, "Cierra equipo/acc"),
    ("Plan Básico", "Cliente nuevo (mejor caso de exito)", 3, "Cierra plan básico"),
    ("Plan Básico", "Venta no concretada", 4, "Rechaza oferta básica"),
    
    ("Plan Premium", "Cliente nuevo (mejor caso de exito)", 1, "Cierra plan premium"),
    ("Plan Premium", "Venta no concretada", 10, "Rechaza premium"),
    ("Plan Premium", "Postventa", 1, "Considera caro"), # Salto transeúnte
    
    ("Venta no concretada", "Fracaso (Fuga)", 0, "Une a fuga global"),
    
    # Canalizaciones de Éxitos de Ventas (Capa 3) a Éxito Final (Capa 4)
    ("Cliente nuevo (mejor caso de exito)", "Éxito Comercial (Venta)", 0, "Registrar Cliente"),
    ("Venta de equipo o accesorio (exito medio)", "Éxito Comercial (Venta)", 0, "Registrar Venta Equipo"),
    
    # --- Rama Postventa ---
    ("Postventa", "Negociar Descuento", 15, "Descuento 50% (Pérdida)"),
    ("Postventa", "Perfilamiento", 4, "Venta sin descuento"),
    ("Postventa", "Soporte Nivel 1", 3, "Asistencia técnica postventa"),
    ("Postventa", "Verificar Estado Pago", 2, "Revisar suspensión"),
    ("Negociar Descuento", "Nuevo plan", 2, "Acepta migración de plan"),
    ("Negociar Descuento", "Recambio de equipo", 4, "Acepta recambio físico"),
    ("Negociar Descuento", "Procesar Baja", 2, "Rechaza retención"),
    
    ("Procesar Baja", "Fracaso (Fuga)", 0, "Cliente perdido"),
    ("Procesar Baja", "Escalamiento SERNAC", 10, "Baja no procesada"),
    
    # Canalizaciones de Éxitos de Postventa (Capa 3) a Éxito Final (Capa 4)
    ("Nuevo plan", "Éxito Comercial (Venta)", 0, "Activar Plan"),
    ("Recambio de equipo", "Éxito Comercial (Venta)", 0, "Despachar Equipo")
]

# Configuración visual del gráfico
CONFIG_VISUAL = {
    "figsize": (16, 8),
    "node_size": 4000,
    "node_color_default": "#a3c4f3",
    "node_color_success": "#b9fbc0",
    "node_color_fail": "#ffadad",
    "font_size": 10,
    "font_weight": "bold",
    "edge_color": "#8d99ae",
    "arrowsize": 20
}

# Descripciones premium de negocio para cada nodo conversacional (desplegables por Hover)
DESCRIPCIONES_NODOS = {
    "Llamada Entrante": "El cliente llama a sucursal virtual Telefonia",
    "Facturación": "El cliente pregunta por cobros indebidos",
    "Técnicos": "El cliente pregunta por falla en su servicio",
    "Ventas": "El cliente desea contratar nuevos servicios o adquirir equipos",
    "Postventa": "El cliente solicita asistencia comercial posterior a la compra o desea cancelar. Puede derivarse a venta directa sin descuento (Perfilamiento) o a retención con descuento (Negociar Descuento)",
    
    # Capa 2
    "Verificar Contrato": "Se revisan las cláusulas de permanencia y SLAs del cliente",
    "Revisar Historial": "Se auditan las boletas y cobros de meses anteriores",
    "Soporte Nivel 1": "Intento de resolución remota guiada por el agente telefónico",
    "Verificar Estado Pago": "Validación de morosidad o cortes vigentes en sistemas de cobro",
    "Perfilamiento": "Detección de necesidades de consumo para ajustar oferta comercial",
    "Negociar Descuento": "Propuesta de retención ofreciendo bonificación tarifaria especial",
    
    # Capa 3
    "Tramitar Devolución": "Gestión interna para abonar saldo a favor del cliente",
    "Explicar Cobro": "Clarificación detallada de tarifas, cargos adicionales y consumos",
    "Corte de servicio por no pago": "El servicio está suspendido por facturas pendientes de pago",
    "Reinicio Remoto": "Ejecución de reset virtual de la ONT o módem del abonado",
    "Soporte Nivel 2": "Escalamiento a ingenieros expertos en redes para diagnóstico profundo",
    "Derivar a Terreno": "Agendamiento de visita física de un técnico calificado a domicilio",
    "Plan Básico": "Presentación de planes esenciales de menor valor mensual",
    "Plan Premium": "Presentación de planes de alta velocidad o servicios ilimitados",
    "Cliente nuevo (mejor caso de exito)": "Alta exitosa de nuevo abonado en la plataforma comercial",
    "Venta de equipo o accesorio (exito medio)": "Venta exitosa de terminal físico o kit de accesorios",
    "Nuevo plan": "Migración exitosa a una tarifa más adecuada, reteniendo al abonado",
    "Recambio de equipo": "Renovación exitosa del terminal móvil o módem hogar",
    "Venta no concretada": "El prospecto rechaza las ofertas presentadas y cierra el contacto",
    "Procesar Baja": "Ejecución de la desconexión definitiva de la cuenta en sistemas",
    
    # Capa 4
    "Éxito (Contención)": "El cliente finaliza conforme con una resolución técnica o de cobro, evitando la fuga",
    "Éxito Comercial (Venta)": "El cliente adquiere un nuevo producto o renueva su plan, generando valor al negocio",
    "Fracaso (Fuga)": "Pérdida definitiva del cliente con baja o fuga comercial",
    "Escalamiento SERNAC": "Reclamo formal en organismo regulador por disconformidad grave"
}
