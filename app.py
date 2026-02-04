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
import numpy as np
from scipy.spatial.distance import cdist
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
    
    /* PLAYER BOX MEJORADO */
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
        min-height: 80px;
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
        margin-bottom: 5px;
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
    
    /* BADGE PARA PARTICIPANTES */
    .participant-badge {
        background: linear-gradient(135deg, #1f2937, #374151);
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #FDB931;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
    }
    
    .participant-badge:hover {
        transform: translateX(5px);
        border-left-color: #ef4444;
    }
    
    /* INDICADOR DE NAVEGACIÓN */
    .nav-indicator {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 20px 0;
    }
    
    .nav-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #374151;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .nav-dot.active {
        background: #FDB931;
        transform: scale(1.2);
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
            min-height: 75px;
            padding: 12px;
        }
        
        .rounds-wrapper {
            gap: 25px;
            padding: 0 15px;
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
            min-height: 70px;
            padding: 10px;
            margin: 8px 0;
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
            min-height: 65px;
            padding: 8px;
            margin: 6px 0;
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
            min-height: 55px;
            padding: 6px;
            margin: 4px 0;
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
    
    /* ESTILOS PARA MODALES Y CONFIRMACIONES */
    .confirmation-modal {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: #1f2937;
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #FDB931;
        z-index: 1000;
        max-width: 90%;
        width: 500px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    }
    
    .overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        z-index: 999;
    }
    
    /* MEJORAS DE ACCESIBILIDAD */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
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
    
    /* TARJETAS DE PARTICIPANTES */
    .participant-card {
        background: linear-gradient(145deg, #1f2937, #111827);
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid #374151;
        transition: all 0.3s ease;
    }
    
    .participant-card:hover {
        border-color: #FDB931;
        transform: translateY(-3px);
    }
    
    /* PANEL ADMIN FLOTANTE */
    .admin-panel {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: rgba(31, 41, 55, 0.95);
        border: 2px solid #FDB931;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        backdrop-filter: blur(5px);
    }
    
    .admin-toggle-btn {
        background: linear-gradient(135deg, #FDB931, #ef4444);
        color: black;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .admin-toggle-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 0 15px rgba(253, 185, 49, 0.5);
    }
    
    .admin-menu {
        margin-top: 10px;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    
    .admin-menu-item {
        background: #1f2937;
        color: white;
        border: 1px solid #374151;
        padding: 8px 12px;
        border-radius: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 12px;
    }
    
    .admin-menu-item:hover {
        background: #374151;
        border-color: #FDB931;
    }
    
    .danger-btn {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
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
    "1": {"name": "Blanco (10º Kyu)", "value": 1},
    "2": {"name": "Amarillo (9º Kyu)", "value": 2},
    "3": {"name": "Naranja (8º Kyu)", "value": 3},
    "4": {"name": "Verde (7º Kyu)", "value": 4},
    "5": {"name": "Azul (6º Kyu)", "value": 5},
    "6": {"name": "Violeta (5º Kyu)", "value": 6},
    "7": {"name": "Marrón (4º-1º Kyu)", "value": 7},
    "8": {"name": "Negro (1º-3º Dan)", "value": 8},
    "9": {"name": "Negro (4º-6º Dan)", "value": 9},
    "10": {"name": "Negro (7º-10º Dan)", "value": 10}
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
            is_q = 'Q' in m
            data.append({
                "Category": cat, "Match_ID": m, 
                "P1_Name": "Fighter A" if is_q else "", "P1_Dojo": "Dojo X" if is_q else "", "P1_Votes": 0,
                "P2_Name": "Fighter B" if is_q else "", "P2_Dojo": "Dojo Y" if is_q else "", "P2_Votes": 0,
                "Winner": None,
                "Live": False if m in ['S1', 'S2', 'F1'] else False
            })
    return pd.DataFrame(data)

# Datos iniciales para inscripciones
@st.cache_data(ttl=30)
def get_initial_inscriptions_df():
    return pd.DataFrame(columns=[
        "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", "Grado_Valor",
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
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Hoja1", ttl=15)
        if df.empty or "P1_Votes" not in df.columns: 
            df = get_initial_df()
            conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
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

def save_data(df):
    conn = get_connection()
    try:
        conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

def save_inscriptions(df):
    conn = get_connection()
    try:
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando inscripciones: {e}")

def reset_all_data():
    """Resetea todos los datos del torneo"""
    try:
        conn = get_connection()
        
        # Resetear brackets a estado inicial
        initial_df = get_initial_df()
        conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=initial_df)
        
        # Resetear inscripciones
        initial_insc = get_initial_inscriptions_df()
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=initial_insc)
        
        # Limpiar caches
        st.cache_data.clear()
        
        # Limpiar session state
        if 'group_participants' in st.session_state:
            st.session_state.group_participants = []
        if 'current_participant' in st.session_state:
            st.session_state.current_participant = {}
        
        return True
    except Exception as e:
        st.error(f"Error reseteando datos: {e}")
        return False

def validate_data(df):
    """Valida la integridad de los datos"""
    errors = []
    
    required_matches = ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']
    for cat in ALL_CATS:
        cat_matches = df[df['Category'] == cat]['Match_ID'].tolist()
        for rm in required_matches:
            if rm not in cat_matches:
                errors.append(f"Falta {rm} en {cat}")
    
    for idx, row in df.iterrows():
        winner = row.get('Winner')
        if pd.notna(winner) and winner != "":
            p1_name = row.get('P1_Name')
            p2_name = row.get('P2_Name')
            if winner not in [p1_name, p2_name]:
                errors.append(f"Ganador inválido en {row['Category']} - {row['Match_ID']}")
    
    return errors

# --- FUNCIONES DE EMPAREJAMIENTO AUTOMÁTICO ---
def calculate_similarity_score(p1, p2):
    """
    Calcula un score de similitud entre dos participantes
    Score más bajo = más similares
    """
    score = 0
    
    # Peso (30% de importancia)
    peso_diff = abs(p1['Peso'] - p2['Peso'])
    score += (peso_diff / 50) * 0.3  # Normalizado a escala 0-1
    
    # Estatura (30% de importancia)
    estatura_diff = abs(p1['Estatura'] - p2['Estatura'])
    score += (estatura_diff / 50) * 0.3  # Normalizado
    
    # Grado (30% de importancia)
    grado_diff = abs(int(p1['Grado_Valor']) - int(p2['Grado_Valor']))
    score += (grado_diff / 10) * 0.3  # Normalizado a escala 0-1
    
    # Edad (10% de importancia)
    edad_diff = abs(p1['Edad'] - p2['Edad'])
    score += (edad_diff / 50) * 0.1  # Normalizado
    
    return score

def automatic_pairing(category):
    """
    Realiza emparejamiento automático basado en similitud de participantes
    """
    try:
        # Obtener inscritos de la categoría específica
        inscritos_df = inscriptions_df[inscriptions_df['Categoria'] == category]
        
        if len(inscritos_df) < 2:
            st.warning(f"No hay suficientes inscritos en {category} para emparejar (mínimo 2)")
            return False
        
        # Filtrar solo inscritos activos
        inscritos_df = inscritos_df[inscriptions_df['Estado'] != 'Eliminado']
        
        # Preparar lista de participantes
        participants = []
        for _, row in inscritos_df.iterrows():
            participants.append({
                'ID': row['ID'],
                'Nombre_Completo': row['Nombre_Completo'],
                'Peso': float(row['Peso']),
                'Estatura': float(row['Estatura']),
                'Grado_Valor': int(row['Grado_Valor']),
                'Edad': int(row['Edad']),
                'Dojo': row['Dojo']
            })
        
        # Si hay número impar, excluir al que menos se empareje
        if len(participants) % 2 != 0:
            # Calcular scores totales para cada participante
            participant_scores = {}
            for i, p1 in enumerate(participants):
                total_score = 0
                for j, p2 in enumerate(participants):
                    if i != j:
                        total_score += calculate_similarity_score(p1, p2)
                participant_scores[i] = total_score
            
            # Excluir al que tenga el score total más alto (menos compatible)
            exclude_idx = max(participant_scores, key=participant_scores.get)
            excluded_participant = participants.pop(exclude_idx)
            st.warning(f"Participante excluido por emparejamiento impar: {excluded_participant['Nombre_Completo']}")
        
        # Crear matriz de similitud
        n = len(participants)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                score = calculate_similarity_score(participants[i], participants[j])
                similarity_matrix[i][j] = score
                similarity_matrix[j][i] = score
        
        # Emparejar usando algoritmo greedy
        pairs = []
        used = set()
        
        # Ordenar participantes por mejor emparejamiento
        for i in range(n):
            if i not in used:
                # Encontrar mejor match no usado
                best_match = None
                best_score = float('inf')
                
                for j in range(n):
                    if i != j and j not in used:
                        if similarity_matrix[i][j] < best_score:
                            best_score = similarity_matrix[i][j]
                            best_match = j
                
                if best_match is not None:
                    pairs.append((participants[i], participants[best_match], best_score))
                    used.add(i)
                    used.add(best_match)
        
        # Actualizar brackets con los emparejamientos
        cat_matches = main_df[main_df['Category'] == category]
        
        # Ordenar pairs por score (mejores emparejamientos primero)
        pairs.sort(key=lambda x: x[2])
        
        # Asignar a Q1, Q2, Q3, Q4
        match_ids = ['Q1', 'Q2', 'Q3', 'Q4']
        for idx, match_id in enumerate(match_ids):
            if idx < len(pairs):
                p1, p2, score = pairs[idx]
                
                # Encontrar índice en main_df
                match_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == match_id)].index
                
                if not match_idx.empty:
                    main_df.at[match_idx[0], 'P1_Name'] = p1['Nombre_Completo']
                    main_df.at[match_idx[0], 'P1_Dojo'] = p1['Dojo']
                    main_df.at[match_idx[0], 'P2_Name'] = p2['Nombre_Completo']
                    main_df.at[match_idx[0], 'P2_Dojo'] = p2['Dojo']
                    main_df.at[match_idx[0], 'P1_Votes'] = 0
                    main_df.at[match_idx[0], 'P2_Votes'] = 0
                    main_df.at[match_idx[0], 'Winner'] = None
                    
                    st.success(f"Emparejado Q{idx+1}: {p1['Nombre_Completo']} vs {p2['Nombre_Completo']} (Score: {score:.2f})")
        
        # Guardar cambios
        save_data(main_df)
        
        # Marcar participantes como emparejados
        for p1, p2, _ in pairs:
            p1_idx = inscriptions_df[inscriptions_df['Nombre_Completo'] == p1['Nombre_Completo']].index
            p2_idx = inscriptions_df[inscriptions_df['Nombre_Completo'] == p2['Nombre_Completo']].index
            
            if not p1_idx.empty:
                inscriptions_df.at[p1_idx[0], 'Estado'] = 'Emparejado'
            if not p2_idx.empty:
                inscriptions_df.at[p2_idx[0], 'Estado'] = 'Emparejado'
        
        save_inscriptions(inscriptions_df)
        
        return True
        
    except Exception as e:
        st.error(f"Error en emparejamiento automático: {e}")
        return False

def generate_random_pairing(category):
    """
    Emparejamiento aleatorio (para testing o emergencias)
    """
    try:
        # Obtener inscritos de la categoría
        inscritos_df = inscriptions_df[inscriptions_df['Categoria'] == category]
        
        if len(inscritos_df) < 2:
            st.warning(f"No hay suficientes inscritos en {category}")
            return False
        
        participants = inscritos_df['Nombre_Completo'].tolist()
        dojos = inscritos_df['Dojo'].tolist()
        
        # Mezclar aleatoriamente
        combined = list(zip(participants, dojos))
        random.shuffle(combined)
        
        # Crear pairs
        pairs = []
        for i in range(0, len(combined), 2):
            if i+1 < len(combined):
                pairs.append((combined[i], combined[i+1]))
        
        # Asignar a brackets
        match_ids = ['Q1', 'Q2', 'Q3', 'Q4']
        for idx, match_id in enumerate(match_ids):
            if idx < len(pairs):
                (p1_name, p1_dojo), (p2_name, p2_dojo) = pairs[idx]
                
                match_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == match_id)].index
                
                if not match_idx.empty:
                    main_df.at[match_idx[0], 'P1_Name'] = p1_name
                    main_df.at[match_idx[0], 'P1_Dojo'] = p1_dojo
                    main_df.at[match_idx[0], 'P2_Name'] = p2_name
                    main_df.at[match_idx[0], 'P2_Dojo'] = p2_dojo
                    main_df.at[match_idx[0], 'P1_Votes'] = 0
                    main_df.at[match_idx[0], 'P2_Votes'] = 0
                    main_df.at[match_idx[0], 'Winner'] = None
        
        save_data(main_df)
        st.success(f"Emparejamiento aleatorio generado para {category}")
        return True
        
    except Exception as e:
        st.error(f"Error en emparejamiento aleatorio: {e}")
        return False

# Cargar datos iniciales
main_df = load_data()
inscriptions_df = load_inscriptions()

# --- 5. NAVEGACIÓN MEJORADA ---
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
if 'show_admin_panel' not in st.session_state:
    st.session_state.show_admin_panel = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'confirm_reset' not in st.session_state:
    st.session_state.confirm_reset = False

def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

# --- PANEL ADMIN FLOTANTE MEJORADO ---
def render_admin_panel():
    """Panel de administrador flotante accesible desde cualquier página"""
    if not st.session_state.show_admin_panel:
        # Botón flotante para mostrar panel admin
        st.markdown("""
        <div class="admin-panel">
            <button class="admin-toggle-btn" onclick="showAdminPanel()">⚙️</button>
        </div>
        <script>
        function showAdminPanel() {
            // Esta función debería comunicarse con Streamlit
            const event = new CustomEvent('showAdminPanel');
            window.parent.document.dispatchEvent(event);
        }
        </script>
        """, unsafe_allow_html=True)
    else:
        # Panel admin expandido
        st.markdown(f"""
        <div class="admin-panel">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong style="color: #FDB931;">🔧 PANEL ADMIN</strong>
                <button onclick="hideAdminPanel()" style="background: none; border: none; color: white; cursor: pointer; font-size: 16px;">×</button>
            </div>
            
            <div class="admin-menu">
                <button onclick="adminAction('logout')" class="admin-menu-item">🚪 Cerrar Sesión</button>
                <button onclick="adminAction('reset')" class="admin-menu-item danger-btn">🔄 Resetear Torneo</button>
                <button onclick="adminAction('backup')" class="admin-menu-item">💾 Crear Backup</button>
                <button onclick="adminAction('stats')" class="admin-menu-item">📊 Ver Estadísticas</button>
            </div>
        </div>
        
        <script>
        function hideAdminPanel() {{
            const event = new CustomEvent('hideAdminPanel');
            window.parent.document.dispatchEvent(event);
        }}
        
        function adminAction(action) {{
            const event = new CustomEvent('adminAction', {{ detail: {{ action: action }} }});
            window.parent.document.dispatchEvent(event);
        }}
        </script>
        """, unsafe_allow_html=True)

# --- HEADER MEJORADO RESPONSIVO ---
def render_header():
    logo_org = "https://cdn-icons-png.flaticon.com/512/1603/1603754.png" 
    logo_spon1 = "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg" 
    logo_spon2 = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
    
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
            <div style="color:#666; font-size:10px; margin-bottom:5px; letter-spacing:1px;">POWERED BY</div>
            <div class="sponsor-logos">
                <img src="{logo_spon1}" class="sponsor-logo">
                <img src="{logo_spon2}" class="sponsor-logo">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. FUNCIONES PARA INSCRIPCIÓN ---
def generate_payment_code():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

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
            "Grado_Valor": int(participant_data["grado"]),
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
            "Estado": "Activo"
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

# --- MANEJO DE EVENTOS JAVASCRIPT ---
st.markdown("""
<script>
// Manejar eventos del panel admin
window.addEventListener('showAdminPanel', function() {
    // Disparar evento para Streamlit
    window.parent.postMessage({type: 'streamlit', 'showAdminPanel': true}, '*');
});

window.addEventListener('hideAdminPanel', function() {
    window.parent.postMessage({type: 'streamlit', 'showAdminPanel': false}, '*');
});

window.addEventListener('adminAction', function(e) {
    window.parent.postMessage({type: 'streamlit', 'adminAction': e.detail.action}, '*');
});

// Manejar votaciones
window.addEventListener('streamlitVote', function(e) {
    window.parent.postMessage({type: 'streamlit', 'vote': e.detail}, '*');
});
</script>
""", unsafe_allow_html=True)

# --- 7. VISTA HOME MEJORADA CON INSCRIPCIÓN ---
if st.session_state.view == "HOME":
    render_header()
    
    # Mostrar panel admin flotante
    render_admin_panel()
    
    errors = validate_data(main_df)
    if errors and st.session_state.get('is_admin', False):
        with st.expander("⚠️ Errores de Validación", expanded=False):
            for error in errors:
                st.error(error)
    
    # Navegación principal
    tab1, tab2, tab3 = st.tabs(["🏆 TORNEO", "📝 INSCRIPCIÓN", "📊 ESTADÍSTICAS"])
    
    with tab1:
        st.markdown("### 📂 SELECCIONA TU CATEGORÍA")
        
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
                        if st.button(weight_class, key=f"m_{w}_{idx}", use_container_width=True):
                            go("BRACKET", w)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if kumite_women:
                    st.markdown("<div style='color:#ef4444; margin-top:20px; margin-bottom:10px; font-weight:bold; font-size:16px;'>WOMEN</div>", unsafe_allow_html=True)
                    st.markdown('<div class="category-grid">', unsafe_allow_html=True)
                    for idx, w in enumerate(kumite_women):
                        weight_class = w.split("| ")[-1]
                        if st.button(weight_class, key=f"w_{w}_{idx}", use_container_width=True):
                            go("BRACKET", w)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        if kata_cats:
            with st.expander("🙏 KATA", expanded=True):
                st.markdown('<div class="category-grid">', unsafe_allow_html=True)
                for idx, cat in enumerate(kata_cats):
                    category_name = cat.split("| ")[-1]
                    if st.button(category_name, key=f"k_{cat}_{idx}", use_container_width=True):
                        go("BRACKET", cat)
                st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📝 SISTEMA DE INSCRIPCIÓN")
        
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
                    grado_options = list(KARATE_GRADES.keys())
                    grado = st.selectbox("Grado *", options=grado_options, 
                                        format_func=lambda x: f"{x} - {KARATE_GRADES[x]['name']}")
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
                uploaded_file = st.file_uploader("Sube tu foto frontal estilo carnet actualizada", 
                                               type=['jpg', 'jpeg', 'png'])
                
                foto_base64 = ""
                if uploaded_file is not None:
                    try:
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
                            
                            # Mostrar participantes agregados
                            st.markdown("#### 📋 PARTICIPANTES AGREGADOS")
                            for i, p in enumerate(st.session_state.group_participants, 1):
                                with st.container():
                                    col_info, col_action = st.columns([4, 1])
                                    with col_info:
                                        st.markdown(f"**{i}. {p['nombre_completo']}** - {p['categoria']}")
                                    with col_action:
                                        if st.button("🗑️", key=f"remove_{i}"):
                                            st.session_state.group_participants.pop(i-1)
                                            st.rerun()
            
            # Para inscripción colectiva, botón para finalizar agregación
            if st.session_state.inscription_type == "colectivo" and len(st.session_state.group_participants) > 0:
                st.markdown("---")
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
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background: #1f2937; padding: 25px; border-radius: 10px; margin: 20px 0;'>
                    <h4 style='color: #FDB931;'>INSCRIPCIÓN COLECTIVA COMPLETADA</h4>
                    <p><strong>Total de participantes:</strong> {len(st.session_state.group_participants)}</p>
                    <p><strong>Código de Pago:</strong> <code>{st.session_state.payment_code}</code></p>
                    <p><strong>Estado:</strong> <span style='color: #FDB931;'>Pendiente de verificación</span></p>
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
        st.markdown("### 📊 ESTADÍSTICAS DEL TORNEO")
        
        if st.session_state.get('is_admin', False):
            # Estadísticas de inscripciones
            st.subheader("📈 INSCRIPCIONES POR CATEGORÍA")
            
            if not inscriptions_df.empty:
                # Convertir DataFrame para análisis
                inscripciones_por_categoria = inscriptions_df['Categoria'].value_counts()
                
                col1, col2 = st.columns(2)
                with col1:
                    total_inscritos = len(inscriptions_df)
                    individuales = len(inscriptions_df[inscriptions_df['Tipo_Inscripcion'] == 'individual'])
                    colectivas = len(inscriptions_df[inscriptions_df['Tipo_Inscripcion'] == 'colectivo'])
                    
                    st.metric("Total Inscritos", total_inscritos)
                    st.metric("Individuales", individuales)
                    st.metric("Colectivas", colectivas)
                    
                    # Emparejados vs no emparejados
                    emparejados = len(inscriptions_df[inscriptions_df['Estado'] == 'Emparejado'])
                    activos = len(inscriptions_df[inscriptions_df['Estado'] == 'Activo'])
                    st.metric("Emparejados", emparejados)
                    st.metric("Activos (sin emparejar)", activos)
                
                with col2:
                    if not inscripciones_por_categoria.empty:
                        st.bar_chart(inscripciones_por_categoria)
                
                # Botones de emparejamiento automático (solo admin)
                st.markdown("---")
                st.subheader("🤖 EMPAREJAMIENTO AUTOMÁTICO")
                
                categoria_emparejar = st.selectbox("Seleccionar categoría para emparejar", 
                                                 options=inscriptions_df['Categoria'].unique())
                
                col_auto, col_random = st.columns(2)
                with col_auto:
                    if st.button("🎯 Emparejamiento Inteligente", use_container_width=True):
                        with st.spinner("Calculando emparejamientos óptimos..."):
                            success = automatic_pairing(categoria_emparejar)
                            if success:
                                st.success(f"Emparejamiento completado para {categoria_emparejar}")
                                time.sleep(2)
                                st.rerun()
                
                with col_random:
                    if st.button("🎲 Emparejamiento Aleatorio", use_container_width=True):
                        success = generate_random_pairing(categoria_emparejar)
                        if success:
                            st.success(f"Emparejamiento aleatorio generado para {categoria_emparejar}")
                            time.sleep(2)
                            st.rerun()
                
                # Lista de inscritos
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

# --- 8. VISTA BRACKET MEJORADA CON LLAVES HORIZONTALES ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    cat_df = main_df[main_df['Category'] == cat].set_index('Match_ID')
    
    def get_row(mid): 
        try: return cat_df.loc[mid]
        except: return pd.Series()
    
    def get_val(row, col): 
        return row[col] if col in row and pd.notna(row[col]) and row[col] != "" else "..."
    
    def generate_share_link():
        import urllib.parse
        base_url = "https://wkb-hub.streamlit.app/"
        params = {"category": urllib.parse.quote(cat)}
        return f"{base_url}?{params}"

    render_header()
    
    # Mostrar panel admin flotante
    render_admin_panel()
    
    # Barra Superior Mejorada y Responsiva
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 INICIO", use_container_width=True):
            go("HOME")
    with col2:
        st.markdown(f"<h3 style='text-align:center; color:#FDB931; margin-top:0;' class='responsive-text-md'>{cat}</h3>", 
                   unsafe_allow_html=True)
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
            
            # Gestión de inscripciones (solo admin)
            st.subheader("👥 GESTIÓN DE INSCRIPCIONES")
            if not inscriptions_df.empty:
                inscritos_categoria = inscriptions_df[inscriptions_df['Categoria'] == cat]
                if not inscritos_categoria.empty:
                    st.metric(f"Inscritos en {cat.split('|')[-1]}", len(inscritos_categoria))
                    with st.expander("Ver inscritos", expanded=False):
                        for _, row in inscritos_categoria.iterrows():
                            st.markdown(f"**{row['Nombre_Completo']}** - {row['Dojo']} - {row['Estado']}")
            
            # Emparejamiento automático para esta categoría
            st.subheader("🤖 EMPAREJAMIENTO")
            col_auto, col_rand = st.columns(2)
            with col_auto:
                if st.button("🎯 Auto", help="Emparejamiento inteligente por similitud", use_container_width=True):
                    with st.spinner("Calculando emparejamientos..."):
                        success = automatic_pairing(cat)
                        if success:
                            st.success("Emparejamiento completado!")
                            time.sleep(2)
                            st.rerun()
            
            with col_rand:
                if st.button("🎲 Aleatorio", help="Emparejamiento aleatorio", use_container_width=True):
                    success = generate_random_pairing(cat)
                    if success:
                        st.success("Emparejamiento aleatorio generado!")
                        time.sleep(2)
                        st.rerun()
            
            # Sistema de reset
            st.subheader("⚠️ SISTEMA DE RESET")
            
            if st.session_state.confirm_reset:
                st.warning("¿ESTÁS SEGURO? Esta acción borrará TODOS los datos.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ SÍ, RESETEAR TODO", type="primary", use_container_width=True):
                        success = reset_all_data()
                        if success:
                            st.success("✅ Sistema reseteado completamente")
                            st.session_state.confirm_reset = False
                            time.sleep(2)
                            st.rerun()
                with col_no:
                    if st.button("❌ CANCELAR", use_container_width=True):
                        st.session_state.confirm_reset = False
                        st.rerun()
            else:
                if st.button("🔄 RESETEAR SISTEMA", type="secondary", use_container_width=True):
                    st.session_state.confirm_reset = True
                    st.rerun()
            
            if 'backups' in st.session_state and st.session_state.backups:
                st.subheader("🔄 Restaurar Backup")
                backup_option = st.selectbox("Seleccionar backup", list(st.session_state.backups.keys()))
                if st.button("Restaurar este backup", use_container_width=True):
                    backup_data = st.session_state.backups[backup_option]
                    restored_df = pd.DataFrame(backup_data)
                    save_data(restored_df)
                    st.success("Backup restaurado!")
                    st.rerun()
            
            st.subheader("✏️ Editar Match")
            match_edit = st.selectbox("Seleccionar match", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
            
            with st.form("edit_match_form"):
                row = get_row(match_edit)
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown(":red[**AKA (Rojo)**]")
                    n1 = st.text_input("Nombre", get_val(row, 'P1_Name'), key=f"n1_{match_edit}")
                    d1 = st.text_input("Dojo/País", get_val(row, 'P1_Dojo'), key=f"d1_{match_edit}")
                    live1 = st.checkbox("En Vivo", value=row.get('Live', False) if not row.empty else False)
                
                with c2:
                    st.markdown(":grey[**SHIRO (Blanco)**]")
                    n2 = st.text_input("Nombre", get_val(row, 'P2_Name'), key=f"n2_{match_edit}")
                    d2 = st.text_input("Dojo/País", get_val(row, 'P2_Dojo'), key=f"d2_{match_edit}")
                
                st.markdown("---")
                
                winner_opts = ["", n1, n2] if n1 != "..." and n2 != "..." else [""]
                curr_w = get_val(row, 'Winner')
                w_idx = winner_opts.index(curr_w) if curr_w in winner_opts else 0
                winner = st.selectbox("GANADOR", winner_opts, index=w_idx)
                
                if st.form_submit_button("💾 GUARDAR CAMBIOS", use_container_width=True):
                    idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==match_edit)].index
                    if not idx.empty:
                        main_df.at[idx[0], 'P1_Name'] = n1
                        main_df.at[idx[0], 'P1_Dojo'] = d1
                        main_df.at[idx[0], 'P2_Name'] = n2
                        main_df.at[idx[0], 'P2_Dojo'] = d2
                        main_df.at[idx[0], 'Winner'] = winner
                        main_df.at[idx[0], 'Live'] = live1
                        
                        if winner and 'Q' in match_edit:
                            q_num = int(match_edit[1])
                            if q_num in [1, 2]:
                                s1_idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']=='S1')].index
                                if not s1_idx.empty:
                                    if q_num == 1:
                                        main_df.at[s1_idx[0], 'P1_Name'] = winner
                                        main_df.at[s1_idx[0], 'P1_Dojo'] = d1 if winner == n1 else d2
                                    else:
                                        main_df.at[s1_idx[0], 'P2_Name'] = winner
                                        main_df.at[s1_idx[0], 'P2_Dojo'] = d1 if winner == n1 else d2
                            elif q_num in [3, 4]:
                                s2_idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']=='S2')].index
                                if not s2_idx.empty:
                                    if q_num == 3:
                                        main_df.at[s2_idx[0], 'P1_Name'] = winner
                                        main_df.at[s2_idx[0], 'P1_Dojo'] = d1 if winner == n1 else d2
                                    else:
                                        main_df.at[s2_idx[0], 'P2_Name'] = winner
                                        main_df.at[s2_idx[0], 'P2_Dojo'] = d1 if winner == n1 else d2
                        
                        save_data(main_df)
                        st.success("✅ Cambios guardados!")
                        time.sleep(1)
                        st.rerun()

    # --- VOTACIÓN MEJORADA ---
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
    
    # Mostrar botones de votación
    st.markdown('<div class="vote-buttons-container">', unsafe_allow_html=True)
    
    for m in ['Q1', 'Q2', 'Q3', 'Q4']:
        row = get_row(m)
        p1, p2 = get_val(row, 'P1_Name'), get_val(row, 'P2_Name')
        
        if p1 != "..." and p2 != "...":
            v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
            v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
            total = v1 + v2
            
            if total > 0:
                pct1 = (v1 / total * 100)
                pct2 = (v2 / total * 100)
            else:
                pct1 = pct2 = 0
            
            live_indicator = "🔴 " if row.get('Live', False) else ""
            
            col = st.container()
            with col:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(145deg, #1f2937, #111827);
                    padding: 15px; 
                    border-radius: 10px; 
                    border: 1px solid #374151;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                ">
                    <div style="color: #FDB931; font-weight: bold; margin-bottom: 12px; font-size: 15px; text-align: center;">
                        {live_indicator}MATCH {m}
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 14px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="color: #ef4444; font-weight: bold;">🔴</div>
                            <div style="font-size: 13px;">{p1[:15]}{'...' if len(p1) > 15 else ''}</div>
                        </div>
                        <div style="color: #666; font-weight: bold;">VS</div>
                        <div style="text-align: center; flex: 1;">
                            <div style="color: white; font-weight: bold;">⚪</div>
                            <div style="font-size: 13px;">{p2[:15]}{'...' if len(p2) > 15 else ''}</div>
                        </div>
                    </div>
                    
                    <div style="background: #374151; height: 8px; border-radius: 4px; margin-bottom: 12px; overflow: hidden;">
                        <div style="width: {pct1}%; height: 100%; background: linear-gradient(90deg, #ef4444, #dc2626); float: left;"></div>
                        <div style="width: {pct2}%; height: 100%; background: linear-gradient(90deg, #ffffff, #d1d5db); float: left;"></div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                        <button onclick="streamlitVote('{m}', 'P1')" style="
                            flex: 1; 
                            padding: 10px; 
                            background: linear-gradient(135deg, #ef4444, #dc2626); 
                            color: white; 
                            border: none; 
                            border-radius: 6px; 
                            cursor: pointer; 
                            font-size: 13px;
                            font-family: 'Roboto Condensed', sans-serif;
                            font-weight: bold;
                            transition: all 0.3s ease;
                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(239, 68, 68, 0.3)'"
                        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                            🔴 VOTAR ROJO
                        </button>
                        <button onclick="streamlitVote('{m}', 'P2')" style="
                            flex: 1; 
                            padding: 10px; 
                            background: linear-gradient(135deg, #ffffff, #d1d5db); 
                            color: black; 
                            border: none; 
                            border-radius: 6px; 
                            cursor: pointer; 
                            font-size: 13px;
                            font-family: 'Roboto Condensed', sans-serif;
                            font-weight: bold;
                            transition: all 0.3s ease;
                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(255, 255, 255, 0.3)'"
                        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                            ⚪ VOTAR BLANCO
                        </button>
                    </div>
                    
                    <div style="font-size: 12px; color: #9ca3af; text-align: center; display: flex; justify-content: space-between;">
                        <span>🔴 {int(pct1)}%</span>
                        <span>Total: {v1 + v2}</span>
                        <span>⚪ {int(pct2)}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # JavaScript para votación
    st.markdown("""
    <script>
    function streamlitVote(matchId, player) {
        // Esta función se comunicaría con Streamlit
        const event = new CustomEvent('streamlitVote', { 
            detail: { matchId: matchId, player: player } 
        });
        window.parent.document.dispatchEvent(event);
    }
    
    // Manejar eventos táctiles para móviles
    document.addEventListener('touchstart', function() {}, {passive: true});
    </script>
    """, unsafe_allow_html=True)

    # --- GENERADOR BRACKET HORIZONTAL RESPONSIVO ---
    def render_player(row, p_prefix, color_class):
        name = get_val(row, f'{p_prefix}_Name')
        dojo = get_val(row, f'{p_prefix}_Dojo')
        
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
        
        return f"""
        <div class="player-box {color_class}">
            {live_indicator}
            <div class="p-name">{name}</div>
            <div class="p-details">
                <span>🥋 {dojo}</span>
                <span>{int(pct)}%</span>
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
                        <div class="p-name">{w_q1}</div>
                        <div class="p-details">
                            <span>🥋 {get_val(r_q1, 'P1_Dojo') if w_q1 == get_val(r_q1, 'P1_Name') else get_val(r_q1, 'P2_Dojo')}</span>
                        </div>
                    </div>
                    <div class="player-box border-white">
                        <div class="p-name">{w_q2}</div>
                        <div class="p-details">
                            <span>🥋 {get_val(r_q2, 'P1_Dojo') if w_q2 == get_val(r_q2, 'P1_Name') else get_val(r_q2, 'P2_Dojo')}</span>
                        </div>
                        <div class="line-r"></div>
                    </div>
                </div>
                <div style="height: 50%; display: flex; flex-direction: column; justify-content: center; position: relative; margin-top: 40px;">
                    <div class="conn-v" style="height: 120px; top: 50%; transform: translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top: 60px;">
                        <div class="p-name">{w_q3}</div>
                        <div class="p-details">
                            <span>🥋 {get_val(r_q3, 'P1_Dojo') if w_q3 == get_val(r_q3, 'P1_Name') else get_val(r_q3, 'P2_Dojo')}</span>
                        </div>
                    </div>
                    <div class="player-box border-white">
                        <div class="p-name">{w_q4}</div>
                        <div class="p-details">
                            <span>🥋 {get_val(r_q4, 'P1_Dojo') if w_q4 == get_val(r_q4, 'P1_Name') else get_val(r_q4, 'P2_Dojo')}</span>
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
                        <div class="p-name">{w_s1}</div>
                        <div class="p-details">
                            <span>🥋 {get_val(r_s1, 'P1_Dojo') if w_s1 == get_val(r_s1, 'P1_Name') else get_val(r_s1, 'P2_Dojo')}</span>
                        </div>
                    </div>
                    <div class="player-box border-white">
                        <div class="p-name">{w_s2}</div>
                        <div class="p-details">
                            <span>🥋 {get_val(r_s2, 'P1_Dojo') if w_s2 == get_val(r_s2, 'P1_Name') else get_val(r_s2, 'P2_Dojo')}</span>
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
                        {w_f1 if w_f1 != "..." else "POR DEFINIR"}
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

# --- 9. MANEJO DE EVENTOS GLOBALES ---
# Escuchar eventos de JavaScript
try:
    # Esto capturaría eventos del panel admin flotante
    # Nota: En Streamlit Cloud necesitarías configuración adicional para WebSockets
    pass
except:
    pass

# --- 10. FUNCIÓN PRINCIPAL DE RESET ---
def confirm_reset_dialog():
    """Diálogo de confirmación para resetear el sistema"""
    if st.session_state.confirm_reset:
        st.markdown("""
        <div class="overlay"></div>
        <div class="confirmation-modal">
            <h3 style="color: #ef4444; text-align: center;">⚠️ ¿RESETEAR SISTEMA COMPLETO?</h3>
            <p style="text-align: center; margin: 20px 0;">
                Esta acción <strong>NO SE PUEDE DESHACER</strong>. Se borrarán:<br>
                • Todos los brackets y resultados<br>
                • Todas las inscripciones<br>
                • Todos los votos y estadísticas
            </p>
            
            <div style="display: flex; gap: 10px; margin-top: 30px;">
                <button onclick="confirmReset()" style="
                    flex: 1; 
                    padding: 12px; 
                    background: linear-gradient(135deg, #ef4444, #dc2626);
                    color: white; 
                    border: none; 
                    border-radius: 6px; 
                    font-weight: bold;
                    cursor: pointer;
                ">
                    ✅ SÍ, RESETEAR TODO
                </button>
                <button onclick="cancelReset()" style="
                    flex: 1; 
                    padding: 12px; 
                    background: #374151; 
                    color: white; 
                    border: none; 
                    border-radius: 6px; 
                    font-weight: bold;
                    cursor: pointer;
                ">
                    ❌ CANCELAR
                </button>
            </div>
        </div>
        
        <script>
        function confirmReset() {
            window.parent.postMessage({type: 'streamlit', 'resetConfirm': true}, '*');
        }
        function cancelReset() {
            window.parent.postMessage({type: 'streamlit', 'resetConfirm': false}, '*');
        }
        </script>
        """, unsafe_allow_html=True)

# Mostrar diálogo de reset si está activo
if st.session_state.get('confirm_reset', False):
    confirm_reset_dialog()
