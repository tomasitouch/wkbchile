import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import hashlib
import datetime
from datetime import timedelta
import base64
from PIL import Image
import io
import numpy as np
import random
import string
import uuid
import mercadopago
import logging
import re
import json
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# ============================================================================
# 1. CONFIGURACIÓN INICIAL
# ============================================================================

st.set_page_config(
    page_title="WKB Tournament Hub",
    layout="wide",
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

# Meta tags para responsive design
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

# ============================================================================
# 2. CONFIGURACIÓN DE LOGGING
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_event(event_type, details):
    logger.info(f"{event_type}: {details}")

# ============================================================================
# 3. CONSTANTES Y CONFIGURACIONES
# ============================================================================

SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

SHEET_NAMES = {
    "brackets": "Brackets",
    "inscriptions": "Inscripciones",
    "config": "Configuracion",
    "payments": "Pagos",
    "backup": "Backup",
    "votes": "Votos"  # Nueva hoja para tracking de votos
}

# Configuración de categorías
CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}

ALL_CATEGORIES = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

# Grados de karate
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

# ============================================================================
# 4. SEGURIDAD
# ============================================================================

ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# ============================================================================
# 5. ESTILOS CSS PROFESIONALES
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Roboto+Condensed:wght@400;700&display=swap');
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    /* Estilos base */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
        font-family: 'Montserrat', sans-serif;
        min-height: 100vh;
    }
    
    /* Header mejorado */
    .main-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-bottom: 3px solid #fdb931;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 2rem;
        animation: slideInLeft 0.8s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, #fdb931, transparent);
    }
    
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    .tournament-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        background: linear-gradient(45deg, #ffffff, #fdb931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 2px 10px rgba(253, 185, 49, 0.3);
        letter-spacing: 1px;
    }
    
    .tournament-subtitle {
        font-size: 0.9rem;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-top: 0.5rem;
    }
    
    /* Cards modernas */
    .modern-card {
        background: rgba(25, 25, 45, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.8rem;
        margin: 1.5rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        animation: fadeIn 0.6s ease-out;
    }
    
    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(253, 185, 49, 0.2);
        border-color: rgba(253, 185, 49, 0.3);
    }
    
    .card-title {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 1.4rem;
        color: #fdb931;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .card-title::after {
        content: '';
        flex: 1;
        height: 2px;
        background: linear-gradient(90deg, #fdb931, transparent);
        margin-left: 15px;
    }
    
    /* Botones mejorados */
    .stButton > button {
        background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
        color: white;
        border: 1px solid rgba(253, 185, 49, 0.3);
        padding: 12px 24px;
        border-radius: 10px;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        width: 100%;
        text-align: center;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
        border-color: #fdb931;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(253, 185, 49, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Badges */
    .status-badge {
        display: inline-block;
        padding: 6px 15px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-open {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
    }
    
    .badge-closed {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }
    
    .badge-live {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        animation: pulse 2s infinite;
    }
    
    /* Progress bars */
    .progress-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        height: 10px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #fdb931, #ff6b6b);
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Grid responsive */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(25, 25, 45, 0.8);
        border-radius: 12px;
        padding: 5px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        background: transparent;
        color: #a0a0a0;
        border-radius: 8px;
        padding: 12px 24px;
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0f3460, #1a1a2e);
        color: #fdb931;
        box-shadow: 0 4px 15px rgba(253, 185, 49, 0.2);
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(15, 52, 96, 0.8), rgba(26, 26, 46, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: rgba(253, 185, 49, 0.3);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(45deg, #ffffff, #fdb931);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Alerts */
    .alert {
        padding: 1.2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        border-left: 4px solid;
        animation: fadeIn 0.5s ease;
    }
    
    .alert-success {
        background: rgba(16, 185, 129, 0.15);
        border-left-color: #10b981;
        color: #10b981;
    }
    
    .alert-warning {
        background: rgba(245, 158, 11, 0.15);
        border-left-color: #f59e0b;
        color: #f59e0b;
    }
    
    .alert-error {
        background: rgba(239, 68, 68, 0.15);
        border-left-color: #ef4444;
        color: #ef4444;
    }
    
    .alert-info {
        background: rgba(59, 130, 246, 0.15);
        border-left-color: #3b82f6;
        color: #3b82f6;
    }
    
    /* Match cards */
    .match-card {
        background: linear-gradient(135deg, rgba(15, 52, 96, 0.9), rgba(26, 26, 46, 0.9));
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .match-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #fdb931, #ff6b6b, #fdb931);
    }
    
    .match-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(253, 185, 49, 0.2);
    }
    
    .match-card.live {
        border-color: #f59e0b;
        animation: pulse 2s infinite;
    }
    
    .match-card.completed {
        border-color: #10b981;
    }
    
    .match-card.pending {
        border-color: #6b7280;
    }
    
    /* Player info */
    .player-info {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.05);
        margin: 8px 0;
    }
    
    .player-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0f3460, #1a1a2e);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #fdb931;
        border: 2px solid rgba(253, 185, 49, 0.3);
    }
    
    .player-details {
        flex: 1;
    }
    
    .player-name {
        font-weight: 600;
        color: white;
        font-size: 1rem;
    }
    
    .player-dojo {
        font-size: 0.8rem;
        color: #a0a0a0;
    }
    
    .player-votes {
        font-size: 0.9rem;
        color: #fdb931;
        font-weight: bold;
    }
    
    /* Vote buttons */
    .vote-btn {
        background: linear-gradient(135deg, #1a1a2e, #0f3460);
        border: 2px solid rgba(253, 185, 49, 0.3);
        color: #fdb931;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        width: 100%;
    }
    
    .vote-btn:hover {
        background: linear-gradient(135deg, #0f3460, #1a1a2e);
        border-color: #fdb931;
        transform: scale(1.05);
    }
    
    .vote-btn.voted {
        background: linear-gradient(135deg, #10b981, #059669);
        border-color: #10b981;
        color: white;
    }
    
    /* Timeline */
    .timeline {
        position: relative;
        padding-left: 30px;
        margin: 2rem 0;
    }
    
    .timeline::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(180deg, #fdb931, transparent);
    }
    
    .timeline-item {
        position: relative;
        margin-bottom: 2rem;
    }
    
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -33px;
        top: 5px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #fdb931;
        border: 3px solid #1a1a2e;
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 50px;
        height: 50px;
        border: 3px solid rgba(255, 255, 255, 0.1);
        border-top: 3px solid #fdb931;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .header-content {
            flex-direction: column;
            text-align: center;
            gap: 1rem;
        }
        
        .tournament-title {
            font-size: 1.8rem;
        }
        
        .grid-container {
            grid-template-columns: 1fr;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 10px;
            font-size: 0.9rem;
        }
    }
    
    /* Scrollbar personalizado */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #fdb931, #0f3460);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #fdb931, #1a1a2e);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 6. CONEXIONES Y UTILIDADES
# ============================================================================

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def init_mercadopago():
    try:
        MP_ACCESS_TOKEN = st.secrets["mercadopago"]["access_token"]
        return mercadopago.SDK(MP_ACCESS_TOKEN)
    except:
        return None

# ============================================================================
# 7. FUNCIONES DE INICIALIZACIÓN
# ============================================================================

def initialize_sheets():
    """Inicializa todas las hojas necesarias"""
    try:
        conn = get_connection()
        
        # Configuración inicial
        config_data = {
            "setting": [
                "tournament_stage", "registration_open", "tournament_name",
                "inscription_price", "voting_enabled", "auto_confirm_payment",
                "last_backup", "payment_check_interval"
            ],
            "value": [
                "inscription", "true", "WKB Chile 2024",
                "50000", "true", "true",
                "", "30"
            ]
        }
        
        config_df = pd.DataFrame(config_data)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=config_df)
        
        # Inicializar otras hojas
        for sheet in ["inscriptions", "brackets", "payments", "backup", "votes"]:
            conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[sheet], data=pd.DataFrame())
        
        create_backup("initial")
        return True
    except Exception as e:
        log_event("ERROR_SHEETS_INIT", str(e))
        return False

# ============================================================================
# 8. FUNCIONES DE CARGA DE DATOS
# ============================================================================

@st.cache_data(ttl=10)
def load_config():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=10)
        if df.empty:
            initialize_sheets()
            df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=10)
        return df.set_index("setting")["value"].to_dict()
    except:
        return {}

@st.cache_data(ttl=10)
def load_inscriptions():
    try:
        conn = get_connection()
        return conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], ttl=10)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_brackets():
    try:
        conn = get_connection()
        return conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], ttl=5)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_votes():
    try:
        conn = get_connection()
        return conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["votes"], ttl=5)
    except:
        return pd.DataFrame()

# ============================================================================
# 9. FUNCIONES DE GESTIÓN DEL TORNEO
# ============================================================================

def get_tournament_stage():
    config = load_config()
    return config.get("tournament_stage", "inscription")

def is_registration_open():
    config = load_config()
    return config.get("registration_open", "true").lower() == "true"

def is_voting_enabled():
    config = load_config()
    return config.get("voting_enabled", "true").lower() == "true"

def set_tournament_stage(stage):
    try:
        conn = get_connection()
        config_df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=5)
        config_df.loc[config_df["setting"] == "tournament_stage", "value"] = stage
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=config_df)
        st.cache_data.clear()
        return True
    except:
        return False

# ============================================================================
# 10. FUNCIONES DE BRACKETS PROFESIONALES
# ============================================================================

def generate_bracket_visualization(category):
    """Genera visualización profesional de bracket"""
    brackets_df = load_brackets()
    category_df = brackets_df[brackets_df["Category"] == category]
    
    if category_df.empty:
        return None
    
    # Organizar por rondas
    rounds_order = ["Round of 64", "Round of 32", "Round of 16", "Quarterfinals", "Semifinals", "Finals", "Champion"]
    rounds = []
    
    for round_name in rounds_order:
        round_matches = category_df[category_df["Round"] == round_name]
        if not round_matches.empty:
            rounds.append({
                "name": round_name,
                "matches": round_matches.sort_values("Match_Number").to_dict("records")
            })
    
    return rounds

def create_bracket_html(rounds):
    """Crea HTML para visualización de bracket"""
    html = """
    <div class="bracket-container" style="
        display: flex;
        overflow-x: auto;
        padding: 20px;
        gap: 40px;
        min-height: 600px;
        align-items: flex-start;
    ">
    """
    
    for i, round_data in enumerate(rounds):
        html += f"""
        <div class="round" style="
            min-width: 280px;
            display: flex;
            flex-direction: column;
            gap: 40px;
        ">
            <div class="round-header" style="
                text-align: center;
                color: #fdb931;
                font-weight: bold;
                font-size: 1.1rem;
                margin-bottom: 20px;
                padding: 10px;
                background: rgba(15, 52, 96, 0.5);
                border-radius: 8px;
                border: 1px solid rgba(253, 185, 49, 0.3);
            ">
                {round_data['name']}
            </div>
        """
        
        for match in round_data["matches"]:
            p1_class = "winner" if match.get("Winner_ID") == match.get("P1_ID") else ""
            p2_class = "winner" if match.get("Winner_ID") == match.get("P2_ID") else ""
            
            html += f"""
            <div class="match" style="
                position: relative;
                margin: 20px 0;
            ">
                <!-- Líneas conectores -->
                <div class="connector-right" style="
                    position: absolute;
                    right: -20px;
                    top: 50%;
                    width: 20px;
                    height: 2px;
                    background: linear-gradient(90deg, #374151, #6b7280);
                    z-index: 1;
                "></div>
                
                <div class="match-content" style="
                    background: linear-gradient(135deg, rgba(15, 52, 96, 0.9), rgba(26, 26, 46, 0.9));
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    overflow: hidden;
                    position: relative;
                    z-index: 2;
                ">
                    <div class="player {p1_class}" style="
                        padding: 15px;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        background: {('rgba(16, 185, 129, 0.2)' if p1_class else 'transparent')};
                    ">
                        <div style="font-weight: 600; color: #ffffff; margin-bottom: 5px;">
                            {match.get('P1_Name', 'TBD')}
                        </div>
                        <div style="font-size: 0.8rem; color: #a0a0a0;">
                            {match.get('P1_Dojo', '')}
                        </div>
                        <div style="font-size: 0.8rem; color: #fdb931; margin-top: 5px;">
                            Votes: {match.get('P1_Votes', 0)}
                        </div>
                    </div>
                    
                    <div class="player {p2_class}" style="
                        padding: 15px;
                        background: {('rgba(16, 185, 129, 0.2)' if p2_class else 'transparent')};
                    ">
                        <div style="font-weight: 600; color: #ffffff; margin-bottom: 5px;">
                            {match.get('P2_Name', 'TBD')}
                        </div>
                        <div style="font-size: 0.8rem; color: #a0a0a0;">
                            {match.get('P2_Dojo', '')}
                        </div>
                        <div style="font-size: 0.8rem; color: #fdb931; margin-top: 5px;">
                            Votes: {match.get('P2_Votes', 0)}
                        </div>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    html += "</div>"
    return html

# ============================================================================
# 11. SISTEMA DE VOTACIÓN AVANZADO
# ============================================================================

def register_vote(match_id, player_id, voter_ip=None):
    """Registra un voto para un jugador"""
    try:
        votes_df = load_votes()
        
        # Verificar si ya votó
        vote_key = f"{match_id}_{voter_ip}" if voter_ip else f"{match_id}_anon"
        if not votes_df.empty and vote_key in votes_df["vote_key"].values:
            return False, "Ya has votado en este match"
        
        # Registrar voto
        new_vote = pd.DataFrame([{
            "vote_key": vote_key,
            "match_id": match_id,
            "player_id": player_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "voter_ip": voter_ip or "anonymous"
        }])
        
        votes_df = pd.concat([votes_df, new_vote], ignore_index=True)
        
        # Actualizar votos en brackets
        brackets_df = load_brackets()
        match_mask = brackets_df["Match_ID"] == match_id
        
        if not brackets_df[match_mask].empty:
            match = brackets_df[match_mask].iloc[0]
            if player_id == match["P1_ID"]:
                brackets_df.loc[match_mask, "P1_Votes"] = match.get("P1_Votes", 0) + 1
            elif player_id == match["P2_ID"]:
                brackets_df.loc[match_mask, "P2_Votes"] = match.get("P2_Votes", 0) + 1
            
            brackets_df.loc[match_mask, "Total_Votes"] = match.get("Total_Votes", 0) + 1
            brackets_df.loc[match_mask, "Last_Vote_Time"] = datetime.datetime.now().isoformat()
            
            # Guardar cambios
            conn = get_connection()
            conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=brackets_df)
            conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["votes"], data=votes_df)
            
            st.cache_data.clear()
            return True, "Voto registrado exitosamente"
    
    except Exception as e:
        log_event("ERROR_REGISTER_VOTE", str(e))
    
    return False, "Error registrando voto"

def get_match_votes(match_id):
    """Obtiene estadísticas de votos para un match"""
    votes_df = load_votes()
    match_votes = votes_df[votes_df["match_id"] == match_id]
    
    return {
        "total_votes": len(match_votes),
        "p1_votes": len(match_votes[match_votes["player_id"] == match_id + "_P1"]),
        "p2_votes": len(match_votes[match_votes["player_id"] == match_id + "_P2"]),
        "vote_history": match_votes.to_dict("records")[-10:]  # Últimos 10 votos
    }

# ============================================================================
# 12. COMPONENTES VISUALES
# ============================================================================

def render_header():
    """Renderiza el header profesional"""
    st.markdown(f"""
    <div class="main-header">
        <div class="header-content">
            <div style="flex: 1;">
                <div class="tournament-title">🥋 WKB TOURNAMENT HUB</div>
                <div class="tournament-subtitle">World Kyokushin Budokai Chile 2024</div>
            </div>
            
            <div style="display: flex; gap: 15px; align-items: center;">
                <div class="status-badge {'badge-open' if is_registration_open() else 'badge-closed'}">
                    {('OPEN' if is_registration_open() else 'CLOSED')}
                </div>
                <div class="status-badge {'badge-live' if get_tournament_stage() == 'competition' else ''}">
                    {get_tournament_stage().upper()}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_statistics():
    """Renderiza estadísticas del torneo"""
    inscriptions_df = load_inscriptions()
    brackets_df = load_brackets()
    
    confirmed = len(inscriptions_df[inscriptions_df["Estado_Pago"] == "Confirmado"]) if "Estado_Pago" in inscriptions_df.columns else 0
    total_matches = len(brackets_df) if not brackets_df.empty else 0
    live_matches = len(brackets_df[brackets_df["Status"] == "Live"]) if not brackets_df.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">Confirmed Participants</div>
        </div>
        """.format(confirmed), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">Total Matches</div>
        </div>
        """.format(total_matches), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">Live Matches</div>
        </div>
        """.format(live_matches), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">{}</div>
            <div class="stat-label">Categories</div>
        </div>
        """.format(len(ALL_CATEGORIES)), unsafe_allow_html=True)

def render_match_card(match, category, show_voting=True):
    """Renderiza una tarjeta de match con votación"""
    match_class = ""
    if match.get("Status") == "Live":
        match_class = "live"
    elif match.get("Status") == "Completed":
        match_class = "completed"
    else:
        match_class = "pending"
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="player-info">
            <div class="player-avatar">1</div>
            <div class="player-details">
                <div class="player-name">{match.get('P1_Name', 'TBD')}</div>
                <div class="player-dojo">{match.get('P1_Dojo', '')}</div>
            </div>
            <div class="player-votes">{match.get('P1_Votes', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if show_voting and is_voting_enabled() and match.get("Status") == "Live":
            if st.button(f"Vote {match.get('P1_Name', 'Player 1')[:15]}...", 
                        key=f"vote_p1_{match['Match_ID']}",
                        use_container_width=True):
                success, message = register_vote(
                    match["Match_ID"], 
                    match["P1_ID"],
                    voter_ip=st.experimental_user.hash
                )
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"**VS**")
        st.markdown(f"*{match.get('Round')}*")
        
        if match.get("Winner"):
            st.success(f"🏆 Winner: {match.get('Winner')}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        if match.get("P2_Name"):
            st.markdown(f"""
            <div class="player-info">
                <div class="player-avatar">2</div>
                <div class="player-details">
                    <div class="player-name">{match.get('P2_Name', 'TBD')}</div>
                    <div class="player-dojo">{match.get('P2_Dojo', '')}</div>
                </div>
                <div class="player-votes">{match.get('P2_Votes', 0)}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if show_voting and is_voting_enabled() and match.get("Status") == "Live":
                if st.button(f"Vote {match.get('P2_Name', 'Player 2')[:15]}...", 
                            key=f"vote_p2_{match['Match_ID']}",
                            use_container_width=True):
                    success, message = register_vote(
                        match["Match_ID"], 
                        match["P2_ID"],
                        voter_ip=st.experimental_user.hash
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

# ============================================================================
# 13. VISTA DE BRACKETS
# ============================================================================

def render_bracket_view(category):
    """Vista principal de brackets"""
    render_header()
    
    st.markdown(f"""
    <div style="margin: 2rem 0;">
        <h2 style="color: #fdb931; margin-bottom: 0.5rem;">{category}</h2>
        <div style="color: #a0a0a0; font-size: 0.9rem;">
            Interactive Tournament Bracket • Live Voting Enabled
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["🏆 Bracket View", "📊 Match Details", "📈 Statistics"])
    
    with tab1:
        # Visualización de bracket
        rounds = generate_bracket_visualization(category)
        if rounds:
            bracket_html = create_bracket_html(rounds)
            st.markdown(bracket_html, unsafe_allow_html=True)
            
            # Controles de bracket
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Refresh Bracket", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
            with col2:
                if st.button("📥 Download Bracket", use_container_width=True):
                    st.info("Bracket download feature coming soon!")
            with col3:
                if st.button("🏠 Back to Home", use_container_width=True):
                    st.session_state.view = "HOME"
                    st.rerun()
        else:
            st.info("Bracket not generated yet for this category.")
    
    with tab2:
        # Lista detallada de matches
        brackets_df = load_brackets()
        category_df = brackets_df[brackets_df["Category"] == category]
        
        if not category_df.empty:
            for _, match in category_df.iterrows():
                render_match_card(match, category, show_voting=True)
        else:
            st.info("No matches found for this category.")
    
    with tab3:
        # Estadísticas de la categoría
        brackets_df = load_brackets()
        category_df = brackets_df[brackets_df["Category"] == category]
        
        if not category_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico de votos por match
                matches_data = []
                for _, match in category_df.iterrows():
                    matches_data.append({
                        "Match": match["Match_ID"],
                        "P1_Votes": match.get("P1_Votes", 0),
                        "P2_Votes": match.get("P2_Votes", 0),
                        "Total": match.get("Total_Votes", 0)
                    })
                
                if matches_data:
                    df = pd.DataFrame(matches_data)
                    fig = px.bar(df, x="Match", y=["P1_Votes", "P2_Votes"], 
                                title="Votes by Match", barmode="group")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Estadísticas de participación
                total_votes = category_df["Total_Votes"].sum() if "Total_Votes" in category_df.columns else 0
                live_matches = len(category_df[category_df["Status"] == "Live"])
                completed_matches = len(category_df[category_df["Status"] == "Completed"])
                
                st.markdown("""
                <div class="modern-card">
                    <div class="card-title">📊 Category Stats</div>
                    <div style="margin: 1rem 0;">
                        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                            <span>Total Votes:</span>
                            <span style="color: #fdb931; font-weight: bold;">{}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                            <span>Live Matches:</span>
                            <span style="color: #f59e0b; font-weight: bold;">{}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                            <span>Completed Matches:</span>
                            <span style="color: #10b981; font-weight: bold;">{}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 10px 0;">
                            <span>Total Matches:</span>
                            <span style="font-weight: bold;">{}</span>
                        </div>
                    </div>
                </div>
                """.format(total_votes, live_matches, completed_matches, len(category_df)), 
                unsafe_allow_html=True)

# ============================================================================
# 14. VISTA DE INSCRIPCIÓN
# ============================================================================

def render_inscription_view():
    """Vista de inscripción"""
    render_header()
    
    st.markdown("""
    <div style="margin: 2rem 0;">
        <h2 style="color: #fdb931; margin-bottom: 0.5rem;">Tournament Registration</h2>
        <div style="color: #a0a0a0; font-size: 0.9rem;">
            Secure Registration • Multiple Payment Methods • Instant Confirmation
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not is_registration_open():
        st.markdown("""
        <div class="alert-warning">
            <strong>⚠️ REGISTRATIONS CLOSED</strong><br>
            The registration period has ended. The tournament is now in competition stage.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏆 View Tournament Brackets", use_container_width=True):
            st.session_state.view = "HOME"
            st.rerun()
        return
    
    # Formulario de inscripción simplificado
    with st.form("registration_form"):
        st.markdown('<div class="card-title">👤 Participant Information</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", placeholder="Juan Pérez González")
            age = st.number_input("Age *", min_value=18, max_value=80, value=18)
            weight = st.number_input("Weight (kg) *", min_value=30.0, max_value=150.0, value=70.0)
            height = st.number_input("Height (cm) *", min_value=100, max_value=220, value=170)
        
        with col2:
            grade = st.selectbox("Grade *", options=list(KARATE_GRADES.keys()), 
                               format_func=lambda x: KARATE_GRADES[x])
            dojo = st.text_input("Dojo/Club *", placeholder="Dojo Zen Karate")
            phone = st.text_input("Phone *", placeholder="+56912345678")
            email = st.text_input("Email *", placeholder="example@email.com")
        
        # Categoría
        st.markdown('<div class="card-title">🏆 Competition Category</div>', unsafe_allow_html=True)
        category = st.selectbox("Select your category *", options=ALL_CATEGORIES)
        
        # Documentos
        st.markdown('<div class="card-title">📄 Required Documents</div>', unsafe_allow_html=True)
        col_consent1, col_consent2 = st.columns(2)
        
        with col_consent1:
            consent = st.checkbox("I authorize the processing of my personal data")
        
        with col_consent2:
            waiver = st.checkbox("I accept the terms and conditions of participation")
        
        # Botones
        col_submit1, col_submit2 = st.columns(2)
        with col_submit1:
            submit = st.form_submit_button("🚀 Proceed to Payment", type="primary", use_container_width=True)
        with col_submit2:
            cancel = st.form_submit_button("🔙 Back to Home", use_container_width=True)
        
        if cancel:
            st.session_state.view = "HOME"
            st.rerun()
        
        if submit:
            if not all([name, dojo, phone, email, consent, waiver]):
                st.error("Please fill all required fields (*)")
            else:
                # Simular procesamiento
                with st.spinner("Processing registration..."):
                    time.sleep(2)
                    st.success("Registration submitted successfully!")
                    st.info("Payment system integration coming soon!")

# ============================================================================
# 15. VISTA PRINCIPAL (HOME)
# ============================================================================

def render_home_view():
    """Vista principal del sistema"""
    render_header()
    
    # Estadísticas
    render_statistics()
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Categories", "📝 Register", "👥 Participants", "⚙️ Admin"])
    
    with tab1:
        st.markdown('<div class="card-title">Tournament Categories</div>', unsafe_allow_html=True)
        
        for group, subcategories in CATEGORIES_CONFIG.items():
            st.markdown(f"### {group}")
            
            cols = st.columns(len(subcategories))
            for idx, subcat in enumerate(subcategories):
                full_cat = f"{group} | {subcat}"
                
                with cols[idx]:
                    # Contar inscritos
                    inscriptions_df = load_inscriptions()
                    count = len(inscriptions_df[
                        (inscriptions_df["Categoria"] == full_cat) & 
                        (inscriptions_df["Estado_Pago"] == "Confirmado")
                    ]) if not inscriptions_df.empty else 0
                    
                    if st.button(
                        f"**{subcat}**\n\n"
                        f"📊 {count} registered\n"
                        f"{"✅ Voting Open" if is_voting_enabled() else "⏸️ Voting Paused"}",
                        key=f"cat_{full_cat}",
                        use_container_width=True
                    ):
                        st.session_state.view = "BRACKET"
                        st.session_state.category = full_cat
                        st.rerun()
    
    with tab2:
        if get_tournament_stage() == "competition":
            st.markdown("""
            <div class="alert-info">
                <strong>🏆 TOURNAMENT IN PROGRESS</strong><br>
                Registrations are closed. The competition has started!
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("View Live Brackets", type="primary", use_container_width=True):
                # Ir a la categoría con más participantes
                inscriptions_df = load_inscriptions()
                if not inscriptions_df.empty:
                    cat_counts = inscriptions_df[
                        inscriptions_df["Estado_Pago"] == "Confirmado"
                    ]["Categoria"].value_counts()
                    
                    if not cat_counts.empty:
                        st.session_state.category = cat_counts.index[0]
                        st.session_state.view = "BRACKET"
                        st.rerun()
        else:
            if st.button("Start Registration", type="primary", use_container_width=True):
                st.session_state.view = "INSCRIPTION"
                st.rerun()
    
    with tab3:
        st.markdown('<div class="card-title">Registered Participants</div>', unsafe_allow_html=True)
        
        inscriptions_df = load_inscriptions()
        if not inscriptions_df.empty:
            # Filtros
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filter_cat = st.selectbox("Filter by category", 
                                         ["All"] + list(inscriptions_df["Categoria"].unique()))
            with col_filter2:
                filter_status = st.selectbox("Filter by status", 
                                           ["All", "Confirmed", "Pending"])
            
            # Aplicar filtros
            filtered_df = inscriptions_df.copy()
            if filter_cat != "All":
                filtered_df = filtered_df[filtered_df["Categoria"] == filter_cat]
            if filter_status != "All":
                if filter_status == "Confirmed":
                    filtered_df = filtered_df[filtered_df["Estado_Pago"] == "Confirmado"]
                else:
                    filtered_df = filtered_df[filtered_df["Estado_Pago"] != "Confirmado"]
            
            # Mostrar datos
            st.dataframe(
                filtered_df[["Nombre_Completo", "Categoria", "Dojo", "Estado_Pago", "Fecha_Inscripcion"]],
                column_config={
                    "Nombre_Completo": "Name",
                    "Categoria": "Category",
                    "Dojo": "Dojo",
                    "Estado_Pago": "Payment Status",
                    "Fecha_Inscripcion": "Registration Date"
                },
                use_container_width=True
            )
        else:
            st.info("No participants registered yet.")
    
    with tab4:
        # Panel de administración
        if not st.session_state.get("is_admin", False):
            st.markdown('<div class="card-title">🔒 Admin Access</div>', unsafe_allow_html=True)
            
            admin_pass = st.text_input("Admin Password", type="password")
            
            if st.button("Login", type="primary", use_container_width=True):
                if check_admin(admin_pass):
                    st.session_state.is_admin = True
                    st.success("Access granted!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            st.success("✅ ADMIN SESSION ACTIVE")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
            
            st.markdown("---")
            st.markdown('<div class="card-title">Tournament Controls</div>', unsafe_allow_html=True)
            
            # Controles rápidos
            col_control1, col_control2 = st.columns(2)
            
            with col_control1:
                current_stage = get_tournament_stage()
                if current_stage == "inscription":
                    if st.button("Close Registrations", type="primary", use_container_width=True):
                        if set_tournament_stage("competition"):
                            st.success("Registrations closed!")
                            st.rerun()
                else:
                    if st.button("Reopen Registrations", use_container_width=True):
                        if set_tournament_stage("inscription"):
                            st.success("Registrations reopened!")
                            st.rerun()
            
            with col_control2:
                if st.button("Refresh All Data", use_container_width=True):
                    st.cache_data.clear()
                    st.success("Data refreshed!")
                    st.rerun()

# ============================================================================
# 16. APLICACIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal de la aplicación"""
    
    # Inicializar estado de sesión
    if "view" not in st.session_state:
        st.session_state.view = "HOME"
    if "category" not in st.session_state:
        st.session_state.category = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    
    # Verificar configuración
    config = load_config()
    if not config:
        with st.spinner("Initializing system..."):
            initialize_sheets()
    
    # Navegación
    if st.session_state.view == "HOME":
        render_home_view()
    elif st.session_state.view == "INSCRIPTION":
        render_inscription_view()
    elif st.session_state.view == "BRACKET" and st.session_state.category:
        render_bracket_view(st.session_state.category)
    else:
        st.session_state.view = "HOME"
        st.rerun()

# ============================================================================
# 17. EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Critical error: {str(e)}")
        log_event("CRITICAL_ERROR", str(e))
        
        st.markdown("""
        <div class="alert-error">
            <strong>🛠️ Troubleshooting</strong><br>
            1. Refresh the page<br>
            2. Check your internet connection<br>
            3. Contact support if the problem persists
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Restart Application", type="primary"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()
