import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import random
import math
import time
from datetime import datetime
import re
import numpy as np

# === CONFIGURACIÓN DE PÁGINA ===
st.set_page_config(
    page_title="WKB WORLD CUP 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === CONSTANTES ===
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
PRECIO = 15000
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
CODIGO_VIP = "WKB2026"

CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

PAISES = ["Chile", "Argentina", "Perú", "Brasil", "Uruguay", "Paraguay", 
          "Bolivia", "Ecuador", "Colombia", "Venezuela", "Otro"]

# === FUNCIONES DE UTILIDAD ===
def generar_id(nombre, email):
    texto = f"{nombre}{email}{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def formatear_peso(valor):
    return f"${valor:,.0f}".replace(",", ".")

def tiempo_restante():
    delta = FECHA_TORNEO - datetime.now()
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return dias, horas, minutos, segundos

def verificar_admin(password):
    try:
        return hashlib.sha256(password.encode()).hexdigest() == st.secrets["general"]["admin_token_hash"]
    except:
        return password == "admin123"

# === FUNCIONES DE GOOGLE SHEETS ===
@st.cache_data(ttl=5)
def leer_inscripciones():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Inscripciones", ttl=0)
        df = df.fillna("")
        if df.empty:
            return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo"])
        return df
    except:
        return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo"])

def guardar_inscripcion(datos):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            df_existente = leer_inscripciones()
        except:
            df_existente = pd.DataFrame()
        
        nueva_fila = pd.DataFrame([{
            "ID": datos['id'],
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nombre": datos['nombre'].upper(),
            "Email": datos['email'].lower(),
            "Telefono": datos['telefono'],
            "Edad": datos['edad'],
            "Dojo": datos['dojo'].upper(),
            "Pais": datos['pais'],
            "Categoria": datos['categoria'],
            "Estado": "CONFIRMADO",
            "Metodo": datos['metodo']
        }])
        
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except:
        return False

@st.cache_data(ttl=5)
def leer_brackets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Brackets", ttl=0)
        df = df.fillna("")
        if df.empty:
            return pd.DataFrame(columns=[
                "Categoria", "Ronda", "Partido_ID", "Competidor1_ID", "Competidor1_Nombre", 
                "Dojo1", "Competidor2_ID", "Competidor2_Nombre", "Dojo2", 
                "Ganador_ID", "Ganador_Nombre", "Siguiente_Partido_ID", "Posicion", 
                "Total_Rondas", "Estado_Partido", "Tipo_Emparejamiento"
            ])
        return df
    except:
        return pd.DataFrame(columns=[
            "Categoria", "Ronda", "Partido_ID", "Competidor1_ID", "Competidor1_Nombre", 
            "Dojo1", "Competidor2_ID", "Competidor2_Nombre", "Dojo2", 
            "Ganador_ID", "Ganador_Nombre", "Siguiente_Partido_ID", "Posicion", 
            "Total_Rondas", "Estado_Partido", "Tipo_Emparejamiento"
        ])

def guardar_brackets(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except:
        return False

# === NUEVA LÓGICA DE EMPAREJAMIENTO MEJORADA ===
def generar_emparejamientos_por_categoria(df_competidores, categoria, tipo_emparejamiento="aleatorio", seed=None):
    """
    Genera emparejamientos para una categoría específica con diferentes estrategias
    """
    if seed:
        random.seed(seed)
    
    num_competidores = len(df_competidores)
    if num_competidores < 2:
        return []
    
    # Copia de competidores para no modificar el original
    competidores = df_competidores.copy()
    
    # Aplicar estrategia de emparejamiento
    if tipo_emparejamiento == "aleatorio":
        competidores = competidores.sample(frac=1).reset_index(drop=True)
    
    elif tipo_emparejamiento == "por_dojo":
        # Evitar que competidores del mismo dojo se enfrenten en primera ronda
        dojos = competidores['Dojo'].tolist()
        indices = list(range(num_competidores))
        random.shuffle(indices)
        
        # Reordenar para separar dojos
        competidores_reordenados = []
        dojos_vistos = set()
        
        for idx in indices:
            if len(competidores_reordenados) < num_competidores:
                competidores_reordenados.append(competidores.iloc[idx])
        
        if competidores_reordenados:
            competidores = pd.DataFrame(competidores_reordenados).reset_index(drop=True)
    
    elif tipo_emparejamiento == "por_pais":
        # Similar a por_dojo pero por país
        paises = competidores['Pais'].tolist()
        indices = list(range(num_competidores))
        random.shuffle(indices)
        
        competidores_reordenados = []
        for idx in indices:
            if len(competidores_reordenados) < num_competidores:
                competidores_reordenados.append(competidores.iloc[idx])
        
        if competidores_reordenados:
            competidores = pd.DataFrame(competidores_reordenados).reset_index(drop=True)
    
    elif tipo_emparejamiento == "sembrado":
        # Ordenar por algún criterio (ej. edad, peso, etc.)
        competidores = competidores.sort_values('Edad', ascending=False).reset_index(drop=True)
    
    elif tipo_emparejamiento == "manual":
        # Para configuración manual desde admin
        pass
    
    return competidores

def calcular_rondas_necesarias(num_competidores):
    """Calcula el número de rondas y el tamaño del bracket"""
    num_rondas = math.ceil(math.log2(num_competidores))
    capacidad_total = 2 ** num_rondas
    return num_rondas, capacidad_total

def crear_bracket_estructura(categoria, num_rondas, capacidad_total, competidores_ordenados):
    """Crea la estructura completa del bracket"""
    partidos = []
    pid = 1
    num_competidores = len(competidores_ordenados)
    
    # Ronda 1 - Asignar competidores y BYEs
    for i in range(0, capacidad_total, 2):
        pos = i // 2
        
        # Asignar competidores según orden
        c1 = competidores_ordenados.iloc[i] if i < num_competidores else None
        c2 = competidores_ordenados.iloc[i + 1] if (i + 1) < num_competidores else None
        
        partido = {
            "Categoria": categoria,
            "Ronda": 1,
            "Partido_ID": pid,
            "Competidor1_ID": c1['ID'] if c1 is not None else "BYE",
            "Competidor1_Nombre": c1['Nombre'] if c1 is not None else "BYE",
            "Dojo1": c1['Dojo'] if c1 is not None else "-",
            "Competidor2_ID": c2['ID'] if c2 is not None else "BYE",
            "Competidor2_Nombre": c2['Nombre'] if c2 is not None else "BYE",
            "Dojo2": c2['Dojo'] if c2 is not None else "-",
            "Ganador_ID": "",
            "Ganador_Nombre": "",
            "Siguiente_Partido_ID": None,
            "Posicion": pos,
            "Total_Rondas": num_rondas,
            "Estado_Partido": "PENDIENTE",
            "Tipo_Emparejamiento": "AUTOMATICO"
        }
        
        # Si hay BYE, el ganador es automático
        if partido["Competidor1_Nombre"] == "BYE" and partido["Competidor2_Nombre"] != "BYE":
            partido["Ganador_ID"] = partido["Competidor2_ID"]
            partido["Ganador_Nombre"] = partido["Competidor2_Nombre"]
            partido["Estado_Partido"] = "AUTOMATICO"
        elif partido["Competidor2_Nombre"] == "BYE" and partido["Competidor1_Nombre"] != "BYE":
            partido["Ganador_ID"] = partido["Competidor1_ID"]
            partido["Ganador_Nombre"] = partido["Competidor1_Nombre"]
            partido["Estado_Partido"] = "AUTOMATICO"
        elif partido["Competidor1_Nombre"] == "BYE" and partido["Competidor2_Nombre"] == "BYE":
            partido["Estado_Partido"] = "VACIO"
        
        partidos.append(partido)
        pid += 1
    
    # Rondas siguientes
    partidos_por_ronda = capacidad_total // 2
    for ronda in range(2, num_rondas + 1):
        partidos_por_ronda = partidos_por_ronda // 2
        for j in range(partidos_por_ronda):
            # Calcular partido origen para la siguiente ronda
            partido_origen1 = (j * 2) + 1
            partido_origen2 = (j * 2) + 2
            
            partido = {
                "Categoria": categoria,
                "Ronda": ronda,
                "Partido_ID": pid,
                "Competidor1_ID": "",
                "Competidor1_Nombre": "",
                "Dojo1": "",
                "Competidor2_ID": "",
                "Competidor2_Nombre": "",
                "Dojo2": "",
                "Ganador_ID": "",
                "Ganador_Nombre": "",
                "Siguiente_Partido_ID": None,
                "Posicion": j,
                "Total_Rondas": num_rondas,
                "Estado_Partido": "PENDIENTE",
                "Tipo_Emparejamiento": "AUTOMATICO"
            }
            partidos.append(partido)
            pid += 1
    
    return partidos

def generar_brackets_avanzados(estrategias_por_categoria=None):
    """
    Genera brackets con estrategias configurables por categoría
    """
    df = leer_inscripciones()
    if df.empty: 
        return False, "No hay inscripciones registradas"
    
    df_conf = df[df['Estado'] == 'CONFIRMADO'].copy()
    if len(df_conf) < 2: 
        return False, "Se necesitan al menos 2 competidores"
    
    todos_partidos = []
    stats_categorias = {}
    
    if estrategias_por_categoria is None:
        estrategias_por_categoria = {}
    
    for categoria in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == categoria]
        num_competidores = len(df_cat)
        
        if num_competidores >= 2:
            # Obtener estrategia para esta categoría (default: aleatorio)
            estrategia = estrategias_por_categoria.get(categoria, {
                'tipo': 'aleatorio',
                'seed': int(time.time())
            })
            
            # Generar orden de competidores según estrategia
            competidores_ordenados = generar_emparejamientos_por_categoria(
                df_cat, 
                categoria,
                tipo_emparejamiento=estrategia['tipo'],
                seed=estrategia.get('seed')
            )
            
            num_rondas, capacidad_total = calcular_rondas_necesarias(num_competidores)
            
            stats_categorias[categoria] = {
                'competidores': num_competidores,
                'rondas': num_rondas,
                'capacidad': capacidad_total,
                'estrategia': estrategia['tipo']
            }
            
            # Crear estructura del bracket
            partidos_categoria = crear_bracket_estructura(
                categoria, 
                num_rondas, 
                capacidad_total, 
                competidores_ordenados
            )
            
            todos_partidos.extend(partidos_categoria)
    
    if todos_partidos:
        df_brackets = pd.DataFrame(todos_partidos)
        if guardar_brackets(df_brackets):
            mensaje = "✅ Brackets generados exitosamente\n\n"
            for cat, stats in stats_categorias.items():
                mensaje += f"• **{cat}**: {stats['competidores']} competidores "
                mensaje += f"({stats['estrategia']})\n"
            return True, mensaje
    
    return False, "No se pudieron generar los brackets"

def actualizar_ganador_desde_admin(categoria, partido_id, ganador_id, ganador_nombre):
    """Actualiza el ganador y propaga automáticamente al siguiente partido"""
    df_b = leer_brackets()
    
    # Actualizar el partido actual
    mask = (df_b['Categoria'] == categoria) & (df_b['Partido_ID'] == partido_id)
    df_b.loc[mask, 'Ganador_ID'] = ganador_id
    df_b.loc[mask, 'Ganador_Nombre'] = ganador_nombre
    df_b.loc[mask, 'Estado_Partido'] = 'COMPLETADO'
    
    # Encontrar el siguiente partido
    partido_actual = df_b[mask].iloc[0]
    ronda_actual = partido_actual['Ronda']
    posicion = partido_actual['Posicion']
    
    # Calcular posición en siguiente ronda
    siguiente_ronda = ronda_actual + 1
    siguiente_posicion = posicion // 2
    
    # Buscar partido en siguiente ronda
    siguiente_mask = (df_b['Categoria'] == categoria) & \
                     (df_b['Ronda'] == siguiente_ronda) & \
                     (df_b['Posicion'] == siguiente_posicion)
    
    if not df_b[siguiente_mask].empty:
        # Determinar si va como competidor1 o competidor2
        es_competidor1 = (posicion % 2 == 0)
        
        if es_competidor1:
            df_b.loc[siguiente_mask, 'Competidor1_ID'] = ganador_id
            df_b.loc[siguiente_mask, 'Competidor1_Nombre'] = ganador_nombre
            df_b.loc[siguiente_mask, 'Dojo1'] = partido_actual.get('Dojo1', '')
        else:
            df_b.loc[siguiente_mask, 'Competidor2_ID'] = ganador_id
            df_b.loc[siguiente_mask, 'Competidor2_Nombre'] = ganador_nombre
            df_b.loc[siguiente_mask, 'Dojo2'] = partido_actual.get('Dojo2', '')
        
        # Verificar si el siguiente partido ya tiene ambos competidores
        sig_partido = df_b[siguiente_mask].iloc[0]
        if sig_partido['Competidor1_Nombre'] and sig_partido['Competidor2_Nombre']:
            if "BYE" not in [sig_partido['Competidor1_Nombre'], sig_partido['Competidor2_Nombre']]:
                df_b.loc[siguiente_mask, 'Estado_Partido'] = 'LISTO'
    
    return guardar_brackets(df_b)

def obtener_siguientes_partidos_disponibles(categoria):
    """Obtiene los partidos que están listos para jugarse"""
    df_b = leer_brackets()
    df_cat = df_b[df_b['Categoria'] == categoria]
    
    # Partidos con ambos competidores y sin ganador
    disponibles = df_cat[
        (df_cat['Competidor1_Nombre'] != "") & 
        (df_cat['Competidor2_Nombre'] != "") & 
        (df_cat['Competidor1_Nombre'] != "BYE") & 
        (df_cat['Competidor2_Nombre'] != "BYE") &
        (df_cat['Ganador_Nombre'] == "")
    ]
    
    return disponibles.sort_values(['Ronda', 'Posicion'])

def obtener_resumen_brackets():
    """Obtiene resumen del estado de los brackets"""
    df_b = leer_brackets()
    if df_b.empty:
        return {}
    
    resumen = {}
    for categoria in df_b['Categoria'].unique():
        df_cat = df_b[df_b['Categoria'] == categoria]
        
        total_partidos = len(df_cat)
        completados = len(df_cat[df_cat['Estado_Partido'] == 'COMPLETADO'])
        pendientes = len(df_cat[df_cat['Estado_Partido'] == 'PENDIENTE'])
        automaticos = len(df_cat[df_cat['Estado_Partido'] == 'AUTOMATICO'])
        
        resumen[categoria] = {
            'total': total_partidos,
            'completados': completados,
            'pendientes': pendientes,
            'automaticos': automaticos,
            'progreso': f"{completados}/{total_partidos}"
        }
    
    return resumen

# === CSS FUTURISTA PROFESIONAL (igual que antes) ===
css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Space+Grotesk:wght@300;400;600;700&display=swap');
    
    .stApp {
        background: #0a0a0f;
        font-family: 'Inter', sans-serif;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1a1a24;
    }
    ::-webkit-scrollbar-thumb {
        background: #ff2b2b;
        border-radius: 4px;
    }
    
    .header-container {
        text-align: center;
        padding: 40px 20px;
        position: relative;
        overflow: hidden;
    }
    
    .logo-img {
        width: min(400px, 80%);
        filter: drop-shadow(0 0 40px rgba(255,43,43,0.3));
        transition: transform 0.5s;
    }
    
    .title-main {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #ff8a8a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 20px 0 10px;
        letter-spacing: 2px;
    }
    
    .countdown-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        max-width: 800px;
        margin: 40px auto;
        padding: 0 20px;
    }
    
    .countdown-item {
        background: linear-gradient(145deg, #12121a, #1a1a24);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s;
    }
    
    .countdown-number {
        font-family: 'Space Grotesk', monospace;
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 800;
        color: #ff2b2b;
    }
    
    .glass-card {
        background: rgba(18, 18, 26, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 24px;
        padding: 30px;
        margin: 20px 0;
    }
    
    .metric-container {
        background: linear-gradient(145deg, #12121a, #0a0a0f);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s;
    }
    
    .metric-label {
        color: rgba(255,255,255,0.5);
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        color: #ff2b2b;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #ff2b2b, #ff5555) !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        width: 100%;
        transition: all 0.3s !important;
    }
    
    .admin-button > button {
        background: linear-gradient(135deg, #ff8c00, #ff2b2b) !important;
    }
    
    .bracket-container {
        background: rgba(18, 18, 26, 0.5);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 30px;
        margin: 20px 0;
        overflow-x: auto;
    }
    
    .bracket-round {
        display: flex;
        flex-direction: column;
        gap: 20px;
        min-width: 300px;
    }
    
    .bracket-round-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #ff2b2b;
        text-align: center;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(255,43,43,0.3);
    }
    
    .bracket-match {
        background: linear-gradient(145deg, #12121a, #1a1a24);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 15px;
        position: relative;
        transition: all 0.3s;
    }
    
    .bracket-match.ready {
        border-color: #00ff88;
        box-shadow: 0 0 20px rgba(0,255,136,0.2);
    }
    
    .bracket-match.completed {
        border-color: gold;
        opacity: 0.8;
    }
    
    .bracket-competitor {
        padding: 8px 12px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 0.9rem;
    }
    
    .bracket-competitor.red {
        border-left: 4px solid #ff2b2b;
    }
    
    .bracket-competitor.blue {
        border-left: 4px solid #1e90ff;
    }
    
    .bracket-competitor.winner {
        background: rgba(255,215,0,0.1);
        border-left-color: gold;
    }
    
    .bracket-id {
        position: absolute;
        top: -8px;
        right: 10px;
        background: #ff2b2b;
        color: white;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 20px;
    }
    
    .status-badge {
        position: absolute;
        top: -8px;
        left: 10px;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 20px;
        background: #666;
        color: white;
    }
    
    .status-badge.ready {
        background: #00ff88;
        color: black;
    }
    
    .status-badge.completed {
        background: gold;
        color: black;
    }
    
    .progress-bar {
        height: 8px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #ff2b2b, gold);
        transition: width 0.3s;
    }
    
    .strategy-selector {
        background: rgba(255,43,43,0.1);
        border: 1px solid #ff2b2b;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# === HEADER ===
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" class="logo-img">
        <div class="title-main">WORLD CUP 2026</div>
        <div class="subtitle">SANTIAGO · CHILE</div>
    </div>
    """, unsafe_allow_html=True)

# === COUNTDOWN ===
dias, horas, minutos, segundos = tiempo_restante()
st.markdown(f"""
<div class="countdown-grid">
    <div class="countdown-item">
        <div class="countdown-number">{dias}</div>
        <div class="countdown-label">DÍAS</div>
    </div>
    <div class="countdown-item">
        <div class="countdown-number">{horas}</div>
        <div class="countdown-label">HORAS</div>
    </div>
    <div class="countdown-item">
        <div class="countdown-number">{minutos}</div>
        <div class="countdown-label">MINUTOS</div>
    </div>
    <div class="countdown-item">
        <div class="countdown-number">{segundos}</div>
        <div class="countdown-label">SEGUNDOS</div>
    </div>
</div>
""", unsafe_allow_html=True)

# === TABS ===
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "📝 INSCRIPCIÓN", "🏆 BRACKETS", "⚡ ADMIN"])

# ========== TAB 1: DASHBOARD ==========
with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    df = leer_inscripciones()
    
    if not df.empty:
        df_conf = df[df['Estado'] == 'CONFIRMADO']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">INSCRITOS</div>
                <div class="metric-value">{len(df_conf)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">CATEGORÍAS</div>
                <div class="metric-value">{df_conf['Categoria'].nunique()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">DOJOS</div>
                <div class="metric-value">{df_conf['Dojo'].nunique()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            cupos_restantes = 500 - len(df_conf)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">CUPOS</div>
                <div class="metric-value">{cupos_restantes}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Resumen de brackets
        resumen_brackets = obtener_resumen_brackets()
        if resumen_brackets:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("### 🏆 Progreso del Torneo")
            
            for cat, stats in resumen_brackets.items():
                progreso = (stats['completados'] / stats['total']) * 100 if stats['total'] > 0 else 0
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{cat}</span>
                        <span>{stats['progreso']} partidos</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progreso}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Gráfico de distribución
        counts = df_conf['Categoria'].value_counts().sort_values()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=counts.index,
            x=counts.values,
            orientation='h',
            marker=dict(
                color=counts.values,
                colorscale=[[0, '#440000'], [1, '#ff2b2b']],
                showscale=False
            ),
            text=counts.values,
            textposition='outside',
            textfont=dict(color='white')
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📌 No hay inscripciones registradas")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 2: INSCRIPCIÓN (igual que antes) ==========
with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Formulario de Inscripción")
    
    with st.form("form_inscripcion"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre Completo *")
            email = st.text_input("Email *")
            telefono = st.text_input("Teléfono *")
        
        with col2:
            edad = st.number_input("Edad *", 18, 99, 25)
            dojo = st.text_input("Dojo *")
            pais = st.selectbox("País", PAISES)
        
        categoria = st.selectbox("Categoría *", CATEGORIAS)
        
        st.markdown(f"### Valor: {formatear_peso(PRECIO)} CLP")
        
        metodo_pago = st.radio(
            "Método de pago",
            ["Código VIP", "Pagar después"],
            horizontal=True
        )
        
        codigo_vip = ""
        if metodo_pago == "Código VIP":
            codigo_vip = st.text_input("Código VIP", type="password")
        
        terminos = st.checkbox("Acepto los términos y condiciones del torneo")
        
        submitted = st.form_submit_button("INSCRIBIRSE")
        
        if submitted:
            errores = []
            if not nombre or len(nombre.split()) < 2:
                errores.append("Nombre completo requerido")
            if not email or not validar_email(email):
                errores.append("Email inválido")
            if not telefono or len(telefono) < 8:
                errores.append("Teléfono inválido")
            if not dojo:
                errores.append("Dojo requerido")
            if not terminos:
                errores.append("Debes aceptar los términos")
            if metodo_pago == "Código VIP" and codigo_vip != CODIGO_VIP:
                errores.append("Código VIP inválido")
            
            if not errores:
                datos = {
                    'id': generar_id(nombre, email),
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono,
                    'edad': edad,
                    'dojo': dojo,
                    'pais': pais,
                    'categoria': categoria,
                    'metodo': 'VIP' if metodo_pago == "Código VIP" else 'Pendiente'
                }
                
                if guardar_inscripcion(datos):
                    st.balloons()
                    st.success("✅ ¡Inscripción exitosa!")
                    time.sleep(2)
                    st.rerun()
            else:
                for error in errores:
                    st.error(error)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 3: BRACKETS ==========
with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🏆 Brackets del Torneo")
    
    # Verificar admin
    is_admin = False
    with st.expander("🔐 Acceso Admin", expanded=False):
        admin_pass = st.text_input("Contraseña Admin", type="password", key="admin_pass_brackets")
        is_admin = verificar_admin(admin_pass)
    
    # Panel de generación de brackets (solo admin)
    if is_admin:
        st.markdown("#### ⚙️ Configuración de Emparejamientos")
        
        with st.form("config_brackets"):
            estrategias = {}
            
            st.markdown('<div class="strategy-selector">', unsafe_allow_html=True)
            st.markdown("Selecciona estrategia por categoría:")
            
            # Opción global
            estrategia_global = st.selectbox(
                "Estrategia Global (aplica a todas)",
                ["aleatorio", "por_dojo", "por_pais", "sembrado", "manual"],
                format_func=lambda x: {
                    "aleatorio": "🎲 Completamente aleatorio",
                    "por_dojo": "🏢 Separar por Dojo",
                    "por_pais": "🌍 Separar por País",
                    "sembrado": "📊 Sembrado por Edad",
                    "manual": "✋ Configuración manual"
                }.get(x, x)
            )
            
            # Opciones por categoría
            st.markdown("---")
            st.markdown("Ajustes específicos por categoría:")
            
            cols = st.columns(2)
            for i, categoria in enumerate(CATEGORIAS):
                with cols[i % 2]:
                    estrategia_cat = st.selectbox(
                        f"{categoria[:20]}...",
                        ["global", "aleatorio", "por_dojo", "por_pais", "sembrado"],
                        index=0,
                        key=f"strat_{categoria}"
                    )
                    if estrategia_cat != "global":
                        estrategias[categoria] = {
                            'tipo': estrategia_cat,
                            'seed': int(time.time())
                        }
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                generar = st.form_submit_button("⚡ GENERAR BRACKETS CON ESTRATEGIA")
        
        if generar:
            with st.spinner("Generando brackets con estrategias personalizadas..."):
                resultado, mensaje = generar_brackets_avanzados(estrategias)
                if resultado:
                    st.success(mensaje)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning(mensaje)
        
        st.markdown("<hr>", unsafe_allow_html=True)
    
    # Mostrar brackets
    df_brackets = leer_brackets()
    
    if not df_brackets.empty:
        categorias = df_brackets['Categoria'].unique()
        categoria_sel = st.selectbox("📂 Seleccionar Categoría", categorias)
        
        df_cat = df_brackets[df_brackets['Categoria'] == categoria_sel]
        
        if not df_cat.empty:
            total_rondas = int(df_cat['Total_Rondas'].iloc[0])
            rondas = sorted(df_cat['Ronda'].unique())
            
            # Partidos listos para jugar
            partidos_listos = obtener_siguientes_partidos_disponibles(categoria_sel)
            if not partidos_listos.empty and is_admin:
                st.markdown("#### ⚔️ Partidos Listos para Jugar")
                with st.expander("Seleccionar Ganadores"):
                    for _, partido in partidos_listos.iterrows():
                        st.markdown(f"**Partido #{partido['Partido_ID']}**")
                        ganador = st.radio(
                            f"",
                            [partido['Competidor1_Nombre'], partido['Competidor2_Nombre']],
                            key=f"winner_{partido['Partido_ID']}",
                            horizontal=True
                        )
                        
                        if st.button(f"✓ Confirmar Ganador", key=f"btn_{partido['Partido_ID']}"):
                            ganador_id = partido['Competidor1_ID'] if ganador == partido['Competidor1_Nombre'] else partido['Competidor2_ID']
                            if actualizar_ganador_desde_admin(categoria_sel, partido['Partido_ID'], ganador_id, ganador):
                                st.success(f"✅ Ganador: {ganador}")
                                st.rerun()
                        st.markdown("---")
            
            # Construir HTML de brackets
            html = '<div class="bracket-container"><div style="display: flex; gap: 40px; min-width: max-content;">'
            
            for ronda in rondas:
                df_ronda = df_cat[df_cat['Ronda'] == ronda].sort_values('Posicion')
                
                # Título de ronda
                if ronda == total_rondas:
                    titulo = "🏆 FINAL"
                elif ronda == total_rondas - 1:
                    titulo = "🥈 SEMIFINAL"
                elif ronda == total_rondas - 2:
                    titulo = "🥉 CUARTOS"
                else:
                    titulo = f"RONDA {ronda}"
                
                html += f'<div class="bracket-round">'
                html += f'<div class="bracket-round-title">{titulo}</div>'
                
                for _, p in df_ronda.iterrows():
                    # Datos seguros
                    id_p = str(p['Partido_ID'])
                    c1 = str(p['Competidor1_Nombre']) if p['Competidor1_Nombre'] else "---"
                    c2 = str(p['Competidor2_Nombre']) if p['Competidor2_Nombre'] else "---"
                    d1 = str(p['Dojo1']) if p['Dojo1'] else ""
                    d2 = str(p['Dojo2']) if p['Dojo2'] else ""
                    ganador = str(p['Ganador_Nombre'])
                    estado = str(p['Estado_Partido'])
                    
                    # Determinar estilos
                    c1_win = (ganador == c1 and ganador != "" and ganador != "---")
                    c2_win = (ganador == c2 and ganador != "" and ganador != "---")
                    
                    # Clase para el match
                    match_class = "bracket-match"
                    if estado == "COMPLETADO":
                        match_class += " completed"
                    elif c1 != "---" and c2 != "---" and c1 != "BYE" and c2 != "BYE" and not ganador:
                        match_class += " ready"
                    
                    # Badge de estado
                    status_badge = ""
                    if estado == "COMPLETADO":
                        status_badge = '<span class="status-badge completed">COMPLETADO</span>'
                    elif c1 != "---" and c2 != "---" and c1 != "BYE" and c2 != "BYE" and not ganador:
                        status_badge = '<span class="status-badge ready">LISTO</span>'
                    
                    # Bye badge
                    bye_badge = ""
                    if "BYE" in [c1, c2]:
                        bye_badge = '<div class="bracket-bye">⭐ BYE</div>'
                    
                    html += f'<div class="{match_class}">'
                    html += f'<span class="bracket-id">#{id_p}</span>'
                    html += status_badge
                    html += bye_badge
                    
                    # Competidor 1
                    html += f'<div class="bracket-competitor red{" winner" if c1_win else ""}">'
                    html += f'<div style="font-weight: {"bold" if c1_win else "normal"}">{c1}</div>'
                    if d1:
                        html += f'<div class="bracket-dojo">{d1}</div>'
                    html += '</div>'
                    
                    # Competidor 2
                    html += f'<div class="bracket-competitor blue{" winner" if c2_win else ""}">'
                    html += f'<div style="font-weight: {"bold" if c2_win else "normal"}">{c2}</div>'
                    if d2:
                        html += f'<div class="bracket-dojo">{d2}</div>'
                    html += '</div>'
                    
                    html += '</div>'
                
                html += '</div>'
            
            html += '</div></div>'
            
            st.markdown(html, unsafe_allow_html=True)
            
            # Leyenda
            st.markdown("""
            <div class="legend">
                <div class="legend-item"><div class="legend-color red"></div> Aka (Rojo)</div>
                <div class="legend-item"><div class="legend-color blue"></div> Ao (Azul)</div>
                <div class="legend-item"><div class="legend-color gold"></div> Ganador</div>
                <div class="legend-item"><div class="legend-color bye"></div> BYE</div>
                <div class="legend-item"><span style="color:#00ff88;">🟢</span> Listo</div>
                <div class="legend-item"><span style="color:gold;">🏆</span> Completado</div>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.info("📌 No hay brackets generados")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 4: ADMIN ==========
with tab4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ⚡ Panel de Administración")
    
    password = st.text_input("Contraseña", type="password", key="admin_pass_main")
    
    if verificar_admin(password):
        tabs_admin = st.tabs(["📋 Inscripciones", "🏆 Gestión de Brackets", "📊 Estadísticas", "⚙️ Configuración"])
        
        with tabs_admin[0]:
            df_admin = leer_inscripciones()
            if not df_admin.empty:
                st.dataframe(df_admin, use_container_width=True, hide_index=True)
                csv = df_admin.to_csv(index=False)
                st.download_button(
                    "📥 DESCARGAR CSV",
                    csv,
                    "inscripciones.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                st.info("No hay inscripciones")
        
        with tabs_admin[1]:
            df_b = leer_brackets()
            if not df_b.empty:
                st.markdown("#### 🔧 Edición Manual de Brackets")
                
                # Vista de datos
                with st.expander("Ver datos completos"):
                    st.dataframe(df_b, use_container_width=True, hide_index=True)
                
                # Editor de partidos
                with st.expander("Editar partido específico"):
                    col1, col2 = st.columns(2)
                    with col1:
                        cat_edit = st.selectbox("Categoría", df_b['Categoria'].unique())
                    with col2:
                        df_cat_edit = df_b[df_b['Categoria'] == cat_edit]
                        partido_edit = st.selectbox("ID Partido", df_cat_edit['Partido_ID'].unique())
                    
                    if partido_edit:
                        partido = df_cat_edit[df_cat_edit['Partido_ID'] == partido_edit].iloc[0]
                        
                        with st.form("edit_partido"):
                            st.markdown(f"**Partido #{partido_edit} - Ronda {partido['Ronda']}**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                c1_nombre = st.text_input("Competidor 1", partido['Competidor1_Nombre'])
                                c1_dojo = st.text_input("Dojo 1", partido['Dojo1'])
                            with col2:
                                c2_nombre = st.text_input("Competidor 2", partido['Competidor2_Nombre'])
                                c2_dojo = st.text_input("Dojo 2", partido['Dojo2'])
                            
                            ganador = st.text_input("Ganador", partido['Ganador_Nombre'])
                            estado = st.selectbox("Estado", ["PENDIENTE", "COMPLETADO", "AUTOMATICO", "VACIO"])
                            
                            if st.form_submit_button("💾 ACTUALIZAR"):
                                df_b.loc[(df_b['Categoria'] == cat_edit) & 
                                        (df_b['Partido_ID'] == partido_edit), 
                                        ['Competidor1_Nombre', 'Dojo1', 'Competidor2_Nombre', 
                                         'Dojo2', 'Ganador_Nombre', 'Estado_Partido']] = [
                                    c1_nombre, c1_dojo, c2_nombre, c2_dojo, ganador, estado
                                ]
                                if guardar_brackets(df_b):
                                    st.success("✅ Partido actualizado")
                                    st.rerun()
                
                # Gestión de BYEs
                with st.expander("Gestionar BYEs automáticos"):
                    if st.button("🔄 Recalcular BYEs automáticos"):
                        # Lógica para recalcular BYEs
                        st.info("Funcionalidad en desarrollo")
                
                # Reset
                if st.button("⚠️ REINICIAR BRACKETS", use_container_width=True):
                    df_vacio = pd.DataFrame(columns=df_b.columns)
                    if guardar_brackets(df_vacio):
                        st.warning("Brackets reiniciados")
                        st.rerun()
            
            else:
                st.info("No hay brackets generados")
        
        with tabs_admin[2]:
            df_stats = leer_inscripciones()
            if not df_stats.empty:
                df_conf = df_stats[df_stats['Estado'] == 'CONFIRMADO']
                
                col1, col2, col3 = st.columns(3)
                
                total = len(df_conf[df_conf['Metodo'] != 'VIP']) * PRECIO
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">INGRESOS</div>
                        <div class="metric-value">{formatear_peso(total)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    vip_count = len(df_stats[df_stats['Metodo'] == 'VIP'])
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">VIP</div>
                        <div class="metric-value">{vip_count}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    pendientes = len(df_stats[df_stats['Metodo'] == 'Pendiente'])
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">PENDIENTES</div>
                        <div class="metric-value">{pendientes}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Estadísticas de brackets
                resumen = obtener_resumen_brackets()
                if resumen:
                    st.markdown("---")
                    st.markdown("### 📊 Estado de Brackets")
                    
                    df_resumen = pd.DataFrame(resumen).T
                    st.dataframe(df_resumen, use_container_width=True)
        
        with tabs_admin[3]:
            st.markdown("#### ⚙️ Configuración del Sistema")
            
            with st.form("config_sistema"):
                st.markdown("**Estrategias por defecto**")
                default_strategy = st.selectbox(
                    "Estrategia global por defecto",
                    ["aleatorio", "por_dojo", "por_pais", "sembrado"]
                )
                
                st.markdown("**Límites del torneo**")
                max_inscripciones = st.number_input("Máximo de inscripciones", 100, 1000, 500)
                
                st.markdown("**Configuración de Google Sheets**")
                st.info("Configurar en secrets.toml")
                
                if st.form_submit_button("💾 GUARDAR CONFIGURACIÓN"):
                    st.success("Configuración guardada (simulado)")
    
    elif password:
        st.error("❌ Contraseña incorrecta")
    
    st.markdown('</div>', unsafe_allow_html=True)

# === FOOTER ===
st.markdown("""
<div class="footer">
    <p>© 2024 World Kyokushin Budokai Chile · Todos los derechos reservados</p>
</div>
""", unsafe_allow_html=True)
