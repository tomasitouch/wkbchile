import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import hashlib
import json
import datetime
from datetime import timedelta
import base64
from PIL import Image
import io
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Official Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

# Agrega meta tags para responsive
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

# LINK GOOGLE SHEET
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

# --- 2. SEGURIDAD MEJORADA ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"



# --- ACCESO ADMIN SUPER FÁCIL ---
def render_admin_access():
    """Muestra un botón secreto para acceso admin"""
    # Solo mostrar si NO es admin (si ya es admin, no necesita el botón)
    if not st.session_state.get('is_admin', False):
        # Usamos columnas para ponerlo discretamente en el header
        col1, col2, col3, col4, col5 = st.columns(5)
        with col5:
            # Botón secreto con icono pequeño
            if st.button("🔑", help="Acceso admin (contraseña: admin123)", 
                        use_container_width=True):
                # Mostrar diálogo de contraseña
                with st.popover("🔐 Acceso Administrativo"):
                    st.markdown("#### Ingresa la contraseña admin")
                    password = st.text_input("Contraseña:", type="password", 
                                           placeholder="admin123")
                    
                    if st.button("Ingresar", type="primary"):
                        if check_admin(password):
                            st.session_state.is_admin = True
                            st.success("✅ Acceso concedido!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta")


def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 3. ESTILOS CSS PRO MEJORADO RESPONSIVO CON LLAVES HORIZONTALES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    @keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    @keyframes slideIn { from { transform: translateX(-100%); } to { transform: translateX(0); } }
    
    /* BASE RESPONSIVA */
    .stApp { 
        background-color: #0e1117; 
        color: white; 
        font-family: 'Inter', sans-serif !important;
        min-height: 100vh;
        -webkit-tap-highlight-color: transparent;
    }
    
    h1, h2, h3, h4 { 
        font-family: 'Roboto Condensed', sans-serif !important; 
        text-transform: uppercase; 
        margin-bottom: 1rem !important;
    }
    
    /* HEADER RESPONSIVE MEJORADO */
    .header-container { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 15px 20px; 
        background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; 
        animation: fadeIn 0.5s ease-out; 
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 15px;
    }
    
    .header-title {
        display: flex;
        align-items: center;
        flex: 1;
        min-width: 250px;
    }
    
    .header-sponsors {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        flex: 1;
        min-width: 250px;
    }
    
    .sponsor-logos {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        justify-content: flex-end;
    }
    
    .sponsor-logo { 
        height: 35px; 
        opacity: 0.8; 
        transition: 0.3s; 
        filter: grayscale(100%); 
        max-width: 120px;
    }
    .sponsor-logo:hover { opacity: 1; filter: grayscale(0%); transform: scale(1.05); }
    
    /* BOTONES RESPONSIVOS */
    div.stButton > button {
        width: 100%; 
        background: #1f2937; 
        color: #e5e7eb; 
        border: 1px solid #374151;
        padding: 12px; 
        border-radius: 6px; 
        text-align: left; 
        font-size: clamp(12px, 2vw, 14px); 
        transition: 0.2s;
        font-family: 'Roboto Condensed', sans-serif !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    div.stButton > button:hover { 
        border-color: #ef4444; 
        color: #ef4444; 
        transform: translateX(5px); 
    }
    
    /* BRACKET RESPONSIVE MEJORADO - SIEMPRE HORIZONTAL */
    .bracket-container { 
        overflow-x: auto; 
        overflow-y: hidden;
        padding: 20px 10px; 
        display: flex; 
        justify-content: center; 
        align-items: stretch;
        animation: fadeIn 0.8s ease-out; 
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
        min-height: 500px;
        width: 100%;
        position: relative;
    }
    
    /* Scrollbar personalizada */
    .bracket-container::-webkit-scrollbar {
        height: 8px;
    }
    
    .bracket-container::-webkit-scrollbar-track {
        background: #1a202c;
        border-radius: 4px;
    }
    
    .bracket-container::-webkit-scrollbar-thumb {
        background: linear-gradient(90deg, #ef4444, #FDB931);
        border-radius: 4px;
    }
    
    .bracket-container::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(90deg, #dc2626, #d97706);
    }
    
    /* CONTENEDOR DE ROUNDS HORIZONTALES */
    .rounds-wrapper {
        display: flex;
        justify-content: flex-start;
        align-items: stretch;
        gap: 30px;
        padding: 0 20px;
        min-width: min-content;
    }
    
    .round { 
        min-width: 280px; 
        max-width: 320px;
        margin: 0;
        display: flex; 
        flex-direction: column; 
        justify-content: space-around;
        flex-shrink: 0;
        position: relative;
        background: rgba(31, 41, 55, 0.3);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid rgba(55, 65, 81, 0.5);
    }
    
    /* Titulo de round */
    .round-title {
        text-align: center;
        color: #FDB931;
        font-size: clamp(14px, 1.5vw, 16px);
        font-weight: bold;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #374151;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* INDICADOR LIVE */
    .live-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #ef4444;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 1s infinite;
    }
    
    /* PLAYER BOX MEJORADO CON FOTO */
    .player-box { 
        background: linear-gradient(145deg, #1f2937, #111827); 
        padding: 15px; 
        margin: 10px 0; 
        border-radius: 8px; 
        position: relative; 
        z-index: 2; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); 
        border: 1px solid #374151; 
        transition: all 0.3s ease;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .player-box:hover { 
        transform: translateY(-2px); 
        z-index: 10; 
        border-color: #FDB931;
        box-shadow: 0 6px 20px rgba(253, 185, 49, 0.2);
    }
    
    /* Contenedor para foto y nombre */
    .player-info {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    
    .player-photo {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid;
        flex-shrink: 0;
    }
    
    .photo-red { border-color: #ef4444; }
    .photo-white { border-color: #ffffff; }
    
    .player-name-container {
        flex: 1;
    }
    
    /* AKA / SHIRO MEJORADO */
    .border-red { 
        border-left: 6px solid #ef4444; 
        background: linear-gradient(90deg, rgba(239,68,68,0.15) 0%, rgba(31,41,55,0.9) 60%); 
    }
    
    .border-white { 
        border-left: 6px solid #ffffff; 
        background: linear-gradient(90deg, rgba(255,255,255,0.15) 0%, rgba(31,41,55,0.9) 60%); 
    }
    
    /* TEXT RESPONSIVO */
    .p-name { 
        font-size: clamp(14px, 1.8vw, 16px); 
        font-weight: bold; 
        color: white; 
        margin-bottom: 2px;
        line-height: 1.2;
        word-break: break-word;
    }
    
    .p-details { 
        font-size: clamp(11px, 1.3vw, 13px); 
        color: #9ca3af; 
        display: flex; 
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 5px;
    }
    
    .p-vote-bar { 
        height: 6px; 
        background: #374151; 
        margin-top: 10px; 
        border-radius: 3px; 
        overflow: hidden; 
        position: relative;
    }
    
    .p-vote-fill { 
        height: 100%; 
        transition: width 0.5s ease;
        border-radius: 3px;
    }
    
    /* CHAMPION RESPONSIVE MEJORADO */
    .champion-box { 
        background: linear-gradient(135deg, #FDB931 0%, #d9a024 100%); 
        color: black !important; 
        text-align: center; 
        padding: 25px 15px; 
        border-radius: 10px; 
        font-weight: bold; 
        font-size: clamp(18px, 2.5vw, 22px);
        box-shadow: 0 10px 30px rgba(253, 185, 49, 0.4); 
        animation: fadeIn 1.5s;
        word-break: break-word;
        border: 3px solid rgba(255, 255, 255, 0.2);
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    .champion-box::before {
        content: '🏆';
        font-size: 40px;
        position: absolute;
        opacity: 0.2;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
    }
    
    /* LINES MEJORADAS PARA HORIZONTAL */
    .line-r { 
        position: absolute; 
        right: -25px; 
        width: 25px; 
        height: 2px; 
        background: linear-gradient(90deg, #6b7280, #9ca3af);
        top: 50%; 
        z-index: 1; 
        transform: translateY(-50%);
    }
    
    .conn-v { 
        position: absolute; 
        right: -25px; 
        width: 2px; 
        height: 100px; 
        background: linear-gradient(180deg, #6b7280, #9ca3af);
        top: 50%; 
        z-index: 1; 
        transform: translateY(-50%);
    }
    
    /* CONTENEDORES RESPONSIVOS */
    .category-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        margin: 25px 0;
    }
    
    .vote-buttons-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        margin: 25px 0;
    }
    
    /* FORMULARIOS DE INSCRIPCIÓN */
    .form-container {
        background: linear-gradient(145deg, #1f2937, #111827);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #374151;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    .form-title {
        color: #FDB931;
        font-size: clamp(18px, 2vw, 24px);
        margin-bottom: 20px;
        text-align: center;
        border-bottom: 2px solid #FDB931;
        padding-bottom: 10px;
    }
    
    .form-group {
        margin-bottom: 20px;
    }
    
    .form-label {
        color: #e5e7eb;
        font-weight: 600;
        margin-bottom: 8px;
        display: block;
        font-size: 14px;
    }
    
    .checkbox-group {
        background: rgba(31, 41, 55, 0.5);
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #374151;
        margin: 15px 0;
    }
    
    /* TARJETAS DE PARTICIPANTES */
    .participant-card {
        background: linear-gradient(145deg, #1f2937, #111827);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #374151;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .participant-card:hover {
        border-color: #FDB931;
        transform: translateY(-3px);
    }
    
    .participant-photo {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #FDB931;
        flex-shrink: 0;
    }
    
    .participant-info {
        flex: 1;
    }
    
    .participant-name {
        font-weight: bold;
        font-size: 16px;
        color: white;
        margin-bottom: 5px;
    }
    
    .participant-details {
        font-size: 12px;
        color: #9ca3af;
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }
    
    /* ESTADO DEL TORNEO */
    .tournament-status {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }
    
    .status-open {
        background: linear-gradient(90deg, #10b981, #34d399);
        color: white;
    }
    
    .status-closed {
        background: linear-gradient(90deg, #ef4444, #f87171);
        color: white;
    }
    
    .status-active {
        background: linear-gradient(90deg, #FDB931, #fbbf24);
        color: black;
    }
    
    /* MEJORAS PARA MÓVILES CON BRACKET HORIZONTAL */
    @media (max-width: 1024px) {
        .header-container { 
            flex-direction: column; 
            text-align: center; 
            padding: 15px; 
            gap: 20px;
        }
        
        .header-title, .header-sponsors {
            align-items: center;
            text-align: center;
            width: 100%;
        }
        
        .sponsor-logos {
            justify-content: center;
        }
        
        .bracket-container { 
            min-height: 450px;
            padding: 15px 5px;
        }
        
        .round { 
            min-width: 260px; 
            max-width: 280px;
            padding: 12px;
        }
        
        .player-box {
            min-height: 110px;
            padding: 12px;
        }
        
        .rounds-wrapper {
            gap: 25px;
            padding: 0 15px;
        }
        
        .player-photo {
            width: 35px;
            height: 35px;
        }
    }
    
    @media (max-width: 768px) {
        .bracket-container { 
            min-height: 400px;
        }
        
        .round { 
            min-width: 230px; 
            max-width: 250px;
            padding: 10px;
        }
        
        .rounds-wrapper {
            gap: 20px;
            padding: 0 10px;
        }
        
        .player-box {
            min-height: 100px;
            padding: 10px;
            margin: 8px 0;
        }
        
        .player-photo {
            width: 32px;
            height: 32px;
        }
        
        .p-name { 
            font-size: 13px; 
        }
        
        .p-details { 
            font-size: 11px; 
        }
        
        .champion-box {
            padding: 20px 12px;
            font-size: 18px;
            min-height: 100px;
        }
        
        .category-grid {
            grid-template-columns: 1fr;
            gap: 15px;
        }
        
        .vote-buttons-container {
            grid-template-columns: 1fr;
            gap: 15px;
        }
        
        .form-container {
            padding: 20px;
        }
    }
    
    @media (max-width: 480px) {
        .header-container {
            padding: 12px;
        }
        
        .header-title img {
            height: 40px;
        }
        
        .sponsor-logo {
            height: 25px;
            max-width: 100px;
        }
        
        .bracket-container { 
            min-height: 350px;
            padding: 10px 5px;
        }
        
        .round { 
            min-width: 200px; 
            max-width: 220px;
            padding: 8px;
        }
        
        .rounds-wrapper {
            gap: 15px;
            padding: 0 8px;
        }
        
        .player-box {
            min-height: 90px;
            padding: 8px;
            margin: 6px 0;
        }
        
        .player-photo {
            width: 28px;
            height: 28px;
        }
        
        .p-name { 
            font-size: 12px; 
        }
        
        .p-details { 
            font-size: 10px; 
            flex-direction: column;
            gap: 2px;
        }
        
        .champion-box {
            padding: 15px 10px;
            font-size: 16px;
            min-height: 90px;
        }
        
        .round-title {
            font-size: 13px;
            margin-bottom: 15px;
        }
        
        .line-r {
            right: -20px;
            width: 20px;
        }
        
        .conn-v {
            right: -20px;
        }
    }
    
    /* ORIENTACIÓN HORIZONTAL EN MÓVILES */
    @media (orientation: landscape) and (max-height: 600px) {
        .bracket-container {
            min-height: 300px;
            padding: 8px 5px;
        }
        
        .round {
            min-width: 180px;
            max-width: 200px;
            padding: 6px;
        }
        
        .player-box {
            min-height: 80px;
            padding: 6px;
            margin: 4px 0;
        }
        
        .player-photo {
            width: 25px;
            height: 25px;
        }
        
        .p-name {
            font-size: 11px;
        }
        
        .champion-box {
            min-height: 80px;
            padding: 12px 8px;
            font-size: 14px;
        }
    }
    
    /* TAMAÑOS DE TEXTO RESPONSIVOS */
    .responsive-text-lg { font-size: clamp(18px, 2.5vw, 24px) !important; }
    .responsive-text-md { font-size: clamp(14px, 1.8vw, 18px) !important; }
    .responsive-text-sm { font-size: clamp(12px, 1.2vw, 14px) !important; }
    
    /* ANIMACIONES PARA INSCRIPCIONES */
    .fade-slide {
        animation: slideIn 0.5s ease-out;
    }
    
    /* BOTONES DE ACCIÓN ESPECIALES */
    .action-button {
        background: linear-gradient(135deg, #ef4444, #FDB931);
        color: white;
        border: none;
        padding: 15px 25px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: block;
        width: 100%;
        margin: 20px 0;
    }
    
    .action-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(239, 68, 68, 0.3);
    }
    
    /* MEJORAS DE ACCESIBILIDAD */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 4. GESTIÓN DE DATOS MEJORADA ---

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

# GRADOS DE KARATE
KARATE_GRADES = {
    "1": "Blanco (10º Kyu)",
    "2": "Amarillo (9º Kyu)",
    "3": "Naranja (8º Kyu)",
    "4": "Verde (7º Kyu)",
    "5": "Azul (6º Kyu)",
    "6": "Violeta (5º Kyu)",
    "7": "Marrón (4º-1º Kyu)",
    "8": "Negro (1º-3º Dan)",
    "9": "Negro (4º-6º Dan)",
    "10": "Negro (7º-10º Dan)"
}

# ESTADOS DEL TORNEO
TOURNAMENT_STATUS = {
    "open": "Inscripciones Abiertas",
    "closed": "Inscripciones Cerradas",
    "active": "Torneo Activo"
}

# Clase para limitar votos
class RateLimiter:
    def __init__(self, max_requests=3, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def allow_request(self, user_id, match_id):
        now = datetime.datetime.now()
        key = f"{user_id}_{match_id}"
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Limpiar requests antiguos
        self.requests[key] = [req_time for req_time in self.requests[key] 
                            if now - req_time < timedelta(seconds=self.time_window)]
        
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        return False

rate_limiter = RateLimiter()

@st.cache_data(ttl=30)
def get_initial_df():
    data = []
    matches = ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']
    for cat in ALL_CATS:
        for m in matches:
            data.append({
                "Category": cat, "Match_ID": m, 
                "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P1_Photo": "", "P1_ID": "",
                "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "P2_Photo": "", "P2_ID": "",
                "Winner": None, "Winner_ID": "",
                "Live": False,
                "Round_Completed": False
            })
    return pd.DataFrame(data)

# Datos iniciales para inscripciones
@st.cache_data(ttl=30)
def get_initial_inscriptions_df():
    return pd.DataFrame(columns=[
        "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", 
        "Dojo", "Organizacion", "Telefono", "Email", "Categoria", 
        "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64",
        "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID", "Estado"
    ])

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=15)
def load_data():
    conn = get_connection()
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Brackets", ttl=15)
        if df.empty: 
            df = get_initial_df()
            conn.update(spreadsheet=SHEET_URL, worksheet="Brackets", data=df)
        return df
    except Exception as e:
        st.error(f"Error cargando brackets: {e}")
        return get_initial_df()

@st.cache_data(ttl=15)
def load_inscriptions():
    conn = get_connection()
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones", ttl=15)
        if df.empty:
            df = get_initial_inscriptions_df()
            conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df)
        return df
    except Exception as e:
        st.error(f"Error cargando inscripciones: {e}")
        return get_initial_inscriptions_df()

@st.cache_data(ttl=15)
def load_tournament_status():
    conn = get_connection()
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Config", ttl=15)
        if df.empty:
            df = pd.DataFrame([{"Parametro": "tournament_status", "Valor": "open"}])
            conn.update(spreadsheet=SHEET_URL, worksheet="Config", data=df)
        return df
    except Exception as e:
        st.error(f"Error cargando configuración: {e}")
        return pd.DataFrame([{"Parametro": "tournament_status", "Valor": "open"}])

def save_data(df):
    conn = get_connection()
    try:
        conn.update(spreadsheet=SHEET_URL, worksheet="Brackets", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando brackets: {e}")

def save_inscriptions(df):
    conn = get_connection()
    try:
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando inscripciones: {e}")

def save_tournament_status(status):
    conn = get_connection()
    try:
        df = pd.DataFrame([{"Parametro": "tournament_status", "Valor": status}])
        conn.update(spreadsheet=SHEET_URL, worksheet="Config", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando estado del torneo: {e}")

def get_tournament_status():
    config_df = load_tournament_status()
    status_row = config_df[config_df['Parametro'] == 'tournament_status']
    if not status_row.empty:
        return status_row.iloc[0]['Valor']
    return "open"

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode()

def base64_to_image_html(base64_string, size=40):
    if base64_string and len(base64_string) > 100:  # Verificar que sea una imagen válida
        return f'<img src="data:image/jpeg;base64,{base64_string}" class="player-photo" style="width:{size}px;height:{size}px;">'
    return f'<div class="player-photo" style="width:{size}px;height:{size}px;background:#374151;display:flex;align-items:center;justify-content:center;">🥋</div>'

# Cargar datos
main_df = load_data()
inscriptions_df = load_inscriptions()
tournament_status = get_tournament_status()

# --- 5. FUNCIONES PARA EMPAREJAMIENTO ---
def generate_brackets_for_category(category):
    """Genera brackets automáticos para una categoría basado en los inscritos"""
    # Filtrar inscritos de la categoría con pago confirmado
    category_inscriptions = inscriptions_df[
        (inscriptions_df['Categoria'] == category) & 
        (inscriptions_df['Estado_Pago'] == 'Confirmado') &
        (inscriptions_df['Estado'] == 'Aceptado')
    ].copy()
    
    if len(category_inscriptions) < 2:
        return False, f"Se necesitan al menos 2 participantes para la categoría {category}. Actualmente hay {len(category_inscriptions)}."
    
    # Mezclar participantes aleatoriamente
    participants = category_inscriptions.sample(frac=1).reset_index(drop=True)
    
    # Determinar cuántos matches necesitamos
    num_participants = len(participants)
    
    # Para simplificar, usaremos un sistema de eliminación simple
    # Los primeros 4 van a cuartos, si hay más de 4, los siguientes van a preliminares
    
    # Obtener los matches de esta categoría
    category_matches = main_df[main_df['Category'] == category].copy()
    
    # Limpiar los matches existentes
    for idx in category_matches.index:
        main_df.at[idx, 'P1_Name'] = ""
        main_df.at[idx, 'P1_Dojo'] = ""
        main_df.at[idx, 'P1_Votes'] = 0
        main_df.at[idx, 'P1_Photo'] = ""
        main_df.at[idx, 'P1_ID'] = ""
        main_df.at[idx, 'P2_Name'] = ""
        main_df.at[idx, 'P2_Dojo'] = ""
        main_df.at[idx, 'P2_Votes'] = 0
        main_df.at[idx, 'P2_Photo'] = ""
        main_df.at[idx, 'P2_ID'] = ""
        main_df.at[idx, 'Winner'] = ""
        main_df.at[idx, 'Winner_ID'] = ""
        main_df.at[idx, 'Round_Completed'] = False
    
    # Asignar participantes a los cuartos
    quarter_matches = ['Q1', 'Q2', 'Q3', 'Q4']
    
    for i, match_id in enumerate(quarter_matches):
        if i * 2 < len(participants):
            # Primer participante
            p1_idx = i * 2
            p1 = participants.iloc[p1_idx]
            
            match_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == match_id)].index[0]
            main_df.at[match_idx, 'P1_Name'] = p1['Nombre_Completo']
            main_df.at[match_idx, 'P1_Dojo'] = p1['Dojo']
            main_df.at[match_idx, 'P1_Photo'] = p1.get('Foto_Base64', '')
            main_df.at[match_idx, 'P1_ID'] = p1['ID']
        
        if i * 2 + 1 < len(participants):
            # Segundo participante
            p2_idx = i * 2 + 1
            p2 = participants.iloc[p2_idx]
            
            match_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == match_id)].index[0]
            main_df.at[match_idx, 'P2_Name'] = p2['Nombre_Completo']
            main_df.at[match_idx, 'P2_Dojo'] = p2['Dojo']
            main_df.at[match_idx, 'P2_Photo'] = p2.get('Foto_Base64', '')
            main_df.at[match_idx, 'P2_ID'] = p2['ID']
    
    # Guardar cambios
    save_data(main_df)
    
    return True, f"Brackets generados para {category}. {len(participants)} participantes emparejados."

def update_match_winner(category, match_id, winner_id):
    """Actualiza el ganador de un match y lo propaga al siguiente round"""
    # Buscar el match
    match_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == match_id)].index
    
    if len(match_idx) == 0:
        return False
    
    match_idx = match_idx[0]
    match_data = main_df.iloc[match_idx]
    
    # Determinar quién ganó
    if match_data['P1_ID'] == winner_id:
        winner_name = match_data['P1_Name']
        winner_dojo = match_data['P1_Dojo']
        winner_photo = match_data['P1_Photo']
    elif match_data['P2_ID'] == winner_id:
        winner_name = match_data['P2_Name']
        winner_dojo = match_data['P2_Dojo']
        winner_photo = match_data['P2_Photo']
    else:
        return False
    
    # Actualizar el match actual
    main_df.at[match_idx, 'Winner'] = winner_name
    main_df.at[match_idx, 'Winner_ID'] = winner_id
    main_df.at[match_idx, 'Round_Completed'] = True
    
    # Propagar al siguiente round si es necesario
    if match_id.startswith('Q'):  # Cuartos -> Semifinales
        q_num = int(match_id[1])
        if q_num in [1, 2]:
            next_match_id = 'S1'
            if q_num == 1:
                position = 'P1'
            else:  # q_num == 2
                position = 'P2'
        elif q_num in [3, 4]:
            next_match_id = 'S2'
            if q_num == 3:
                position = 'P1'
            else:  # q_num == 4
                position = 'P2'
        
        # Buscar el match de semifinales
        next_match_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == next_match_id)].index
        if len(next_match_idx) > 0:
            next_match_idx = next_match_idx[0]
            main_df.at[next_match_idx, f'{position}_Name'] = winner_name
            main_df.at[next_match_idx, f'{position}_Dojo'] = winner_dojo
            main_df.at[next_match_idx, f'{position}_Photo'] = winner_photo
            main_df.at[next_match_idx, f'{position}_ID'] = winner_id
    
    elif match_id.startswith('S'):  # Semifinales -> Final
        s_num = int(match_id[1])
        next_match_id = 'F1'
        position = 'P1' if s_num == 1 else 'P2'
        
        # Buscar el match final
        next_match_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == next_match_id)].index
        if len(next_match_idx) > 0:
            next_match_idx = next_match_idx[0]
            main_df.at[next_match_idx, f'{position}_Name'] = winner_name
            main_df.at[next_match_idx, f'{position}_Dojo'] = winner_dojo
            main_df.at[next_match_idx, f'{position}_Photo'] = winner_photo
            main_df.at[next_match_idx, f'{position}_ID'] = winner_id
    
    # Guardar cambios
    save_data(main_df)
    return True

# --- 6. NAVEGACIÓN MEJORADA ---
if 'view' not in st.session_state: 
    st.session_state.view = "HOME"
if 'cat' not in st.session_state: 
    st.session_state.cat = None
if 'page' not in st.session_state: 
    st.session_state.page = 0
if 'voted_matches' not in st.session_state: 
    st.session_state.voted_matches = set()
if 'inscription_type' not in st.session_state: 
    st.session_state.inscription_type = "individual"
if 'group_participants' not in st.session_state: 
    st.session_state.group_participants = []
if 'current_participant' not in st.session_state: 
    st.session_state.current_participant = {}
if 'inscription_step' not in st.session_state: 
    st.session_state.inscription_step = 1
if 'payment_code' not in st.session_state: 
    st.session_state.payment_code = ""

def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

# --- HEADER MEJORADO RESPONSIVO ---
def render_header():
    logo_org = "https://cdn-icons-png.flaticon.com/512/1603/1603754.png" 
    logo_spon1 = "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg" 
    logo_spon2 = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
    
    # Mostrar estado del torneo
    status_display = TOURNAMENT_STATUS.get(tournament_status, "Inscripciones Abiertas")
    status_class = f"status-{tournament_status}"
    
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">
            <img src="{logo_org}" height="50" style="margin-right:15px; filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));">
            <div>
                <h2 style="margin:0; color:white;" class="responsive-text-md">WKB CHILE</h2>
                <small style="color:#FDB931; font-weight:bold; letter-spacing: 1px;" class="responsive-text-sm">OFFICIAL TOURNAMENT HUB</small>
            </div>
        </div>
        <div class="header-sponsors">
            <div class="tournament-status {status_class}" style="margin-bottom: 8px; padding: 8px 15px; border-radius: 6px;">
                {status_display}
            </div>
            <div style="color:#666; font-size:10px; margin-bottom:5px; letter-spacing:1px;">POWERED BY</div>
            <div class="sponsor-logos">
                <img src="{logo_spon1}" class="sponsor-logo">
                <img src="{logo_spon2}" class="sponsor-logo">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 7. FUNCIONES PARA INSCRIPCIÓN ---
def generate_payment_code():
    import random
    import string
    return 'WKB' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def save_participant(participant_data, inscription_type, group_id=None):
    """Guarda un participante en la base de datos"""
    try:
        # Generar ID único
        import uuid
        participant_id = str(uuid.uuid4())[:8]
        
        # Preparar datos
        new_participant = {
            "ID": participant_id,
            "Nombre_Completo": participant_data["nombre_completo"],
            "Edad": participant_data["edad"],
            "Peso": participant_data["peso"],
            "Estatura": participant_data["estatura"],
            "Grado": participant_data["grado"],
            "Dojo": participant_data["dojo"],
            "Organizacion": participant_data["organizacion"],
            "Telefono": participant_data["telefono"],
            "Email": participant_data["email"],
            "Categoria": participant_data["categoria"],
            "Tipo_Inscripcion": inscription_type,
            "Codigo_Pago": st.session_state.payment_code,
            "Fecha_Inscripcion": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Foto_Base64": participant_data.get("foto_base64", ""),
            "Consentimiento": participant_data["consentimiento"],
            "Descargo": participant_data["descargo"],
            "Estado_Pago": "Pendiente",
            "Grupo_ID": group_id if inscription_type == "colectivo" else "",
            "Estado": "Pendiente"  # Pendiente, Aceptado, Rechazado
        }
        
        # Añadir al dataframe
        global inscriptions_df
        new_row = pd.DataFrame([new_participant])
        inscriptions_df = pd.concat([inscriptions_df, new_row], ignore_index=True)
        
        # Guardar en Google Sheets
        save_inscriptions(inscriptions_df)
        
        return participant_id
    except Exception as e:
        st.error(f"Error guardando participante: {e}")
        return None

def calculate_price(participants_count):
    """Calcula el precio según el número de participantes"""
    base_price = 50000  # $50.000 CLP por persona
    if participants_count >= 5:
        return base_price * participants_count * 0.8  # 20% descuento
    elif participants_count >= 3:
        return base_price * participants_count * 0.9  # 10% descuento
    else:
        return base_price * participants_count

# --- 8. VISTA HOME MEJORADA ---
if st.session_state.view == "HOME":
    render_header()
    render_admin_access()
    
    # Mostrar mensaje según estado del torneo
    if tournament_status == "closed":
        st.warning("⚠️ **INSCRIPCIONES CERRADAS** - El período de inscripción ha finalizado. El torneo comenzará pronto.")
    elif tournament_status == "active":
        st.success("🏆 **TORNEO EN CURSO** - Sigue las llaves y vota por tus favoritos.")
    
    # Navegación principal
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 TORNEO", "📝 INSCRIPCIÓN", "👥 PARTICIPANTES", "📊 ESTADÍSTICAS"])
    
    with tab1:
        st.markdown("### 📂 SELECCIONA TU CATEGORÍA")
        
        # Solo mostrar categorías si el torneo está activo o hay brackets
        if tournament_status == "active" or tournament_status == "closed":
            # PAGINACIÓN RESPONSIVA
            CATEGORIES_PER_PAGE = 8
            total_categories = len(ALL_CATS)
            total_pages = (total_categories + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE
            
            # Control de páginas responsivo
            col_prev, col_page, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.session_state.page > 0:
                    if st.button("◀ Anterior", use_container_width=True):
                        st.session_state.page -= 1
                        st.rerun()
            
            with col_page:
                st.markdown(f"<div style='text-align:center; color:#666; font-size:14px;'>Página {st.session_state.page + 1} de {total_pages}</div>", 
                           unsafe_allow_html=True)
            
            with col_next:
                if st.session_state.page < total_pages - 1:
                    if st.button("Siguiente ▶", use_container_width=True):
                        st.session_state.page += 1
                        st.rerun()
            
            # Mostrar categorías de la página actual
            start_idx = st.session_state.page * CATEGORIES_PER_PAGE
            end_idx = min(start_idx + CATEGORIES_PER_PAGE, total_categories)
            
            # Separar categorías por tipo
            current_cats = ALL_CATS[start_idx:end_idx]
            kumite_men = [cat for cat in current_cats if "KUMITE - MEN" in cat]
            kumite_women = [cat for cat in current_cats if "KUMITE - WOMEN" in cat]
            kata_cats = [cat for cat in current_cats if "KATA" in cat]
            
            # Mostrar categorías con diseño responsivo
            if kumite_men or kumite_women:
                with st.expander("👊 KUMITE SENIORS", expanded=True):
                    if kumite_men:
                        st.markdown("<div style='color:#ef4444; margin-bottom:10px; font-weight:bold; font-size:16px;'>MEN</div>", unsafe_allow_html=True)
                        st.markdown('<div class="category-grid">', unsafe_allow_html=True)
                        for idx, w in enumerate(kumite_men):
                            weight_class = w.split("| ")[-1]
                            
                            # Contar inscritos en esta categoría
                            inscritos_cat = inscriptions_df[
                                (inscriptions_df['Categoria'] == w) & 
                                (inscriptions_df['Estado'] == 'Aceptado')
                            ]
                            count = len(inscritos_cat)
                            
                            if st.button(f"{weight_class} ({count})", key=f"m_{w}_{idx}", use_container_width=True):
                                go("BRACKET", w)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    if kumite_women:
                        st.markdown("<div style='color:#ef4444; margin-top:20px; margin-bottom:10px; font-weight:bold; font-size:16px;'>WOMEN</div>", unsafe_allow_html=True)
                        st.markdown('<div class="category-grid">', unsafe_allow_html=True)
                        for idx, w in enumerate(kumite_women):
                            weight_class = w.split("| ")[-1]
                            
                            # Contar inscritos en esta categoría
                            inscritos_cat = inscriptions_df[
                                (inscriptions_df['Categoria'] == w) & 
                                (inscriptions_df['Estado'] == 'Aceptado')
                            ]
                            count = len(inscritos_cat)
                            
                            if st.button(f"{weight_class} ({count})", key=f"w_{w}_{idx}", use_container_width=True):
                                go("BRACKET", w)
                        st.markdown('</div>', unsafe_allow_html=True)
            
            if kata_cats:
                with st.expander("🙏 KATA", expanded=True):
                    st.markdown('<div class="category-grid">', unsafe_allow_html=True)
                    for idx, cat in enumerate(kata_cats):
                        category_name = cat.split("| ")[-1]
                        
                        # Contar inscritos en esta categoría
                        inscritos_cat = inscriptions_df[
                            (inscriptions_df['Categoria'] == cat) & 
                            (inscriptions_df['Estado'] == 'Aceptado')
                        ]
                        count = len(inscritos_cat)
                        
                        if st.button(f"{category_name} ({count})", key=f"k_{cat}_{idx}", use_container_width=True):
                            go("BRACKET", cat)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📢 El torneo comenzará una vez que se cierren las inscripciones. ¡Inscríbete ahora!")
    
    with tab2:
        st.markdown("### 📝 SISTEMA DE INSCRIPCIÓN")
        
        # Verificar si las inscripciones están abiertas
        if tournament_status != "open":
            st.error("❌ **INSCRIPCIONES CERRADAS** - El período de inscripción ha finalizado.")
        else:
            # Selección tipo de inscripción
            inscription_type = st.radio(
                "Selecciona el tipo de inscripción:",
                ["Individual", "Colectiva"],
                horizontal=True,
                key="inscription_type_radio"
            )
            
            st.session_state.inscription_type = "individual" if inscription_type == "Individual" else "colectivo"
            
            if st.session_state.inscription_type == "colectivo":
                st.info("💡 **Inscripción Colectiva:** Puedes agregar múltiples participantes y realizar un solo pago. Descuentos disponibles para grupos de 3 o más personas.")
            
            # Paso 1: Información del participante
            if st.session_state.inscription_step == 1:
                st.markdown("#### 👤 INFORMACIÓN DEL PARTICIPANTE")
                
                with st.container():
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nombre_completo = st.text_input("Nombre Completo *", placeholder="Ej: Juan Pérez González")
                        edad = st.number_input("Edad *", min_value=5, max_value=80, value=18)
                        peso = st.number_input("Peso (kg) *", min_value=30.0, max_value=150.0, value=70.0, step=0.1)
                        estatura = st.number_input("Estatura (cm) *", min_value=100, max_value=220, value=170)
                    
                    with col2:
                        grado = st.selectbox("Grado *", options=list(KARATE_GRADES.keys()), 
                                            format_func=lambda x: f"{x} - {KARATE_GRADES[x]}")
                        dojo = st.text_input("Dojo/Club *", placeholder="Ej: Dojo Zen")
                        organizacion = st.text_input("Organización *", placeholder="Ej: Federación Chilena de Karate")
                        telefono = st.text_input("Teléfono Contacto *", placeholder="+56912345678")
                        email = st.text_input("Email *", placeholder="ejemplo@email.com")
                    
                    # Selección de categoría
                    st.markdown("#### 🏆 CATEGORÍA DE COMPETENCIA")
                    categoria_opciones = []
                    for cat in ALL_CATS:
                        categoria_opciones.append(cat)
                    
                    categoria = st.selectbox("Selecciona tu categoría *", options=categoria_opciones)
                    
                    # Carga de foto
                    st.markdown("#### 📸 FOTO CARNET (Requerida)")
                    uploaded_file = st.file_uploader("Sube tu foto frontal estilo carnet actualizada (máx. 5MB)", 
                                                   type=['jpg', 'jpeg', 'png'])
                    
                    foto_base64 = ""
                    if uploaded_file is not None:
                        try:
                            # Verificar tamaño
                            if uploaded_file.size > 5 * 1024 * 1024:  # 5MB
                                st.error("La imagen es muy grande. Máximo 5MB.")
                            else:
                                image = Image.open(uploaded_file)
                                # Redimensionar si es muy grande
                                if image.size[0] > 800 or image.size[1] > 800:
                                    image.thumbnail((800, 800))
                                
                                foto_base64 = image_to_base64(image)
                                
                                col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
                                with col_img2:
                                    st.image(image, caption="Previsualización de foto", width=200)
                        except Exception as e:
                            st.error(f"Error procesando la imagen: {e}")
                    
                    # Documentos legales
                    st.markdown("#### 📄 DOCUMENTACIÓN LEGAL")
                    
                    with st.container():
                        consentimiento = st.checkbox(
                            "✅ **Consentimiento Informado:** Autorizo el tratamiento de mis datos personales "
                            "para fines de participación en el torneo y acepto las condiciones del evento.",
                            key="consentimiento"
                        )
                        
                        descargo = st.checkbox(
                            "✅ **Descargo de Responsabilidad:** Eximo a los organizadores de cualquier "
                            "responsabilidad por lesiones que pudiera sufrir durante mi participación.",
                            key="descargo"
                        )
                    
                    # Validación antes de continuar
                    if st.button("💾 GUARDAR PARTICIPANTE", type="primary", use_container_width=True):
                        if not all([nombre_completo, dojo, organizacion, telefono, email, categoria]):
                            st.error("Por favor completa todos los campos obligatorios (*)")
                        elif not (consentimiento and descargo):
                            st.error("Debes aceptar ambos documentos legales para continuar")
                        elif not foto_base64:
                            st.error("Debes subir una foto carnet para continuar")
                        else:
                            # Guardar datos del participante
                            participant_data = {
                                "nombre_completo": nombre_completo,
                                "edad": edad,
                                "peso": peso,
                                "estatura": estatura,
                                "grado": grado,
                                "dojo": dojo,
                                "organizacion": organizacion,
                                "telefono": telefono,
                                "email": email,
                                "categoria": categoria,
                                "foto_base64": foto_base64,
                                "consentimiento": consentimiento,
                                "descargo": descargo
                            }
                            
                            if st.session_state.inscription_type == "individual":
                                # Para individual, proceder directamente al pago
                                st.session_state.current_participant = participant_data
                                st.session_state.inscription_step = 2
                                st.rerun()
                            else:
                                # Para colectivo, agregar a la lista
                                if 'group_participants' not in st.session_state:
                                    st.session_state.group_participants = []
                                
                                st.session_state.group_participants.append(participant_data)
                                st.session_state.current_participant = {}
                                
                                st.success(f"✅ Participante agregado. Total: {len(st.session_state.group_participants)}")
                                st.markdown("---")
                
                # Para inscripción colectiva, botón para finalizar agregación
                if st.session_state.inscription_type == "colectivo" and len(st.session_state.group_participants) > 0:
                    st.markdown("---")
                    
                    # Mostrar participantes agregados
                    st.markdown("#### 📋 PARTICIPANTES AGREGADOS")
                    for i, p in enumerate(st.session_state.group_participants, 1):
                        col_info, col_action = st.columns([4, 1])
                        with col_info:
                            st.markdown(f"**{i}. {p['nombre_completo']}** - {p['categoria']} - {p['dojo']}")
                        with col_action:
                            if st.button("🗑️", key=f"remove_{i}"):
                                st.session_state.group_participants.pop(i-1)
                                st.rerun()
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("🚀 PROCEDER AL PAGO COLECTIVO", type="primary", use_container_width=True):
                            st.session_state.inscription_step = 2
                            st.rerun()
            
            # Paso 2: Pago
            elif st.session_state.inscription_step == 2:
                st.markdown("#### 💳 SISTEMA DE PAGO")
                
                # Calcular total
                if st.session_state.inscription_type == "individual":
                    total_participants = 1
                    participants_list = [st.session_state.current_participant]
                else:
                    total_participants = len(st.session_state.group_participants)
                    participants_list = st.session_state.group_participants
                
                total_price = calculate_price(total_participants)
                
                # Mostrar resumen
                st.markdown(f"""
                <div style='background: #1f2937; padding: 20px; border-radius: 10px; border-left: 5px solid #FDB931;'>
                    <h4 style='margin-top: 0; color: #FDB931;'>RESUMEN DE INSCRIPCIÓN</h4>
                    <p><strong>Tipo:</strong> {st.session_state.inscription_type.upper()}</p>
                    <p><strong>Participantes:</strong> {total_participants}</p>
                    <p><strong>Total a pagar:</strong> <span style='color: #FDB931; font-size: 24px;'>${total_price:,.0f} CLP</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Detalles de participantes
                with st.expander("📋 Ver detalles de participantes", expanded=False):
                    for i, p in enumerate(participants_list, 1):
                        st.markdown(f"**{i}. {p['nombre_completo']}** - {p['categoria']} - {p['dojo']}")
                
                # Método de pago temporal (código)
                st.markdown("---")
                st.markdown("#### 🔒 PAGO CON CÓDIGO")
                st.info("⚠️ **SISTEMA TEMPORAL:** Por ahora, ingresa el código de pago que te proporcionó la organización. Pronto integraremos MercadoPago.")
                
                payment_code = st.text_input("Código de Pago *", placeholder="Ej: WKB2024XYZ", 
                                            help="Código de 8-10 caracteres proporcionado por la organización")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔙 VOLVER", use_container_width=True):
                        st.session_state.inscription_step = 1
                        st.rerun()
                
                with col2:
                    if st.button("✅ CONFIRMAR PAGO", type="primary", use_container_width=True):
                        if not payment_code:
                            st.error("Debes ingresar un código de pago")
                        else:
                            st.session_state.payment_code = payment_code
                            
                            # Generar grupo ID para inscripciones colectivas
                            group_id = None
                            if st.session_state.inscription_type == "colectivo":
                                import random
                                import string
                                group_id = 'GRP_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                            
                            # Guardar todos los participantes
                            saved_ids = []
                            for participant in participants_list:
                                participant_id = save_participant(participant, st.session_state.inscription_type, group_id)
                                if participant_id:
                                    saved_ids.append(participant_id)
                            
                            if len(saved_ids) == len(participants_list):
                                st.session_state.inscription_step = 3
                                st.rerun()
                            else:
                                st.error("Error al guardar algunos participantes")
            
            # Paso 3: Confirmación
            elif st.session_state.inscription_step == 3:
                st.markdown("""
                <div style='text-align: center; padding: 40px 20px;'>
                    <h1 style='color: #FDB931;'>✅ INSCRIPCIÓN EXITOSA</h1>
                    <p style='font-size: 18px;'>Tu inscripción ha sido procesada correctamente.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Mostrar detalles
                if st.session_state.inscription_type == "individual":
                    p = st.session_state.current_participant
                    st.markdown(f"""
                    <div style='background: #1f2937; padding: 25px; border-radius: 10px; margin: 20px 0;'>
                        <h4 style='color: #FDB931;'>DETALLES DE TU INSCRIPCIÓN</h4>
                        <p><strong>Participante:</strong> {p['nombre_completo']}</p>
                        <p><strong>Categoría:</strong> {p['categoria']}</p>
                        <p><strong>Código de Pago:</strong> <code>{st.session_state.payment_code}</code></p>
                        <p><strong>Estado:</strong> <span style='color: #FDB931;'>Pendiente de verificación</span></p>
                        <p style='font-size: 12px; color: #9ca3af; margin-top: 15px;'>
                            Recibirás un correo de confirmación una vez que tu pago sea verificado.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: #1f2937; padding: 25px; border-radius: 10px; margin: 20px 0;'>
                        <h4 style='color: #FDB931;'>INSCRIPCIÓN COLECTIVA COMPLETADA</h4>
                        <p><strong>Total de participantes:</strong> {len(st.session_state.group_participants)}</p>
                        <p><strong>Código de Pago:</strong> <code>{st.session_state.payment_code}</code></p>
                        <p><strong>Estado:</strong> <span style='color: #FDB931;'>Pendiente de verificación</span></p>
                        <p style='font-size: 12px; color: #9ca3af; margin-top: 15px;'>
                            Recibirás un correo de confirmación una vez que tu pago sea verificado.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🏠 VOLVER AL INICIO", type="primary", use_container_width=True):
                        # Resetear estado
                        st.session_state.inscription_step = 1
                        st.session_state.current_participant = {}
                        st.session_state.group_participants = []
                        st.session_state.payment_code = ""
                        st.rerun()
    
    with tab3:
        st.markdown("### 👥 LISTA DE PARTICIPANTES")
        
        if tournament_status == "open":
            st.info("👀 La lista de participantes se mostrará una vez que se cierren las inscripciones.")
        else:
            # Filtrar participantes aceptados
            accepted_participants = inscriptions_df[inscriptions_df['Estado'] == 'Aceptado'].copy()
            
            if accepted_participants.empty:
                st.info("No hay participantes confirmados aún.")
            else:
                # Mostrar estadísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Participantes", len(accepted_participants))
                with col2:
                    individuales = len(accepted_participants[accepted_participants['Tipo_Inscripcion'] == 'individual'])
                    st.metric("Individuales", individuales)
                with col3:
                    colectivos = len(accepted_participants[accepted_participants['Tipo_Inscripcion'] == 'colectivo'])
                    st.metric("Colectivos", colectivos)
                
                # Selector de categoría
                categorias_disponibles = sorted(accepted_participants['Categoria'].unique())
                categoria_seleccionada = st.selectbox("Filtrar por categoría:", ["Todas"] + list(categorias_disponibles))
                
                if categoria_seleccionada != "Todas":
                    filtered_participants = accepted_participants[accepted_participants['Categoria'] == categoria_seleccionada]
                else:
                    filtered_participants = accepted_participants
                
                # Mostrar participantes
                st.markdown(f"#### 📋 Participantes ({len(filtered_participants)})")
                
                for _, participante in filtered_participants.iterrows():
                    # Crear tarjeta de participante
                    photo_html = ""
                    if participante.get('Foto_Base64'):
                        photo_html = f'<img src="data:image/jpeg;base64,{participante["Foto_Base64"]}" class="participant-photo">'
                    else:
                        photo_html = '<div class="participant-photo">🥋</div>'
                    
                    st.markdown(f"""
                    <div class="participant-card">
                        {photo_html}
                        <div class="participant-info">
                            <div class="participant-name">{participante['Nombre_Completo']}</div>
                            <div class="participant-details">
                                <span>🏆 {participante['Categoria'].split('|')[-1]}</span>
                                <span>🥋 {participante['Dojo']}</span>
                                <span>📞 {participante['Telefono']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 📊 ESTADÍSTICAS DEL TORNEO")
        
        if st.session_state.get('is_admin', False):
            # Estadísticas de inscripciones para admin
            st.subheader("📈 ESTADÍSTICAS DE INSCRIPCIONES")
            
            if not inscriptions_df.empty:
                # Totales
                col1, col2, col3 = st.columns(3)
                with col1:
                    total = len(inscriptions_df)
                    st.metric("Total Inscritos", total)
                with col2:
                    pendientes = len(inscriptions_df[inscriptions_df['Estado'] == 'Pendiente'])
                    st.metric("Pendientes", pendientes)
                with col3:
                    aceptados = len(inscriptions_df[inscriptions_df['Estado'] == 'Aceptado'])
                    st.metric("Aceptados", aceptados)
                
                # Gráfico por categoría
                st.subheader("📊 DISTRIBUCIÓN POR CATEGORÍA")
                inscripciones_por_categoria = inscriptions_df['Categoria'].value_counts()
                if not inscripciones_por_categoria.empty:
                    st.bar_chart(inscripciones_por_categoria)
                
                # Lista completa de inscritos
                with st.expander("📋 LISTA COMPLETA DE INSCRITOS", expanded=False):
                    display_cols = ['Nombre_Completo', 'Categoria', 'Dojo', 'Estado_Pago', 'Estado', 'Fecha_Inscripcion']
                    st.dataframe(inscriptions_df[display_cols], use_container_width=True)
            else:
                st.info("No hay inscripciones registradas aún.")
        
        # Estadísticas de votos
        st.subheader("🔥 PARTIDOS MÁS VOTADOS")
        main_df['Total_Votes'] = main_df['P1_Votes'] + main_df['P2_Votes']
        top_matches = main_df.nlargest(5, 'Total_Votes')[['Category', 'Match_ID', 'Total_Votes']]
        st.dataframe(top_matches, use_container_width=True)
    
    # Recarga automática
    st.html("<script>setTimeout(function(){window.location.reload();}, 60000);</script>")

# --- 9. VISTA BRACKET MEJORADA ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    cat_df = main_df[main_df['Category'] == cat].set_index('Match_ID')
    
    def get_row(mid): 
        try: return cat_df.loc[mid]
        except: return pd.Series()
    
    def get_val(row, col): 
        return row[col] if col in row and pd.notna(row[col]) and row[col] != "" else "Por Definir"
    
    def generate_share_link():
        import urllib.parse
        base_url = "https://wkb-hub.streamlit.app/"
        params = {"category": urllib.parse.quote(cat)}
        return f"{base_url}?{params}"

    render_header()
    
    # Barra Superior Mejorada
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 INICIO", use_container_width=True):
            go("HOME")
    with col2:
        # Obtener número de participantes en esta categoría
        inscritos_cat = inscriptions_df[
            (inscriptions_df['Categoria'] == cat) & 
            (inscriptions_df['Estado'] == 'Aceptado')
        ]
        count_participants = len(inscritos_cat)
        
        st.markdown(f"<h3 style='text-align:center; color:#FDB931; margin-top:0;' class='responsive-text-md'>{cat}</h3>", 
                   unsafe_allow_html=True)
        st.caption(f"👥 {count_participants} participantes | 🏆 Llaves del torneo")
    with col3:
        share_link = generate_share_link()
        st.markdown(f"""
        <div style='text-align:right;'>
            <span style='color:#666; font-size:12px;'>SHARE:</span><br>
            <a href='{share_link}' target='_blank' style='color:#FDB931; text-decoration:none; font-size:12px;'>
                🔗 COPIAR LINK
            </a>
        </div>
        """, unsafe_allow_html=True)

    # --- PANEL ADMIN MEJORADO ---
    with st.sidebar:
        st.header("🔧 Panel de Control")
        
        if 'dark_mode' not in st.session_state:
            st.session_state.dark_mode = True
        
        if st.toggle("🌙 Modo Oscuro / ☀️ Modo Claro", value=st.session_state.dark_mode):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
        
        if 'is_admin' not in st.session_state: 
            st.session_state.is_admin = False
        
        if not st.session_state.is_admin:
            st.subheader("Acceso Admin")
            admin_pass = st.text_input("Contraseña", type="password")
            if st.button("🔓 Entrar", use_container_width=True) and check_admin(admin_pass):
                st.session_state.is_admin = True
                st.rerun()
        else:
            st.success("✅ Editor Activo")
            
            if st.button("🚪 Salir", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
            
            # Control del torneo
            st.subheader("🎯 CONTROL DEL TORNEO")
            
            current_status = get_tournament_status()
            new_status = st.selectbox(
                "Estado del Torneo",
                options=["open", "closed", "active"],
                format_func=lambda x: TOURNAMENT_STATUS[x],
                index=["open", "closed", "active"].index(current_status) if current_status in ["open", "closed", "active"] else 0
            )
            
            if new_status != current_status:
                if st.button("💾 Actualizar Estado", use_container_width=True):
                    save_tournament_status(new_status)
                    st.success(f"Estado actualizado a: {TOURNAMENT_STATUS[new_status]}")
                    time.sleep(1)
                    st.rerun()
            
            # Generar brackets para esta categoría
            if new_status == "active" or new_status == "closed":
                st.subheader("🎲 GENERAR BRACKETS")
                
                # Contar participantes en esta categoría
                inscritos_cat = inscriptions_df[
                    (inscriptions_df['Categoria'] == cat) & 
                    (inscriptions_df['Estado'] == 'Aceptado')
                ]
                
                st.metric("Participantes Aceptados", len(inscritos_cat))
                
                if len(inscritos_cat) >= 2:
                    if st.button("🎯 Generar Llaves", use_container_width=True):
                        with st.spinner("Generando brackets..."):
                            success, message = generate_brackets_for_category(cat)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                            time.sleep(2)
                            st.rerun()
                else:
                    st.warning("Se necesitan al menos 2 participantes aceptados para generar brackets.")
            
            # Gestión de inscripciones para esta categoría
            st.subheader("👥 GESTIÓN DE INSCRIPCIONES")
            if not inscriptions_df.empty:
                inscritos_categoria = inscriptions_df[inscriptions_df['Categoria'] == cat]
                
                if not inscritos_categoria.empty:
                    # Filtros
                    estado_filtro = st.selectbox("Filtrar por estado:", ["Todos", "Pendiente", "Aceptado", "Rechazado"])
                    
                    if estado_filtro != "Todos":
                        inscritos_filtrados = inscritos_categoria[inscritos_categoria['Estado'] == estado_filtro]
                    else:
                        inscritos_filtrados = inscritos_categoria
                    
                    st.metric(f"Inscritos ({estado_filtro})", len(inscritos_filtrados))
                    
                    with st.expander("📋 Gestionar inscritos", expanded=False):
                        for idx, row in inscritos_filtrados.iterrows():
                            col_info, col_accion = st.columns([3, 1])
                            with col_info:
                                st.markdown(f"**{row['Nombre_Completo']}**")
                                st.caption(f"{row['Dojo']} | {row['Estado']}")
                            with col_accion:
                                if row['Estado'] == 'Pendiente':
                                    if st.button("✅", key=f"accept_{row['ID']}"):
                                        inscriptions_df.at[idx, 'Estado'] = 'Aceptado'
                                        inscriptions_df.at[idx, 'Estado_Pago'] = 'Confirmado'
                                        save_inscriptions(inscriptions_df)
                                        st.success(f"{row['Nombre_Completo']} aceptado!")
                                        time.sleep(1)
                                        st.rerun()
                                    if st.button("❌", key=f"reject_{row['ID']}"):
                                        inscriptions_df.at[idx, 'Estado'] = 'Rechazado'
                                        save_inscriptions(inscriptions_df)
                                        st.warning(f"{row['Nombre_Completo']} rechazado!")
                                        time.sleep(1)
                                        st.rerun()
            
            # Editor de matches
            if tournament_status == "active":
                st.subheader("✏️ EDITAR RESULTADOS")
                match_edit = st.selectbox("Seleccionar match", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
                
                row = get_row(match_edit)
                if not row.empty:
                    # Mostrar participantes del match
                    p1_name = get_val(row, 'P1_Name')
                    p2_name = get_val(row, 'P2_Name')
                    
                    if p1_name != "Por Definir" and p2_name != "Por Definir":
                        st.markdown(f"**{p1_name}** vs **{p2_name}**")
                        
                        # Seleccionar ganador
                        winner_options = ["", p1_name, p2_name]
                        current_winner = get_val(row, 'Winner')
                        winner_idx = winner_options.index(current_winner) if current_winner in winner_options else 0
                        
                        winner = st.selectbox("Seleccionar ganador", winner_options, index=winner_idx)
                        
                        if winner and st.button("💾 Guardar Resultado", use_container_width=True):
                            # Determinar ID del ganador
                            if winner == p1_name:
                                winner_id = row['P1_ID']
                            else:
                                winner_id = row['P2_ID']
                            
                            success = update_match_winner(cat, match_edit, winner_id)
                            if success:
                                st.success("✅ Resultado guardado!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Error al guardar resultado")
                    else:
                        st.info("Este match aún no tiene participantes asignados.")

    # --- VOTACIÓN MEJORADA (SOLO SI EL TORNEO ESTÁ ACTIVO) ---
    if tournament_status == "active":
        st.markdown("##### 📊 PREDICCIÓN DEL PÚBLICO (EN VIVO)")
        
        def vote(mid, player_col, player_name):
            vote_key = f"{cat}_{mid}"
            if vote_key in st.session_state.voted_matches:
                st.warning(f"Ya votaste en este match!")
                return
            
            user_id = st.session_state.get('user_id', 'anonymous')
            if not rate_limiter.allow_request(user_id, mid):
                st.error("Espera un momento antes de votar de nuevo")
                return
            
            idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==mid)].index
            if not idx.empty:
                current_votes = int(main_df.at[idx[0], player_col])
                main_df.at[idx[0], player_col] = current_votes + 1
                save_data(main_df)
                st.session_state.voted_matches.add(vote_key)
                st.toast(f"✅ Voto para {player_name} enviado!", icon="🔥")
        
        # Mostrar botones de votación para matches con participantes
        vote_matches = []
        for m in ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']:
            row = get_row(m)
            p1_name = get_val(row, 'P1_Name')
            p2_name = get_val(row, 'P2_Name')
            if p1_name != "Por Definir" and p2_name != "Por Definir" and not row.get('Round_Completed', False):
                vote_matches.append((m, row, p1_name, p2_name))
        
        if vote_matches:
            # Usar columnas responsivas
            cols = st.columns(min(len(vote_matches), 4))
            
            for idx, (m, row, p1_name, p2_name) in enumerate(vote_matches):
                with cols[idx % len(cols)]:
                    v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
                    v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
                    total = v1 + v2
                    
                    if total > 0:
                        pct1 = (v1 / total * 100)
                        pct2 = (v2 / total * 100)
                    else:
                        pct1 = pct2 = 0
                    
                    # Mostrar match
                    with st.container():
                        st.markdown(f"**Match {m}**")
                        col_v1, vs, col_v2 = st.columns([4, 1, 4])
                        
                        with col_v1:
                            if st.button(f"🔴 {p1_name[:10]}...", key=f"vote_red_{m}", use_container_width=True):
                                vote(m, 'P1_Votes', p1_name)
                        
                        with vs:
                            st.markdown("<div style='text-align:center; color:#666;'>VS</div>", unsafe_allow_html=True)
                        
                        with col_v2:
                            if st.button(f"⚪ {p2_name[:10]}...", key=f"vote_white_{m}", use_container_width=True):
                                vote(m, 'P2_Votes', p2_name)
                        
                        # Mostrar estadísticas
                        if total > 0:
                            st.progress(pct1/100, text=f"🔴 {int(pct1)}% - ⚪ {int(pct2)}%")
        else:
            st.info("No hay matches activos para votar en este momento.")
    else:
        st.info("🏁 Las votaciones estarán disponibles cuando el torneo esté activo.")

    # --- GENERADOR BRACKET HORIZONTAL CON FOTOS ---
    def render_player(row, p_prefix, color_class):
        name = get_val(row, f'{p_prefix}_Name')
        dojo = get_val(row, f'{p_prefix}_Dojo')
        photo_base64 = row.get(f'{p_prefix}_Photo', '')
        
        v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
        v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
        total = v1 + v2
        pct = 50
        
        if total > 0:
            pct = (v1 / total * 100) if p_prefix == 'P1' else (v2 / total * 100)
        
        bar_bg = "linear-gradient(90deg, #ef4444, #dc2626)" if p_prefix == 'P1' else "linear-gradient(90deg, #ffffff, #d1d5db)"
        
        live_indicator = ""
        if row.get('Live', False):
            live_indicator = '<span class="live-indicator"></span>'
        
        # Determinar clase de foto
        photo_class = "photo-red" if p_prefix == 'P1' else "photo-white"
        
        # Crear HTML de la foto
        photo_html = base64_to_image_html(photo_base64, 40)
        
        return f"""
        <div class="player-box {color_class}">
            {live_indicator}
            <div class="player-info">
                {photo_html}
                <div class="player-name-container">
                    <div class="p-name">{name}</div>
                    <div class="p-details">
                        <span>🥋 {dojo}</span>
                        <span>{int(pct)}%</span>
                    </div>
                </div>
            </div>
            <div class="p-vote-bar">
                <div class="p-vote-fill" style="width:{pct}%; background:{bar_bg};"></div>
            </div>
            {'<div class="line-r"></div>' if color_class != 'none' else ''}
        </div>
        """

    # Obtener datos de todos los matches
    r_q1, r_q2, r_q3, r_q4 = get_row('Q1'), get_row('Q2'), get_row('Q3'), get_row('Q4')
    r_s1, r_s2, r_f1 = get_row('S1'), get_row('S2'), get_row('F1')
    
    w_q1, w_q2, w_q3, w_q4 = get_val(r_q1,'Winner'), get_val(r_q2,'Winner'), get_val(r_q3,'Winner'), get_val(r_q4,'Winner')
    w_s1, w_s2, w_f1 = get_val(r_s1,'Winner'), get_val(r_s2,'Winner'), get_val(r_f1,'Winner')

    # Generar HTML del bracket HORIZONTAL
    html = f"""
    <div class="bracket-container">
        <div class="rounds-wrapper">
            <!-- RONDA DE CUARTOS -->
            <div class="round">
                <div class="round-title">CUARTOS DE FINAL</div>
                {render_player(r_q1, 'P1', 'border-red')}
                {render_player(r_q1, 'P2', 'border-white')}
                <div style="height:40px; position: relative;">
                    <div class="conn-v" style="height: 80px; top: -40px;"></div>
                </div>
                {render_player(r_q2, 'P1', 'border-red')}
                {render_player(r_q2, 'P2', 'border-white')}
                <div style="height:40px; position: relative;">
                    <div class="conn-v" style="height: 80px; top: -40px;"></div>
                </div>
                {render_player(r_q3, 'P1', 'border-red')}
                {render_player(r_q3, 'P2', 'border-white')}
                <div style="height:40px; position: relative;">
                    <div class="conn-v" style="height: 80px; top: -40px;"></div>
                </div>
                {render_player(r_q4, 'P1', 'border-red')}
                {render_player(r_q4, 'P2', 'border-white')}
            </div>

            <!-- RONDA DE SEMIFINALES -->
            <div class="round">
                <div class="round-title">SEMIFINALES</div>
                <div style="height: 50%; display: flex; flex-direction: column; justify-content: center; position: relative; margin-top: 20px;">
                    <div class="conn-v" style="height: 120px; top: 50%; transform: translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top: 60px;">
                        <div class="player-info">
                            {base64_to_image_html(r_q1.get('P1_Photo', '') if w_q1 == get_val(r_q1, 'P1_Name') else r_q1.get('P2_Photo', ''), 40)}
                            <div class="player-name-container">
                                <div class="p-name">{w_q1}</div>
                                <div class="p-details">
                                    <span>🥋 {get_val(r_q1, 'P1_Dojo') if w_q1 == get_val(r_q1, 'P1_Name') else get_val(r_q1, 'P2_Dojo')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="player-box border-white">
                        <div class="player-info">
                            {base64_to_image_html(r_q2.get('P1_Photo', '') if w_q2 == get_val(r_q2, 'P1_Name') else r_q2.get('P2_Photo', ''), 40)}
                            <div class="player-name-container">
                                <div class="p-name">{w_q2}</div>
                                <div class="p-details">
                                    <span>🥋 {get_val(r_q2, 'P1_Dojo') if w_q2 == get_val(r_q2, 'P1_Name') else get_val(r_q2, 'P2_Dojo')}</span>
                                </div>
                            </div>
                        </div>
                        <div class="line-r"></div>
                    </div>
                </div>
                <div style="height: 50%; display: flex; flex-direction: column; justify-content: center; position: relative; margin-top: 40px;">
                    <div class="conn-v" style="height: 120px; top: 50%; transform: translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top: 60px;">
                        <div class="player-info">
                            {base64_to_image_html(r_q3.get('P1_Photo', '') if w_q3 == get_val(r_q3, 'P1_Name') else r_q3.get('P2_Photo', ''), 40)}
                            <div class="player-name-container">
                                <div class="p-name">{w_q3}</div>
                                <div class="p-details">
                                    <span>🥋 {get_val(r_q3, 'P1_Dojo') if w_q3 == get_val(r_q3, 'P1_Name') else get_val(r_q3, 'P2_Dojo')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="player-box border-white">
                        <div class="player-info">
                            {base64_to_image_html(r_q4.get('P1_Photo', '') if w_q4 == get_val(r_q4, 'P1_Name') else r_q4.get('P2_Photo', ''), 40)}
                            <div class="player-name-container">
                                <div class="p-name">{w_q4}</div>
                                <div class="p-details">
                                    <span>🥋 {get_val(r_q4, 'P1_Dojo') if w_q4 == get_val(r_q4, 'P1_Name') else get_val(r_q4, 'P2_Dojo')}</span>
                                </div>
                            </div>
                        </div>
                        <div class="line-r"></div>
                    </div>
                </div>
            </div>

            <!-- RONDA FINAL -->
            <div class="round">
                <div class="round-title">FINAL</div>
                <div style="height: 100%; display: flex; flex-direction: column; justify-content: center; position: relative;">
                    <div class="conn-v" style="height: 160px; top: 50%; transform: translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top: 80px;">
                        <div class="player-info">
                            {base64_to_image_html(r_s1.get('P1_Photo', '') if w_s1 == get_val(r_s1, 'P1_Name') else r_s1.get('P2_Photo', ''), 40)}
                            <div class="player-name-container">
                                <div class="p-name">{w_s1}</div>
                                <div class="p-details">
                                    <span>🥋 {get_val(r_s1, 'P1_Dojo') if w_s1 == get_val(r_s1, 'P1_Name') else get_val(r_s1, 'P2_Dojo')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="player-box border-white">
                        <div class="player-info">
                            {base64_to_image_html(r_s2.get('P1_Photo', '') if w_s2 == get_val(r_s2, 'P1_Name') else r_s2.get('P2_Photo', ''), 40)}
                            <div class="player-name-container">
                                <div class="p-name">{w_s2}</div>
                                <div class="p-details">
                                    <span>🥋 {get_val(r_s2, 'P1_Dojo') if w_s2 == get_val(r_s2, 'P1_Name') else get_val(r_s2, 'P2_Dojo')}</span>
                                </div>
                            </div>
                        </div>
                        <div class="line-r"></div>
                    </div>
                </div>
            </div>

            <!-- CAMPEÓN -->
            <div class="round">
                <div class="round-title">CAMPEÓN 🏆</div>
                <div style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
                    <div class="champion-box">
                        {w_f1 if w_f1 != "Por Definir" else "POR DEFINIR"}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Instrucción para scroll en móviles -->
    <div style="text-align: center; margin-top: 10px; color: #9ca3af; font-size: 12px;">
        <span>← Desliza horizontalmente para ver todas las rondas →</span>
    </div>
    """
    
    st.html(html)
    
    # Botón para ver estadísticas detalladas
    with st.expander("📈 VER ESTADÍSTICAS DETALLADAS", expanded=False):
        total_votes = cat_df['P1_Votes'].sum() + cat_df['P2_Votes'].sum()
        avg_votes_per_match = total_votes / len(cat_df) if len(cat_df) > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Votos Totales", f"{int(total_votes)}")
        with col2:
            st.metric("Partidos", f"{len(cat_df)}")
        with col3:
            st.metric("Promedio por Match", f"{avg_votes_per_match:.1f}")
        
        match_votes = []
        for m in ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']:
            row = get_row(m)
            if not row.empty:
                v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
                v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
                match_votes.append({"Match": m, "Votos": v1 + v2})
        
        if match_votes:
            votes_df = pd.DataFrame(match_votes)
            st.bar_chart(votes_df.set_index('Match'))
    
    # Recarga automática solo para usuarios no-admin
    if not st.session_state.get('is_admin', False):
        st.html("""
        <script>
        // Recarga cada 15 segundos
        setTimeout(function(){
            window.location.reload();
        }, 15000);
        
        // Smooth scroll para móviles
        document.addEventListener('DOMContentLoaded', function() {
            const bracketContainer = document.querySelector('.bracket-container');
            if (bracketContainer && 'ontouchstart' in window) {
                bracketContainer.style.scrollBehavior = 'smooth';
            }
        });
        </script>
        """)
    else:
        st.info("🔄 Recarga automática desactivada en modo admin")
