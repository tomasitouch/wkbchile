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
    # En producción usar st.secrets
    try:
        return hashlib.sha256(password.encode()).hexdigest() == st.secrets["general"]["admin_token_hash"]
    except:
        return password == "admin123"  # Fallback para pruebas

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
            return pd.DataFrame(columns=["Categoria", "Ronda", "Partido_ID", "Competidor1", "Dojo1", "Competidor2", "Dojo2", "Ganador", "Siguiente_Partido", "Posicion", "Total_Rondas"])
        return df
    except:
        return pd.DataFrame(columns=["Categoria", "Ronda", "Partido_ID", "Competidor1", "Dojo1", "Competidor2", "Dojo2", "Ganador", "Siguiente_Partido", "Posicion", "Total_Rondas"])

def guardar_brackets(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except:
        return False

# === GENERADOR DE BRACKETS DINÁMICOS ===
def generar_brackets_dinamicos():
    df = leer_inscripciones()
    if df.empty: 
        return False, "No hay inscripciones registradas"
    
    df_conf = df[df['Estado'] == 'CONFIRMADO'].copy()
    if len(df_conf) < 2: 
        return False, "Se necesitan al menos 2 competidores para generar brackets"
    
    todos_partidos = []
    stats_categorias = {}
    pid = 1
    
    for categoria in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == categoria]
        num_competidores = len(df_cat)
        
        if num_competidores >= 2:
            participantes = df_cat.to_dict('records')
            random.shuffle(participantes)
            
            num_rondas = math.ceil(math.log2(num_competidores))
            capacidad_total = 2 ** num_rondas
            
            stats_categorias[categoria] = {
                'competidores': num_competidores, 
                'rondas': num_rondas,
                'capacidad': capacidad_total
            }
            
            competidores_lista = participantes.copy()
            byes_necesarios = capacidad_total - num_competidores
            
            for i in range(byes_necesarios):
                competidores_lista.insert(random.randint(0, len(competidores_lista)), None)
            
            # Ronda 1
            for i in range(0, len(competidores_lista), 2):
                c1 = competidores_lista[i]
                c2 = competidores_lista[i + 1]
                
                n1 = c1['Nombre'] if c1 else "BYE"
                d1 = c1['Dojo'] if c1 else "-"
                n2 = c2['Nombre'] if c2 else "BYE"
                d2 = c2['Dojo'] if c2 else "-"
                
                winner = ""
                if n1 == "BYE" and n2 != "BYE":
                    winner = n2
                elif n2 == "BYE" and n1 != "BYE":
                    winner = n1

                partido = {
                    "Categoria": categoria, 
                    "Ronda": 1, 
                    "Partido_ID": pid,
                    "Competidor1": n1, 
                    "Dojo1": d1,
                    "Competidor2": n2, 
                    "Dojo2": d2,
                    "Ganador": winner,
                    "Posicion": i // 2, 
                    "Total_Rondas": num_rondas
                }
                todos_partidos.append(partido)
                pid += 1
            
            # Rondas siguientes
            partidos_por_ronda = capacidad_total // 2
            for ronda in range(2, num_rondas + 1):
                partidos_por_ronda = partidos_por_ronda // 2
                for j in range(partidos_por_ronda):
                    partido = {
                        "Categoria": categoria, 
                        "Ronda": ronda, 
                        "Partido_ID": pid,
                        "Competidor1": "", 
                        "Dojo1": "",
                        "Competidor2": "", 
                        "Dojo2": "",
                        "Ganador": "",
                        "Posicion": j, 
                        "Total_Rondas": num_rondas
                    }
                    todos_partidos.append(partido)
                    pid += 1

    if todos_partidos:
        df_brackets = pd.DataFrame(todos_partidos)
        if guardar_brackets(df_brackets):
            mensaje = "✅ Brackets generados exitosamente\n\n"
            for cat, stats in stats_categorias.items():
                mensaje += f"• **{cat}**: {stats['competidores']} competidores\n"
            return True, mensaje
    
    return False, "No se pudieron generar los brackets"

# === CSS FUTURISTA PROFESIONAL ===
css = """
<style>
    /* Importar fuentes */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Space+Grotesk:wght@300;400;600;700&display=swap');
    
    /* Reset y base */
    .stApp {
        background: #0a0a0f;
        font-family: 'Inter', sans-serif;
    }
    
    /* Scrollbar personalizado */
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
    ::-webkit-scrollbar-thumb:hover {
        background: #ff5555;
    }
    
    /* Header y logo */
    .header-container {
        text-align: center;
        padding: 40px 20px;
        position: relative;
        overflow: hidden;
    }
    .header-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 50%, rgba(255,43,43,0.03) 0%, transparent 50%);
        animation: rotate 20s linear infinite;
    }
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .logo-img {
        width: min(400px, 80%);
        filter: drop-shadow(0 0 40px rgba(255,43,43,0.3));
        transition: transform 0.5s;
    }
    .logo-img:hover {
        transform: scale(1.02);
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
    .subtitle {
        color: rgba(255,255,255,0.5);
        font-size: 0.9rem;
        letter-spacing: 4px;
        text-transform: uppercase;
    }
    
    /* Countdown grid */
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
        position: relative;
        overflow: hidden;
        transition: all 0.3s;
    }
    .countdown-item::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #ff2b2b, transparent);
    }
    .countdown-item:hover {
        transform: translateY(-5px);
        border-color: rgba(255,43,43,0.3);
        box-shadow: 0 10px 30px rgba(255,43,43,0.1);
    }
    .countdown-number {
        font-family: 'Space Grotesk', monospace;
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 800;
        color: #ff2b2b;
        line-height: 1;
        margin-bottom: 5px;
        text-shadow: 0 0 20px rgba(255,43,43,0.3);
    }
    .countdown-label {
        color: rgba(255,255,255,0.5);
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    /* Cards de contenido */
    .glass-card {
        background: rgba(18, 18, 26, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 24px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        transition: all 0.3s;
    }
    .glass-card:hover {
        border-color: rgba(255,43,43,0.2);
        box-shadow: 0 30px 60px rgba(255,43,43,0.15);
    }
    
    /* Métricas */
    .metric-container {
        background: linear-gradient(145deg, #12121a, #0a0a0f);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s;
    }
    .metric-container:hover {
        border-color: #ff2b2b;
        transform: translateY(-5px);
    }
    .metric-label {
        color: rgba(255,255,255,0.5);
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        color: #ff2b2b;
        text-shadow: 0 0 30px rgba(255,43,43,0.3);
    }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(18, 18, 26, 0.5);
        backdrop-filter: blur(10px);
        padding: 8px;
        border-radius: 50px;
        border: 1px solid rgba(255,255,255,0.03);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 40px;
        padding: 10px 24px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff2b2b, #ff5555) !important;
        color: white !important;
    }
    
    /* Formulario */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background: rgba(18, 18, 26, 0.8) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s !important;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #ff2b2b !important;
        box-shadow: 0 0 0 2px rgba(255,43,43,0.2) !important;
    }
    
    /* Botones */
    .stButton > button {
        background: linear-gradient(135deg, #ff2b2b, #ff5555) !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 1px !important;
        padding: 12px 24px !important;
        border: none !important;
        border-radius: 12px !important;
        width: 100%;
        transition: all 0.3s !important;
        text-transform: uppercase !important;
        box-shadow: 0 10px 20px rgba(255,43,43,0.2) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 30px rgba(255,43,43,0.3) !important;
    }
    
    /* Admin button especial */
    .admin-button > button {
        background: linear-gradient(135deg, #ff8c00, #ff2b2b) !important;
    }
    
    /* Dividers */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,43,43,0.3), transparent);
        margin: 30px 0;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: rgba(18, 18, 26, 0.5) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Dataframes */
    .stDataFrame {
        background: rgba(18, 18, 26, 0.5) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        padding: 5px;
    }
    
    /* Mensajes */
    .stSuccess {
        background: rgba(0,255,0,0.1) !important;
        border-left-color: #00ff00 !important;
        color: white !important;
        border-radius: 8px !important;
    }
    .stError {
        background: rgba(255,0,0,0.1) !important;
        border-left-color: #ff2b2b !important;
        color: white !important;
        border-radius: 8px !important;
    }
    .stInfo {
        background: rgba(255,255,255,0.05) !important;
        border-left-color: #ff2b2b !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: rgba(255,255,255,0.3);
        padding: 40px 0 20px;
        font-size: 0.8rem;
        letter-spacing: 1px;
        border-top: 1px solid rgba(255,255,255,0.03);
        margin-top: 60px;
    }
    
    /* Brackets styling */
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
        margin-bottom: 20px;
    }
    .bracket-match {
        background: linear-gradient(145deg, #12121a, #1a1a24);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 15px;
        position: relative;
        transition: all 0.3s;
    }
    .bracket-match:hover {
        border-color: #ff2b2b;
        transform: scale(1.02);
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
    .bracket-dojo {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.3);
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
        font-weight: 600;
    }
    .bracket-bye {
        background: rgba(255,215,0,0.1);
        color: gold;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 5px;
    }
    
    /* Leyenda */
    .legend {
        display: flex;
        gap: 30px;
        justify-content: center;
        flex-wrap: wrap;
        margin: 30px 0;
        padding: 20px;
        background: rgba(18, 18, 26, 0.3);
        border-radius: 50px;
        border: 1px solid rgba(255,255,255,0.03);
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: rgba(255,255,255,0.7);
        font-size: 0.8rem;
    }
    .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 4px;
    }
    .legend-color.red { background: #ff2b2b; }
    .legend-color.blue { background: #1e90ff; }
    .legend-color.gold { background: gold; }
    .legend-color.bye { background: gold; opacity: 0.3; }
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
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-label">INSCRITOS</div>
                <div class="metric-value">{}</div>
            </div>
            """.format(len(df_conf)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-label">CATEGORÍAS</div>
                <div class="metric-value">{}</div>
            </div>
            """.format(df_conf['Categoria'].nunique()), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-label">DOJOS</div>
                <div class="metric-value">{}</div>
            </div>
            """.format(df_conf['Dojo'].nunique()), unsafe_allow_html=True)
        
        with col4:
            cupos_restantes = 500 - len(df_conf)
            st.markdown("""
            <div class="metric-container">
                <div class="metric-label">CUPOS</div>
                <div class="metric-value">{}</div>
            </div>
            """.format(cupos_restantes), unsafe_allow_html=True)
        
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
                showscale=False,
                line=dict(color='white', width=1)
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
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                title="Número de Inscritos",
                title_font=dict(color='rgba(255,255,255,0.5)')
            ),
            yaxis=dict(
                showgrid=False,
                title_font=dict(color='rgba(255,255,255,0.5)')
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📌 No hay inscripciones registradas")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 2: INSCRIPCIÓN ==========
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
    
    # Verificar si es admin (para mostrar botón de generar)
    is_admin = False
    with st.expander("🔐 Acceso Admin", expanded=False):
        admin_pass = st.text_input("Contraseña Admin", type="password", key="admin_pass_brackets")
        is_admin = verificar_admin(admin_pass)
    
    # Botón de generar brackets (solo visible para admin)
    if is_admin:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚡ GENERAR BRACKETS", use_container_width=True, key="gen_brackets"):
                with st.spinner("Generando brackets..."):
                    resultado, mensaje = generar_brackets_dinamicos()
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
                    c1 = str(p['Competidor1']) if p['Competidor1'] else "---"
                    c2 = str(p['Competidor2']) if p['Competidor2'] else "---"
                    d1 = str(p['Dojo1']) if p['Dojo1'] else ""
                    d2 = str(p['Dojo2']) if p['Dojo2'] else ""
                    ganador = str(p['Ganador'])
                    
                    # Determinar estilos
                    c1_win = (ganador == c1 and ganador != "" and ganador != "---")
                    c2_win = (ganador == c2 and ganador != "" and ganador != "---")
                    
                    # Bye badge
                    bye_badge = ""
                    if "BYE" in [c1, c2]:
                        bye_badge = '<div class="bracket-bye">⭐ BYE</div>'
                    
                    html += f'<div class="bracket-match">'
                    html += f'<span class="bracket-id">#{id_p}</span>'
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
                    
                    html += '</div>'  # Cierra bracket-match
                
                html += '</div>'  # Cierra bracket-round
            
            html += '</div></div>'  # Cierra contenedores
            
            st.markdown(html, unsafe_allow_html=True)
            
            # Leyenda
            st.markdown("""
            <div class="legend">
                <div class="legend-item"><div class="legend-color red"></div> Aka (Rojo)</div>
                <div class="legend-item"><div class="legend-color blue"></div> Ao (Azul)</div>
                <div class="legend-item"><div class="legend-color gold"></div> Ganador</div>
                <div class="legend-item"><div class="legend-color bye"></div> BYE</div>
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
        tabs_admin = st.tabs(["📋 Inscripciones", "🏆 Brackets", "📊 Estadísticas"])
        
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
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                
                with st.expander("Gestionar Resultados"):
                    with st.form("edit_brackets"):
                        categorias_b = df_b['Categoria'].unique()
                        cat_b = st.selectbox("Categoría", categorias_b)
                        
                        df_cat_b = df_b[df_b['Categoria'] == cat_b]
                        partido_id = st.selectbox("ID Partido", df_cat_b['Partido_ID'].unique())
                        
                        df_partido = df_cat_b[df_cat_b['Partido_ID'] == partido_id].iloc[0]
                        
                        c1 = df_partido['Competidor1']
                        c2 = df_partido['Competidor2']
                        
                        if c1 and c2 and c1 != "BYE" and c2 != "BYE":
                            ganador = st.radio("Ganador", [c1, c2], index=None)
                            
                            if st.form_submit_button("GUARDAR"):
                                if ganador:
                                    df_b.loc[(df_b['Categoria'] == cat_b) & 
                                            (df_b['Partido_ID'] == partido_id), 'Ganador'] = ganador
                                    if guardar_brackets(df_b):
                                        st.success(f"✅ Ganador: {ganador}")
                                        st.rerun()
                                else:
                                    st.error("Selecciona un ganador")
                        else:
                            st.info("Partido con BYE o vacío")
                
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
    
    elif password:
        st.error("❌ Contraseña incorrecta")
    
    st.markdown('</div>', unsafe_allow_html=True)

# === FOOTER ===
st.markdown("""
<div class="footer">
    <p>© 2024 World Kyokushin Budokai Chile · Todos los derechos reservados</p>
</div>
""", unsafe_allow_html=True)
