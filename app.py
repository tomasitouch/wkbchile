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

# --- 2. CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_event(event_type, details):
    """Registra eventos en el sistema"""
    logger.info(f"{event_type}: {details}")

# --- 3. CONFIGURACIÓN DE HOJAS GOOGLE SHEETS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

# Nombres de las hojas requeridas
SHEET_NAMES = {
    "brackets": "Brackets",
    "inscriptions": "Inscripciones",
    "config": "Configuracion",
    "payments": "Pagos",
    "backup": "Backup"  # Nueva hoja para backups
}

# --- 4. CREDENCIALES MERCADO PAGO ---
def init_mercadopago():
    try:
        MP_ACCESS_TOKEN = st.secrets["mercadopago"]["access_token"]
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        return sdk
    except Exception as e:
        st.error(f"Error inicializando Mercado Pago: {str(e)}")
        log_event("ERROR_MERCADOPAGO_INIT", str(e))
        return None

# --- 5. SEGURIDAD MEJORADA ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # sha256("wkbadmin123")

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 6. ESTILOS CSS MEJORADOS CON BRACKETS PROFESIONALES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    @keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    @keyframes slideIn { from { transform: translateX(-100%); } to { transform: translateX(0); } }
    
    .stApp { 
        background-color: #0e1117; 
        color: white; 
        font-family: 'Inter', sans-serif !important;
        min-height: 100vh;
    }
    
    h1, h2, h3, h4 { 
        font-family: 'Roboto Condensed', sans-serif !important; 
        text-transform: uppercase; 
        margin-bottom: 1rem !important;
    }
    
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
    }
    div.stButton > button:hover { 
        border-color: #ef4444; 
        color: #ef4444; 
        transform: translateX(5px); 
    }
    
    .payment-methods {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 30px 0;
        flex-wrap: wrap;
    }
    
    .payment-method {
        background: linear-gradient(145deg, #1f2937, #111827);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        width: 150px;
        border: 2px solid #374151;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .payment-method:hover {
        border-color: #00B1EA;
        transform: translateY(-5px);
    }
    
    .payment-method.selected {
        border-color: #00B1EA;
        background: rgba(0, 177, 234, 0.1);
        box-shadow: 0 5px 15px rgba(0, 177, 234, 0.3);
    }
    
    .payment-icon {
        font-size: 40px;
        margin-bottom: 10px;
    }
    
    .mercado-pago-btn {
        background: linear-gradient(135deg, #00B1EA, #009EE3) !important;
        color: white !important;
        border: none !important;
        padding: 20px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        margin: 20px 0 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
    }
    
    .mercado-pago-btn:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 20px rgba(0, 177, 234, 0.4) !important;
    }
    
    .payment-status {
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        text-align: center;
        animation: fadeIn 0.5s ease;
    }
    
    .status-approved {
        background: rgba(16, 185, 129, 0.2);
        border: 2px solid #10B981;
        color: #10B981;
    }
    
    .status-pending {
        background: rgba(245, 158, 11, 0.2);
        border: 2px solid #F59E0B;
        color: #F59E0B;
    }
    
    .status-rejected {
        background: rgba(239, 68, 68, 0.2);
        border: 2px solid #EF4444;
        color: #EF4444;
    }
    
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
    
    .form-container {
        background: linear-gradient(145deg, #1f2937, #111827);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #374151;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    .stage-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 12px;
        margin-left: 10px;
        text-transform: uppercase;
    }
    
    .stage-open {
        background: linear-gradient(135deg, #10B981, #059669);
        color: white;
    }
    
    .stage-closed {
        background: linear-gradient(135deg, #EF4444, #DC2626);
        color: white;
    }
    
    /* ============================= */
    /* ESTILOS PARA BRACKETS PROFESIONALES */
    /* ============================= */
    
    .bracket-wrapper {
        display: flex;
        flex-direction: row;
        padding: 40px 20px;
        justify-content: flex-start;
        align-items: flex-start;
        overflow-x: auto;
        gap: 0;
        min-height: 600px;
        position: relative;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
    }
    
    .bracket-round {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        width: 280px;
        flex-shrink: 0;
        position: relative;
        min-height: 500px;
        padding: 0 20px;
    }
    
    .bracket-round:not(:last-child)::after {
        content: "";
        position: absolute;
        right: 0;
        top: 50px;
        bottom: 50px;
        width: 50px;
        background: linear-gradient(90deg, transparent, rgba(55, 65, 81, 0.3));
        z-index: -1;
    }
    
    .bracket-match {
        display: flex;
        flex-direction: column;
        margin: 15px 0;
        position: relative;
        padding: 20px 0;
        min-height: 120px;
    }
    
    /* Líneas conectoras horizontales */
    .bracket-match::before {
        content: "";
        position: absolute;
        right: -25px;
        top: 50%;
        width: 25px;
        height: 2px;
        background: linear-gradient(90deg, #374151, #6b7280);
        z-index: 1;
    }
    
    /* Líneas conectoras verticales */
    .bracket-match:nth-child(odd)::after {
        content: "";
        position: absolute;
        right: -25px;
        top: 50%;
        width: 2px;
        height: calc(100% + 40px);
        background: linear-gradient(180deg, #6b7280, transparent);
        z-index: 1;
    }
    
    .bracket-match:nth-child(even)::after {
        content: "";
        position: absolute;
        right: -25px;
        bottom: 50%;
        width: 2px;
        height: calc(100% + 40px);
        background: linear-gradient(180deg, transparent, #6b7280);
        z-index: 1;
    }
    
    .bracket-round:last-child .bracket-match::before,
    .bracket-round:last-child .bracket-match::after {
        display: none;
    }
    
    .bracket-player {
        background: linear-gradient(145deg, #1f2937, #111827);
        border: 1px solid #374151;
        padding: 12px 15px;
        width: 240px;
        font-size: 14px;
        color: #e5e7eb;
        position: relative;
        z-index: 2;
        transition: all 0.3s ease;
        cursor: pointer;
        min-height: 60px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .bracket-player:hover {
        transform: translateX(5px);
        border-color: #FDB931;
        box-shadow: 0 5px 15px rgba(253, 185, 49, 0.2);
    }
    
    .bracket-player.winner {
        border-color: #FDB931;
        background: linear-gradient(145deg, rgba(253, 185, 49, 0.1), rgba(31, 41, 55, 0.9));
        color: #FDB931;
        font-weight: bold;
        border-width: 2px;
    }
    
    .bracket-player.top { 
        border-radius: 8px 8px 0 0; 
        border-bottom: none;
        margin-bottom: -1px;
    }
    
    .bracket-player.bottom { 
        border-radius: 0 0 8px 8px;
        margin-top: -1px;
    }
    
    .player-name {
        font-family: 'Roboto Condensed', sans-serif;
        font-weight: bold;
        font-size: 15px;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .player-dojo {
        font-size: 11px;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .player-votes {
        font-size: 10px;
        color: #FDB931;
        margin-top: 4px;
        font-weight: bold;
    }
    
    .round-header {
        text-align: center;
        color: #FDB931;
        font-family: 'Roboto Condensed', sans-serif;
        font-weight: bold;
        margin-bottom: 30px;
        font-size: 16px;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 10px;
        background: rgba(31, 41, 55, 0.5);
        border-radius: 8px;
        border: 1px solid #374151;
    }
    
    .vote-button {
        margin-top: 8px;
        padding: 4px 12px;
        font-size: 11px;
        background: rgba(253, 185, 49, 0.1);
        border: 1px solid #FDB931;
        color: #FDB931;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-family: 'Roboto Condensed', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .vote-button:hover {
        background: rgba(253, 185, 49, 0.3);
        transform: scale(1.05);
    }
    
    .vote-button.voted {
        background: rgba(16, 185, 129, 0.2);
        border-color: #10B981;
        color: #10B981;
    }
    
    .champion-box {
        background: linear-gradient(135deg, #FDB931 0%, #d9a024 100%);
        color: black !important;
        text-align: center;
        padding: 25px 20px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 20px;
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
        margin-top: 30px;
        font-family: 'Roboto Condensed', sans-serif;
        text-transform: uppercase;
    }
    
    .champion-box::before {
        content: '🏆';
        font-size: 50px;
        position: absolute;
        opacity: 0.3;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
    }
    
    .champion-dojo {
        font-size: 14px;
        color: #333;
        margin-top: 5px;
        font-weight: normal;
        text-transform: none;
    }
    
    @media (max-width: 768px) {
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
        
        .payment-method {
            width: 120px;
            padding: 15px;
        }
        
        .bracket-wrapper {
            padding: 20px 10px;
        }
        
        .bracket-round {
            width: 220px;
        }
        
        .bracket-player {
            width: 200px;
            padding: 10px 12px;
        }
        
        .player-name {
            font-size: 13px;
        }
        
        .player-dojo {
            font-size: 10px;
        }
    }
    
    /* Animaciones */
    @keyframes confetti {
        0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
    
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background: #FDB931;
        top: -10px;
        animation: confetti 3s linear forwards;
        z-index: 1000;
    }
    
    .success-animation {
        text-align: center;
        padding: 50px 20px;
    }
    
    .success-icon {
        font-size: 80px;
        color: #10B981;
        margin-bottom: 20px;
        animation: bounce 1s infinite alternate;
    }
    
    @keyframes bounce {
        from { transform: translateY(0px); }
        to { transform: translateY(-20px); }
    }
    
    /* Loading spinner */
    .loading-spinner {
        display: inline-block;
        width: 50px;
        height: 50px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #FDB931;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Alert boxes */
    .alert-success {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10B981;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin: 15px 0;
    }
    
    .alert-warning {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #F59E0B;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin: 15px 0;
    }
    
    .alert-error {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #EF4444;
        padding: 15px;
        border-radius: 0 8px 8px 0;
        margin: 15px 0;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(145deg, #1f2937, #111827);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #374151;
        text-align: center;
    }
    
    .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #FDB931;
        margin: 10px 0;
    }
    
    .stat-label {
        font-size: 12px;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- 7. CONFIGURACIÓN DEL TORNEO ---
CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATEGORIES = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

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

# --- 8. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# --- 9. FUNCIONES DE INICIALIZACIÓN DE HOJAS ---
def initialize_sheets():
    """Inicializa todas las hojas necesarias en Google Sheets"""
    try:
        conn = get_connection()
        
        # 1. Hoja de Configuración
        config_data = [
            ["setting", "value", "description"],
            ["tournament_stage", "inscription", "Etapa del torneo: inscription o competition"],
            ["registration_open", "true", "Si las inscripciones están abiertas"],
            ["tournament_name", "WKB Chile 2024", "Nombre del torneo"],
            ["inscription_price", "50000", "Precio de inscripción individual en CLP"],
            ["group_discount_3", "0.9", "Descuento para 3 personas (10%)"],
            ["group_discount_5", "0.8", "Descuento para 5 personas (20%)"],
            ["mp_public_key", st.secrets["mercadopago"]["public_key"], "Public key de Mercado Pago"],
            ["mp_access_token", st.secrets["mercadopago"]["access_token"], "Access token de Mercado Pago"],
            ["auto_confirm_payment", "true", "Confirmar inscripción automáticamente al pagar"],
            ["last_backup", "", "Fecha del último backup"],
            ["payment_check_interval", "30", "Intervalo en segundos para verificar pagos"]
        ]
        
        config_df = pd.DataFrame(config_data[1:], columns=config_data[0])
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=config_df)
        
        # 2. Hoja de Inscripciones
        inscriptions_columns = [
            "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", "Grado_Valor",
            "Dojo", "Organizacion", "Telefono", "Email", "Categoria", 
            "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64",
            "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID", "Estado",
            "MP_Payment_ID", "MP_Status", "MP_Date_Approved", "Last_Updated"
        ]
        
        inscriptions_df = pd.DataFrame(columns=inscriptions_columns)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=inscriptions_df)
        
        # 3. Hoja de Pagos
        payments_columns = [
            "payment_id", "inscription_id", "transaction_amount", "currency_id",
            "status", "status_detail", "date_created", "date_approved",
            "payment_method_id", "payment_type_id", "payer_email",
            "payer_identification", "notification_url", "webhook_received",
            "last_checked"
        ]
        
        payments_df = pd.DataFrame(columns=payments_columns)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["payments"], data=payments_df)
        
        # 4. Hoja de Brackets con columnas para votos
        brackets_columns = [
            "Category", "Match_ID", "Round", "Match_Number",
            "P1_Name", "P1_ID", "P1_Dojo", "P1_Votes",
            "P2_Name", "P2_ID", "P2_Dojo", "P2_Votes",
            "Winner", "Winner_ID", "Live", "Status",
            "Total_Votes", "Vote_History", "Last_Vote_Time"
        ]
        
        all_brackets = []
        for category in ALL_CATEGORIES:
            for i in range(1, 5):
                all_brackets.append({
                    "Category": category,
                    "Match_ID": f"Q{i}",
                    "Round": "Quarterfinal",
                    "Match_Number": i,
                    "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
                    "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
                    "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending",
                    "Total_Votes": 0, "Vote_History": "[]", "Last_Vote_Time": ""
                })
            for i in range(1, 3):
                all_brackets.append({
                    "Category": category,
                    "Match_ID": f"S{i}",
                    "Round": "Semifinal",
                    "Match_Number": i,
                    "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
                    "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
                    "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending",
                    "Total_Votes": 0, "Vote_History": "[]", "Last_Vote_Time": ""
                })
            all_brackets.append({
                "Category": category,
                "Match_ID": "F1",
                "Round": "Final",
                "Match_Number": 1,
                "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
                "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
                "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending",
                "Total_Votes": 0, "Vote_History": "[]", "Last_Vote_Time": ""
            })
        
        brackets_df = pd.DataFrame(all_brackets)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=brackets_df)
        
        # 5. Hoja de Backup
        backup_columns = ["backup_date", "backup_type", "data", "notes"]
        backup_df = pd.DataFrame(columns=backup_columns)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["backup"], data=backup_df)
        
        create_backup("initial")
        
        st.cache_data.clear()
        log_event("SHEETS_INITIALIZED", "Todas las hojas fueron inicializadas exitosamente")
        return True
    except Exception as e:
        st.error(f"Error inicializando hojas: {str(e)}")
        log_event("ERROR_SHEETS_INIT", str(e))
        return False

# --- 10. FUNCIONES DE CARGA DE DATOS CON CACHÉ Y SPINNER ---
@st.cache_data(ttl=15, show_spinner="Cargando brackets...")
def load_brackets():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], ttl=15)
        log_event("BRACKETS_LOADED", f"Cargados {len(df)} registros")
        return df
    except Exception as e:
        st.error(f"Error cargando brackets: {str(e)}")
        log_event("ERROR_BRACKETS_LOAD", str(e))
        return pd.DataFrame()

@st.cache_data(ttl=15, show_spinner="Cargando inscripciones...")
def load_inscriptions():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], ttl=15)
        log_event("INSCRIPTIONS_LOADED", f"Cargadas {len(df)} inscripciones")
        return df
    except Exception as e:
        st.error(f"Error cargando inscripciones: {str(e)}")
        log_event("ERROR_INSCRIPTIONS_LOAD", str(e))
        return pd.DataFrame()

@st.cache_data(ttl=15, show_spinner="Cargando configuración...")
def load_config():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=15)
        if df.empty:
            initialize_sheets()
            df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=15)
        log_event("CONFIG_LOADED", f"Cargada configuración con {len(df)} parámetros")
        return df
    except Exception as e:
        try:
            initialize_sheets()
            conn = get_connection()
            df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=15)
            return df
        except Exception as e2:
            log_event("ERROR_CONFIG_LOAD", f"{str(e)} | {str(e2)}")
            return pd.DataFrame(columns=["setting", "value", "description"])

@st.cache_data(ttl=15, show_spinner="Cargando pagos...")
def load_payments():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["payments"], ttl=15)
        log_event("PAYMENTS_LOADED", f"Cargados {len(df)} pagos")
        return df
    except Exception as e:
        st.error(f"Error cargando pagos: {str(e)}")
        log_event("ERROR_PAYMENTS_LOAD", str(e))
        return pd.DataFrame()

def save_inscriptions(df):
    try:
        conn = get_connection()
        # Agregar timestamp de actualización
        df["Last_Updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=df)
        st.cache_data.clear()
        log_event("INSCRIPTIONS_SAVED", f"Guardadas {len(df)} inscripciones")
    except Exception as e:
        st.error(f"Error guardando inscripciones: {str(e)}")
        log_event("ERROR_INSCRIPTIONS_SAVE", str(e))

def save_payments(df):
    try:
        conn = get_connection()
        df["last_checked"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["payments"], data=df)
        st.cache_data.clear()
        log_event("PAYMENTS_SAVED", f"Guardados {len(df)} pagos")
    except Exception as e:
        st.error(f"Error guardando pagos: {str(e)}")
        log_event("ERROR_PAYMENTS_SAVE", str(e))

def save_brackets(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=df)
        st.cache_data.clear()
        log_event("BRACKETS_SAVED", f"Guardados {len(df)} brackets")
    except Exception as e:
        st.error(f"Error guardando brackets: {str(e)}")
        log_event("ERROR_BRACKETS_SAVE", str(e))

def save_config(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=df)
        st.cache_data.clear()
        log_event("CONFIG_SAVED", "Configuración guardada")
    except Exception as e:
        st.error(f"Error guardando configuración: {str(e)}")
        log_event("ERROR_CONFIG_SAVE", str(e))

# --- 11. FUNCIONES DE GESTIÓN DEL TORNEO ---
def get_tournament_stage():
    try:
        config_df = load_config()
        if config_df.empty:
            return "inscription"
        stage_row = config_df[config_df['setting'] == 'tournament_stage']
        if stage_row.empty:
            return "inscription"
        return stage_row.iloc[0]['value']
    except Exception as e:
        log_event("ERROR_GET_TOURNAMENT_STAGE", str(e))
        return "inscription"

def is_registration_open():
    try:
        config_df = load_config()
        if config_df.empty:
            return True
        reg_row = config_df[config_df['setting'] == 'registration_open']
        if reg_row.empty:
            return True
        value = reg_row.iloc[0]['value']
        if pd.isna(value):
            return True
        return str(value).lower() == 'true'
    except Exception as e:
        log_event("ERROR_CHECK_REGISTRATION", str(e))
        return True

def set_registration_status(status):
    try:
        config_df = load_config()
        if config_df.empty:
            return False
        config_df.loc[config_df['setting'] == 'registration_open', 'value'] = str(status).lower()
        save_config(config_df)
        log_event("REGISTRATION_STATUS_CHANGED", f"Nuevo estado: {status}")
        return True
    except Exception as e:
        log_event("ERROR_SET_REGISTRATION_STATUS", str(e))
        return False

def set_tournament_stage(stage):
    try:
        config_df = load_config()
        if config_df.empty:
            return False
        config_df.loc[config_df['setting'] == 'tournament_stage', 'value'] = stage
        save_config(config_df)
        log_event("TOURNAMENT_STAGE_CHANGED", f"Nueva etapa: {stage}")
        return True
    except Exception as e:
        log_event("ERROR_SET_TOURNAMENT_STAGE", str(e))
        return False

# --- 12. FUNCIONES DE MERCADO PAGO ---
def create_mercadopago_preference(total_amount, description, participant_email, inscription_id, return_url=None):
    """Crea una preferencia de pago en Mercado Pago"""
    try:
        sdk = init_mercadopago()
        if not sdk:
            return None
        
        # URL de notificación (webhook) - usando polling en lugar de webhook
        base_url = st.secrets.get("public_url", "https://wkbchile-br5ucwq5ptkox2fnxasjyp.streamlit.app")
        
        # Crear preferencia de pago
        preference_data = {
            "items": [
                {
                    "title": f"Inscripción WKB - {description}",
                    "quantity": 1,
                    "currency_id": "CLP",
                    "unit_price": float(total_amount)
                }
            ],
            "payer": {
                "email": participant_email
            },
            "payment_methods": {
                "excluded_payment_methods": [],
                "excluded_payment_types": [],
                "installments": 1
            },
            "back_urls": {
                "success": f"{base_url}/?payment=success&code={inscription_id}",
                "failure": f"{base_url}/?payment=failure&code={inscription_id}",
                "pending": f"{base_url}/?payment=pending&code={inscription_id}"
            },
            "auto_return": "approved",
            "external_reference": inscription_id,
            "statement_descriptor": "WKB TORNEO",
            "expires": True,
            "expiration_date_from": datetime.datetime.now().isoformat(),
            "expiration_date_to": (datetime.datetime.now() + datetime.timedelta(hours=24)).isoformat()
        }
        
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response and "response" in preference_response:
            log_event("MERCADOPAGO_PREFERENCE_CREATED", f"Inscripción: {inscription_id}, Monto: {total_amount}")
            return preference_response["response"]
        else:
            st.error(f"Error creando preferencia: {preference_response}")
            log_event("ERROR_MERCADOPAGO_PREFERENCE", str(preference_response))
            return None
            
    except Exception as e:
        st.error(f"Error en Mercado Pago: {str(e)}")
        log_event("ERROR_MERCADOPAGO_CREATE", str(e))
        return None

def process_mercadopago_payment(payment_data):
    """Procesa la respuesta de pago de Mercado Pago"""
    try:
        payments_df = load_payments()
        
        # Extraer información del pago
        payment_info = {
            "payment_id": payment_data.get("id"),
            "inscription_id": payment_data.get("external_reference"),
            "transaction_amount": payment_data.get("transaction_amount"),
            "currency_id": payment_data.get("currency_id"),
            "status": payment_data.get("status"),
            "status_detail": payment_data.get("status_detail"),
            "date_created": payment_data.get("date_created"),
            "date_approved": payment_data.get("date_approved"),
            "payment_method_id": payment_data.get("payment_method_id"),
            "payment_type_id": payment_data.get("payment_type_id"),
            "payer_email": payment_data.get("payer", {}).get("email"),
            "payer_identification": str(payment_data.get("payer", {}).get("identification", {})),
            "notification_url": payment_data.get("notification_url"),
            "webhook_received": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_checked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Verificar si el pago ya existe
        existing_payment = payments_df[payments_df["payment_id"] == payment_info["payment_id"]]
        
        if not existing_payment.empty:
            # Actualizar pago existente
            for key, value in payment_info.items():
                payments_df.loc[payments_df["payment_id"] == payment_info["payment_id"], key] = value
        else:
            # Agregar nuevo pago
            new_payment = pd.DataFrame([payment_info])
            payments_df = pd.concat([payments_df, new_payment], ignore_index=True)
        
        save_payments(payments_df)
        
        # Actualizar estado de la inscripción si el pago está aprobado
        if payment_info["status"] == "approved":
            inscriptions_df = load_inscriptions()
            mask = inscriptions_df["Codigo_Pago"] == payment_info["inscription_id"]
            
            if not inscriptions_df[mask].empty:
                inscriptions_df.loc[mask, "Estado_Pago"] = "Confirmado"
                inscriptions_df.loc[mask, "MP_Payment_ID"] = payment_info["payment_id"]
                inscriptions_df.loc[mask, "MP_Status"] = payment_info["status"]
                inscriptions_df.loc[mask, "MP_Date_Approved"] = payment_info["date_approved"]
                inscriptions_df.loc[mask, "Estado"] = "Inscrito"
                
                save_inscriptions(inscriptions_df)
                
                # Enviar notificación por email (simulado)
                send_confirmation_email(inscriptions_df[mask].iloc[0])
                
                log_event("PAYMENT_PROCESSED_SUCCESS", f"Inscripción: {payment_info['inscription_id']}, Pago: {payment_info['payment_id']}")
                return True
        
        log_event("PAYMENT_PROCESSED", f"Estado: {payment_info['status']}, Inscripción: {payment_info['inscription_id']}")
        return False
        
    except Exception as e:
        st.error(f"Error procesando pago: {str(e)}")
        log_event("ERROR_PAYMENT_PROCESS", str(e))
        return False

def get_payment_status(payment_id):
    """Consulta el estado de un pago en Mercado Pago"""
    try:
        sdk = init_mercadopago()
        if not sdk:
            return None
        
        payment_response = sdk.payment().get(payment_id)
        
        if payment_response and "response" in payment_response:
            return payment_response["response"]
        return None
        
    except Exception as e:
        log_event("ERROR_CHECK_PAYMENT_STATUS", str(e))
        return None

def check_payment_status_periodically(payment_code):
    """Verifica el estado del pago periódicamente"""
    try:
        inscriptions_df = load_inscriptions()
        payment_record = inscriptions_df[inscriptions_df["Codigo_Pago"] == payment_code]
        
        if not payment_record.empty:
            status = payment_record.iloc[0]["Estado_Pago"]
            if status == "Confirmado":
                return "success"
            elif status == "Rechazado":
                return "failure"
        
        # También verificar en la hoja de pagos
        payments_df = load_payments()
        payment_record = payments_df[payments_df["inscription_id"] == payment_code]
        
        if not payment_record.empty:
            status = payment_record.iloc[0]["status"]
            if status == "approved":
                return "success"
            elif status == "rejected":
                return "failure"
        
        return "pending"
    except Exception as e:
        log_event("ERROR_CHECK_PAYMENT_PERIODIC", str(e))
        return "pending"

# --- 13. FUNCIONES DE UTILIDAD ---
def render_header():
    """Renderiza el encabezado con el logo y sponsors"""
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-size: 40px;">🥋</span>
                <div>
                    <h1 style="margin: 0; color: white; font-size: 24px;">WKB Official Hub</h1>
                    <p style="margin: 0; color: #FDB931; font-size: 14px;">World Kyokushin Budokai Chile</p>
                </div>
            </div>
        </div>
        <div class="header-sponsors">
            <div style="color: #9ca3af; font-size: 10px; margin-bottom: 5px; text-transform: uppercase;">Official Sponsors</div>
            <div class="sponsor-logos">
                <span style="font-size: 20px;" title="Sponsor 1">🏆</span>
                <span style="font-size: 20px;" title="Sponsor 2">🔥</span>
                <span style="font-size: 20px;" title="Sponsor 3">🛡️</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def validate_participant_data(data):
    """Valida los datos del participante"""
    errors = []
    
    # Validar nombre
    if len(data["nombre_completo"]) < 5:
        errors.append("Nombre completo debe tener al menos 5 caracteres")
    
    # Validar edad
    if data["edad"] < 18:
        errors.append("Debes ser mayor de 18 años para participar")
    elif data["edad"] > 80:
        errors.append("Edad no válida")
    
    # Validar teléfono
    phone_pattern = r'^\+?[\d\s\-\(\)]{8,15}$'
    if not re.match(phone_pattern, data["telefono"]):
        errors.append("Teléfono inválido. Usa formato: +56912345678")
    
    # Validar email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data["email"]):
        errors.append("Email inválido")
    
    # Validar peso y estatura
    if data["peso"] < 30 or data["peso"] > 150:
        errors.append("Peso debe estar entre 30kg y 150kg")
    
    if data["estatura"] < 100 or data["estatura"] > 220:
        errors.append("Estatura debe estar entre 100cm y 220cm")
    
    return errors

def calculate_price(participants_count, inscription_type="individual"):
    try:
        config_df = load_config()
        base_price = 50000
        
        if not config_df.empty:
            price_row = config_df[config_df['setting'] == 'inscription_price']
            if not price_row.empty:
                try:
                    base_price = float(price_row.iloc[0]['value'])
                except:
                    pass
        
        if inscription_type == "colectivo":
            if participants_count >= 5:
                discount = 0.8
            elif participants_count >= 3:
                discount = 0.9
            else:
                discount = 1.0
            total = base_price * participants_count * discount
            return round(total)
        else:
            return base_price * participants_count
    except Exception as e:
        log_event("ERROR_CALCULATE_PRICE", str(e))
        return 50000 * participants_count

def generate_inscription_code():
    """Genera un código único para la inscripción"""
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    random_chars = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"WKB{timestamp}{random_chars}"

def generate_participant_id():
    """Genera un ID único para el participante"""
    return f"P{str(uuid.uuid4())[:8].upper()}"

def generate_group_id():
    """Genera un ID único para grupos"""
    return f"G{str(uuid.uuid4())[:6].upper()}"

def send_confirmation_email(participant_data):
    """Envía email de confirmación (simulado)"""
    try:
        # En producción, integrar con servicio de email
        log_event("EMAIL_SENT", f"Confirmación enviada a {participant_data['Email']}")
        return True
    except Exception as e:
        log_event("ERROR_EMAIL_SEND", str(e))
        return False

def create_backup(backup_type="manual"):
    """Crea un backup de los datos"""
    try:
        conn = get_connection()
        
        # Recopilar datos de todas las hojas
        backup_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "backup_type": backup_type,
            "inscriptions": load_inscriptions().to_dict(),
            "brackets": load_brackets().to_dict(),
            "payments": load_payments().to_dict(),
            "config": load_config().to_dict()
        }
        
        # Guardar en hoja de backup
        backup_df = pd.DataFrame([{
            "backup_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "backup_type": backup_type,
            "data": json.dumps(backup_data),
            "notes": f"Backup automático - {backup_type}"
        }])
        
        existing_df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["backup"], ttl=5)
        if not existing_df.empty:
            backup_df = pd.concat([existing_df, backup_df], ignore_index=True)
        
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["backup"], data=backup_df)
        
        # Actualizar fecha de último backup en configuración
        config_df = load_config()
        config_df.loc[config_df['setting'] == 'last_backup', 'value'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_config(config_df)
        
        log_event("BACKUP_CREATED", f"Tipo: {backup_type}")
        return True
    except Exception as e:
        log_event("ERROR_BACKUP_CREATE", str(e))
        return False

# --- 14. FUNCIONES DE INSCRIPCIÓN ---
def save_participants_temporarily(participants_list, inscription_type, payment_code):
    """Guarda participantes temporalmente (antes del pago)"""
    try:
        inscriptions_df = load_inscriptions()
        group_id = generate_group_id() if inscription_type == "colectivo" else ""
        
        saved_ids = []
        for participant in participants_list:
            participant_id = generate_participant_id()
            
            new_participant = {
                "ID": participant_id,
                "Nombre_Completo": participant["nombre_completo"],
                "Edad": participant["edad"],
                "Peso": participant["peso"],
                "Estatura": participant["estatura"],
                "Grado": participant["grado"],
                "Grado_Valor": int(participant["grado"]),
                "Dojo": participant["dojo"],
                "Organizacion": participant["organizacion"],
                "Telefono": participant["telefono"],
                "Email": participant["email"],
                "Categoria": participant["categoria"],
                "Tipo_Inscripcion": inscription_type,
                "Codigo_Pago": payment_code,
                "Fecha_Inscripcion": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Foto_Base64": participant.get("foto_base64", ""),
                "Consentimiento": participant["consentimiento"],
                "Descargo": participant["descargo"],
                "Estado_Pago": "Pendiente",
                "Grupo_ID": group_id,
                "Estado": "Pre-inscrito",
                "MP_Payment_ID": "",
                "MP_Status": "",
                "MP_Date_Approved": "",
                "Last_Updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            new_row = pd.DataFrame([new_participant])
            inscriptions_df = pd.concat([inscriptions_df, new_row], ignore_index=True)
            saved_ids.append(participant_id)
        
        save_inscriptions(inscriptions_df)
        log_event("PARTICIPANTS_SAVED_TEMP", f"{len(saved_ids)} participantes guardados, código: {payment_code}")
        return saved_ids, group_id
        
    except Exception as e:
        st.error(f"Error guardando participantes: {str(e)}")
        log_event("ERROR_SAVE_PARTICIPANTS_TEMP", str(e))
        return [], ""

def confirm_inscription_manually(inscription_code):
    """Confirma una inscripción manualmente sin pasar por Mercado Pago"""
    try:
        inscriptions_df = load_inscriptions()
        mask = inscriptions_df["Codigo_Pago"] == inscription_code
        
        if not inscriptions_df[mask].empty:
            # Actualizar campos de estado
            inscriptions_df.loc[mask, "Estado_Pago"] = "Confirmado"
            inscriptions_df.loc[mask, "MP_Payment_ID"] = f"MANUAL-{uuid.uuid4().hex[:8].upper()}"
            inscriptions_df.loc[mask, "MP_Status"] = "approved"
            inscriptions_df.loc[mask, "MP_Date_Approved"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            inscriptions_df.loc[mask, "Estado"] = "Inscrito"
            
            save_inscriptions(inscriptions_df)
            
            # Enviar email de confirmación
            for _, participant in inscriptions_df[mask].iterrows():
                send_confirmation_email(participant)
            
            log_event("INSCRIPTION_CONFIRMED_MANUALLY", f"Código: {inscription_code}")
            return True
        return False
    except Exception as e:
        st.error(f"Error en confirmación manual: {str(e)}")
        log_event("ERROR_CONFIRM_INSCRIPTION_MANUALLY", str(e))
        return False

# --- 15. VISTA DE INSCRIPCIÓN CON MERCADO PAGO ---
def render_inscription_view():
    """Vista principal de inscripción con Mercado Pago"""
    render_header()
    
    # Inicializar variables de sesión
    if 'inscription_step' not in st.session_state:
        st.session_state.inscription_step = 1
    if 'inscription_type' not in st.session_state:
        st.session_state.inscription_type = "individual"
    if 'group_participants' not in st.session_state:
        st.session_state.group_participants = []
    if 'current_participant' not in st.session_state:
        st.session_state.current_participant = {}
    if 'payment_processed' not in st.session_state:
        st.session_state.payment_processed = False
    if 'payment_status' not in st.session_state:
        st.session_state.payment_status = None
    if 'payment_data' not in st.session_state:
        st.session_state.payment_data = None
    if 'inscription_code' not in st.session_state:
        st.session_state.inscription_code = None
    if 'payment_check' not in st.session_state:
        st.session_state.payment_check = None
    
    # Verificar parámetros de pago en la URL
    query_params = st.query_params
    if "payment" in query_params:
        handle_payment_callback(query_params["payment"], query_params.get("code", ""))
        return
    
    # Verificar estado de pago periódicamente
    if (st.session_state.payment_processed and 
        st.session_state.payment_status == "pending" and
        st.session_state.inscription_code):
        
        # Solo verificar cada 30 segundos
        current_time = time.time()
        if (st.session_state.payment_check is None or 
            current_time - st.session_state.payment_check > 30):
            
            status = check_payment_status_periodically(st.session_state.inscription_code)
            if status != "pending":
                st.session_state.payment_status = status
                st.session_state.payment_check = current_time
                st.rerun()
    
    st.markdown("### 📝 SISTEMA DE INSCRIPCIÓN - WKB CHILE 2024")
    
    # Verificar si las inscripciones están abiertas
    if not is_registration_open():
        st.markdown('<div class="alert-warning">⚠️ <strong>LAS INSCRIPCIONES ESTÁN CERRADAS</strong></div>', unsafe_allow_html=True)
        st.info("El periodo de inscripción ha finalizado. El torneo está en etapa de competencia.")
        if st.button("🏆 VER BRACKETS DEL TORNEO"):
            st.session_state.view = "HOME"
            st.session_state.inscription_step = 1
            st.rerun()
        return
    
    # Si ya se procesó el pago, mostrar resultado
    if st.session_state.payment_processed:
        show_payment_result()
        return
    
    # Paso 1: Selección de tipo
    if st.session_state.inscription_step == 1:
        show_inscription_type_selection()
    
    # Paso 2: Formulario de inscripción
    elif st.session_state.inscription_step == 2:
        show_inscription_form()
    
    # Paso 3: Sistema de pago con Mercado Pago
    elif st.session_state.inscription_step == 3:
        show_payment_section()

def handle_payment_callback(payment_status, inscription_code):
    """Maneja el callback de Mercado Pago"""
    log_event("PAYMENT_CALLBACK", f"Estado: {payment_status}, Código: {inscription_code}")
    
    if payment_status == "success":
        st.session_state.payment_processed = True
        st.session_state.payment_status = "success"
        st.session_state.inscription_code = inscription_code
        st.success("✅ ¡Pago procesado exitosamente!")
        
        # Procesar pago inmediatamente
        if inscription_code:
            inscriptions_df = load_inscriptions()
            mask = inscriptions_df["Codigo_Pago"] == inscription_code
            if not inscriptions_df[mask].empty:
                inscriptions_df.loc[mask, "Estado_Pago"] = "Confirmado"
                inscriptions_df.loc[mask, "Estado"] = "Inscrito"
                inscriptions_df.loc[mask, "MP_Status"] = "approved"
                inscriptions_df.loc[mask, "MP_Date_Approved"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_inscriptions(inscriptions_df)
        
    elif payment_status == "failure":
        st.session_state.payment_processed = True
        st.session_state.payment_status = "failure"
        st.session_state.inscription_code = inscription_code
        st.error("❌ El pago fue rechazado. Por favor intenta nuevamente.")
    elif payment_status == "pending":
        st.session_state.payment_processed = True
        st.session_state.payment_status = "pending"
        st.session_state.inscription_code = inscription_code
        st.session_state.payment_check = time.time()
        st.warning("⏳ El pago está pendiente. Te notificaremos cuando sea aprobado.")
    
    st.rerun()

def show_inscription_type_selection():
    """Muestra la selección de tipo de inscripción"""
    st.markdown("#### 👥 TIPO DE INSCRIPCIÓN")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("**👤 INSCRIPCIÓN INDIVIDUAL**\n\nPara un solo competidor", 
                    use_container_width=True, key="btn_individual"):
            st.session_state.inscription_type = "individual"
            st.session_state.inscription_step = 2
            st.rerun()
    
    with col2:
        if st.button("**👥 INSCRIPCIÓN GRUPAL**\n\nPara equipos (descuentos disponibles)", 
                    use_container_width=True, key="btn_colectiva"):
            st.session_state.inscription_type = "colectivo"
            st.session_state.inscription_step = 2
            st.rerun()
    
    st.markdown("---")
    st.markdown('<div class="alert-success">' + """
    **💡 INFORMACIÓN IMPORTANTE:**
    - **Pago seguro:** Utilizamos Mercado Pago para procesar tus pagos
    - **Individual:** $50.000 CLP por persona
    - **Grupal (3+ personas):** 10% descuento ($45.000 c/u)
    - **Grupal (5+ personas):** 20% descuento ($40.000 c/u)
    - **Múltiples métodos:** Tarjeta de crédito/débito, transferencia, efectivo
    - **Inscripción inmediata:** Confirmación automática al pagar
    """ + '</div>', unsafe_allow_html=True)

def show_inscription_form():
    """Muestra el formulario de inscripción"""
    if st.session_state.inscription_type == "colectivo":
        st.markdown(f"#### 👥 INSCRIPCIÓN GRUPAL - Participante {len(st.session_state.group_participants) + 1}")
    else:
        st.markdown("#### 👤 INSCRIPCIÓN INDIVIDUAL")
    
    with st.form("participant_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_completo = st.text_input("Nombre Completo *", 
                                           placeholder="Ej: Juan Pérez González")
            edad = st.number_input("Edad *", min_value=18, max_value=80, value=18)
            peso = st.number_input("Peso (kg) *", min_value=30.0, max_value=150.0, 
                                 value=70.0, step=0.1)
            estatura = st.number_input("Estatura (cm) *", min_value=100, max_value=220, 
                                     value=170)
        
        with col2:
            grado = st.selectbox("Grado *", 
                               options=list(KARATE_GRADES.keys()),
                               format_func=lambda x: f"{x} - {KARATE_GRADES[x]['name']}")
            dojo = st.text_input("Dojo/Club *", placeholder="Ej: Dojo Zen Karate")
            organizacion = st.text_input("Organización *", 
                                       placeholder="Ej: Federación Chilena de Karate")
            telefono = st.text_input("Teléfono Contacto *", placeholder="+56912345678")
            email = st.text_input("Email *", placeholder="ejemplo@email.com")
        
        # Selección de categoría
        st.markdown("#### 🏆 CATEGORÍA DE COMPETENCIA")
        categoria = st.selectbox("Selecciona tu categoría *", options=ALL_CATEGORIES)
        
        # Foto carnet (opcional)
        st.markdown("#### 📸 FOTO CARNET (Opcional)")
        uploaded_file = st.file_uploader("Sube tu foto frontal estilo carnet", 
                                       type=['jpg', 'jpeg', 'png'])
        
        foto_base64 = ""
        if uploaded_file is not None:
            try:
                image = Image.open(uploaded_file)
                if image.size[0] > 800 or image.size[1] > 800:
                    image.thumbnail((800, 800))
                foto_base64 = image_to_base64(image)
                
                with st.expander("👁️ VER PREVISUALIZACIÓN"):
                    st.image(image, width=200)
            except Exception as e:
                st.error(f"Error procesando la imagen: {str(e)}")
        
        # Documentación legal
        st.markdown("#### 📄 DOCUMENTACIÓN LEGAL")
        consentimiento = st.checkbox(
            "✅ Autorizo el tratamiento de mis datos personales para fines de participación en el torneo.",
            key="consentimiento"
        )
        
        descargo = st.checkbox(
            "✅ Eximo a los organizadores de cualquier responsabilidad por lesiones durante mi participación.",
            key="descargo"
        )
        
        col_submit1, col_submit2 = st.columns(2)
        with col_submit1:
            submit_button = st.form_submit_button("💾 GUARDAR PARTICIPANTE", 
                                                use_container_width=True)
        with col_submit2:
            cancel_button = st.form_submit_button("🔙 VOLVER", 
                                                 use_container_width=True,
                                                 type="secondary")
        
        if cancel_button:
            st.session_state.inscription_step = 1
            st.rerun()
        
        if submit_button:
            # Validaciones
            validation_errors = validate_participant_data({
                "nombre_completo": nombre_completo,
                "edad": edad,
                "peso": peso,
                "estatura": estatura,
                "telefono": telefono,
                "email": email
            })
            
            if not all([nombre_completo, dojo, organizacion, telefono, email, categoria]):
                st.error("❌ Por favor completa todos los campos obligatorios (*)")
            elif validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}")
            elif not (consentimiento and descargo):
                st.error("❌ Debes aceptar ambos documentos legales para continuar")
            else:
                participant_data = {
                    "nombre_completo": nombre_completo,
                    "edad": edad,
                    "peso": peso,
                    "estatura": estatura,
                    "grado": grado,
                    "grado_valor": int(grado),
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
                    st.session_state.current_participant = participant_data
                    st.session_state.inscription_step = 3
                    log_event("INDIVIDUAL_INSCRIPTION_STARTED", nombre_completo)
                else:
                    st.session_state.group_participants.append(participant_data)
                    st.success(f"✅ Participante agregado. Total: {len(st.session_state.group_participants)}")
                    log_event("GROUP_PARTICIPANT_ADDED", f"{nombre_completo} - Total: {len(st.session_state.group_participants)}")
                    # Limpiar el formulario automáticamente
                    st.rerun()
    
    # Mostrar lista de participantes para inscripción grupal
    if (st.session_state.inscription_type == "colectivo" and 
        len(st.session_state.group_participants) > 0):
        
        st.markdown("---")
        st.markdown("#### 📋 PARTICIPANTES AGREGADOS")
        
        for i, participant in enumerate(st.session_state.group_participants, 1):
            with st.container():
                col_info, col_action = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**{i}. {participant['nombre_completo']}** - {participant['categoria']}")
                with col_action:
                    if st.button("🗑️", key=f"remove_{i}"):
                        st.session_state.group_participants.pop(i-1)
                        log_event("GROUP_PARTICIPANT_REMOVED", f"Índice: {i}")
                        st.rerun()
        
        col_proceed1, col_proceed2, col_proceed3 = st.columns([1, 2, 1])
        with col_proceed2:
            if st.button("🚀 PROCEDER AL PAGO", type="primary", 
                       use_container_width=True):
                st.session_state.inscription_step = 3
                log_event("GROUP_INSCRIPTION_PROCEED", f"{len(st.session_state.group_participants)} participantes")
                st.rerun()




def show_payment_section():
    # Muestra la sección de pago con Mercado Pago
    st.markdown("#### 💳 PAGO CON MERCADO PAGO")
    
    # Calcular total
    if st.session_state.inscription_type == "individual":
        participants_count = 1
        participants_list = [st.session_state.current_participant]
        primary_email = st.session_state.current_participant["email"]
        description = "Individual - " + str(st.session_state.current_participant["nombre_completo"])
    else:
        participants_count = len(st.session_state.group_participants)
        participants_list = st.session_state.group_participants
        primary_email = st.session_state.group_participants[0]["email"] if participants_list else ""
        description = "Grupal - " + str(participants_count) + " participantes"
    
    total_price = calculate_price(participants_count, st.session_state.inscription_type)
    
    # Mostrar resumen usando contenedores nativos de Streamlit para evitar HTML complejo
    with st.container():
        st.info("### TOTAL A PAGAR: $" + "{:,}".format(int(total_price)).replace(",", ".") + " CLP")
        st.markdown("**Tipo de inscripción:** " + st.session_state.inscription_type.upper())
        st.markdown("**Cantidad de participantes:** " + str(participants_count))
        cod_display = st.session_state.inscription_code if st.session_state.inscription_code else "Por generar"
        st.markdown("**Código de inscripción:** " + cod_display)
    
    # Detalles de participantes
    with st.expander("📋 VER DETALLES DE PARTICIPANTES"):
        for i, p in enumerate(participants_list, 1):
            st.markdown(str(i) + ". " + str(p['nombre_completo']) + " - " + str(p['categoria']))
    
    # Generación de código si no existe
    if not st.session_state.inscription_code:
        st.session_state.inscription_code = generate_inscription_code()
        saved_ids, group_id = save_participants_temporarily(
            participants_list,
            st.session_state.inscription_type,
            st.session_state.inscription_code
        )
        if not saved_ids:
            st.error("❌ Error al guardar la inscripción.")
            return
    
    # Crear preferencia de pago
    with st.spinner("🔄 Preparando pago seguro..."):
        preference = create_mercadopago_preference(
            total_amount=total_price,
            description=description,
            participant_email=primary_email,
            inscription_id=st.session_state.inscription_code
        )
    
    if preference and "init_point" in preference:
        payment_url = preference["init_point"]
        
        # Construcción del botón de pago (Concatenación de strings simples)
        html_btn = '<div style="text-align: center; margin: 30px 0;">'
        html_btn += '<a href="' + str(payment_url) + '" target="_blank" style="text-decoration: none;">'
        html_btn += '<button style="background: linear-gradient(135deg, #00B1EA, #009EE3); color: white; '
        html_btn += 'border: none; padding: 20px 40px; font-size: 18px; font-weight: bold; '
        html_btn += 'border-radius: 10px; cursor: pointer; width: 100%; max-width: 400px;">'
        html_btn += '💳 PAGAR CON MERCADO PAGO'
        html_btn += '</button></a></div>'
        
        st.markdown(html_btn, unsafe_allow_html=True)
        
        # QR Code
        st.markdown("---")
        st.markdown("#### 📱 PAGO CON CÓDIGO QR")
        qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" + str(payment_url)
        st.image(qr_url, caption="Escanea para pagar", width=200)
        
        # Instrucciones finales
        st.success("### 💡 Instrucciones:\n1. Haz clic en el botón o escanea el QR.\n2. Completa el pago en Mercado Pago.\n3. Recibirás un correo de confirmación.")
        st.code("ID de seguimiento: " + str(st.session_state.inscription_code))
        
    else:
        st.error("❌ Error al crear el pago. Por favor, intenta nuevamente.")
    
    # Botones de navegación
    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🔙 VOLVER A MODIFICAR", use_container_width=True):
            st.session_state.inscription_step = 2
            st.rerun()
    with col_nav2:
        if st.button("🏠 CANCELAR", use_container_width=True):
            st.session_state.view = "HOME"
            st.session_state.inscription_step = 1
            st.rerun()
    
    # Opciones de Desarrollador
    st.markdown("---")
    with st.expander("🛠️ DESARROLLADOR"):
        if st.button("✅ CONFIRMAR MANUALMENTE", use_container_width=True):
            if confirm_inscription_manually(st.session_state.inscription_code):
                st.session_state.payment_processed = True
                st.session_state.payment_status = "success"
                st.rerun()




def show_payment_result():
    """Muestra el resultado del pago"""
    if st.session_state.payment_status == "success":
        show_payment_success()
    elif st.session_state.payment_status == "failure":
        show_payment_failure()
    elif st.session_state.payment_status == "pending":
        show_payment_pending()

def show_payment_success():
    """Muestra pantalla de pago exitoso"""
    render_header()
    
    # Confeti de celebración
    st.balloons()
    
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 80px; color: #10B981; margin-bottom: 20px; animation: bounce 1s infinite alternate;">✅</div>
        <h1 style="color: #10B981;">¡PAGO EXITOSO!</h1>
        <p style="font-size: 20px; color: #9ca3af;">Tu inscripción ha sido confirmada con éxito</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Información de la inscripción
    st.markdown("---")
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">CÓDIGO DE INSCRIPCIÓN</div>
            <div class="stat-value" style="font-size: 24px;">{st.session_state.inscription_code}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_info2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">ESTADO DE PAGO</div>
            <div class="stat-value" style="color: #10B981; font-size: 24px;">CONFIRMADO ✓</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Próximos pasos
    st.markdown("---")
    st.markdown("### 📧 PRÓXIMOS PASOS")
    st.markdown("""
    <div class="alert-success">
        - **📧 Recibirás un correo** de confirmación con todos los detalles
        - **📱 Guarda tu código de inscripción** para cualquier consulta
        - **📅 Revisa las fechas y horarios** del torneo en nuestro sitio web
        - **🥋 ¡Prepárate para competir y dar lo mejor!**
    </div>
    """, unsafe_allow_html=True)
    
    # Botón de retorno
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 VOLVER AL INICIO", type="primary", use_container_width=True):
            # Resetear estado de inscripción para una nueva
            st.session_state.inscription_step = 1
            st.session_state.current_participant = {}
            st.session_state.group_participants = []
            st.session_state.payment_processed = False
            st.session_state.payment_status = None
            st.session_state.inscription_code = None
            st.session_state.payment_check = None
            st.session_state.view = "HOME"
            st.rerun()

def show_payment_failure():
    """Muestra pantalla de pago fallido"""
    render_header()
    
    st.markdown("""
    <div style='text-align: center; padding: 50px 20px;'>
        <div style='font-size: 80px; color: #EF4444; margin-bottom: 20px;'>❌</div>
        <h1 style="color: #EF4444;">PAGO RECHAZADO</h1>
        <p style='font-size: 20px; color: #9ca3af;'>No pudimos procesar tu pago</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='background: rgba(239, 68, 68, 0.1); padding: 30px; border-radius: 15px; margin: 30px 0; border: 2px solid #EF4444;'>
        <h4 style='color: #FDB931; text-align: center;'>¿QUÉ PUEDES HACER?</h4>
        
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;'>
            <div style='background: rgba(31, 41, 55, 0.5); padding: 15px; border-radius: 10px;'>
                <h5 style='color: #FDB931;'>🔄 INTENTAR NUEVAMENTE</h5>
                <p style='color: #e5e7eb;'>Verifica los datos de tu tarjeta y vuelve a intentar</p>
            </div>
            
            <div style='background: rgba(31, 41, 55, 0.5); padding: 15px; border-radius: 10px;'>
                <h5 style='color: #FDB931;'>💳 USAR OTRO MÉTODO</h5>
                <p style='color: #e5e7eb;'>Prueba con otra tarjeta o método de pago</p>
            </div>
            
            <div style='background: rgba(31, 41, 55, 0.5); padding: 15px; border-radius: 10px;'>
                <h5 style='color: #FDB931;'>📞 CONTACTAR SOPORTE</h5>
                <p style='color: #e5e7eb;'>Si el problema persiste, contáctanos</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones de acción
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 REINTENTAR PAGO", use_container_width=True):
            st.session_state.payment_processed = False
            st.session_state.payment_status = None
            st.rerun()
    
    with col2:
        if st.button("📝 VOLVER A INSCRIPCIÓN", use_container_width=True, type="secondary"):
            st.session_state.inscription_step = 2
            st.session_state.payment_processed = False
            st.session_state.payment_status = None
            st.rerun()
    
    with col3:
        if st.button("🏠 VOLVER AL INICIO", use_container_width=True, type="secondary"):
            st.session_state.view = "HOME"
            st.session_state.inscription_step = 1
            st.session_state.current_participant = {}
            st.session_state.group_participants = []
            st.session_state.payment_processed = False
            st.session_state.payment_status = None
            st.session_state.inscription_code = None
            st.session_state.payment_check = None
            st.rerun()

def show_payment_pending():
    """Muestra pantalla de pago pendiente"""
    render_header()
    
    st.markdown("""
    <div style='text-align: center; padding: 50px 20px;'>
        <div style='font-size: 80px; color: #F59E0B; margin-bottom: 20px;'>⏳</div>
        <h1 style="color: #F59E0B;">PAGO PENDIENTE</h1>
        <p style='font-size: 20px; color: #9ca3af;'>Estamos procesando tu pago</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="payment-status status-pending">
        <h4 style='color: #F59E0B;'>🔄 PAGO EN PROCESO</h4>
        <p>Tu inscripción será confirmada automáticamente una vez que el pago sea aprobado.</p>
        <p><strong>Código de inscripción:</strong> <code>{st.session_state.inscription_code}</code></p>
        <p><strong>Fecha:</strong> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert-warning">
        **📧 RECIBIRÁS UNA NOTIFICACIÓN**
        - Te enviaremos un correo cuando el pago sea aprobado
        - Si el pago no se completa en 24 horas, será cancelado automáticamente
        - Puedes reintentar el pago en cualquier momento
        - El estado se actualizará automáticamente en esta página
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar estado automáticamente
    if st.session_state.inscription_code:
        status = check_payment_status_periodically(st.session_state.inscription_code)
        if status != "pending":
            st.session_state.payment_status = status
            st.rerun()
    
    # Botones de acción
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 VERIFICAR ESTADO", use_container_width=True):
            if st.session_state.inscription_code:
                status = check_payment_status_periodically(st.session_state.inscription_code)
                if status != "pending":
                    st.session_state.payment_status = status
                    st.rerun()
                else:
                    st.info("El pago aún está pendiente. Por favor, espera la confirmación.")
    
    with col2:
        if st.button("🏠 VOLVER AL INICIO", use_container_width=True, type="secondary"):
            st.session_state.view = "HOME"
            st.session_state.inscription_step = 1
            st.session_state.current_participant = {}
            st.session_state.group_participants = []
            st.session_state.payment_processed = False
            st.session_state.payment_status = None
            st.session_state.inscription_code = None
            st.session_state.payment_check = None
            st.rerun()

# --- 16. FUNCIONES DE BRACKETS ---



def generate_dynamic_brackets_for_category(category):
    """Genera brackets dinámicos según la cantidad de participantes"""
    try:
        brackets_df = load_brackets()
        inscriptions_df = load_inscriptions()
        
        if inscriptions_df.empty:
            st.warning(f"No hay inscritos en {category}")
            return False
        
        category_inscriptions = inscriptions_df[
            (inscriptions_df['Categoria'] == category) & 
            (inscriptions_df['Estado_Pago'] == 'Confirmado')
        ]
        
        participants = category_inscriptions.to_dict('records')
        num_participants = len(participants)
        
        if num_participants < 2:
            st.warning(f"No hay suficientes inscritos confirmados en {category} (mínimo 2)")
            return False
        
        random.shuffle(participants)
        
        # CALCULAR ESTRUCTURA DEL BRACKET
        bracket_structure = calculate_bracket_structure(num_participants)
        
        # Limpiar brackets existentes para esta categoría
        brackets_df = brackets_df[brackets_df['Category'] != category]
        
        all_brackets = []
        
        # Generar todas las rondas
        for round_num, round_info in enumerate(bracket_structure['rounds']):
            round_name = round_info['name']
            num_matches = round_info['matches']
            next_round_matches = bracket_structure['rounds'][round_num + 1]['matches'] if round_num + 1 < len(bracket_structure['rounds']) else 1
            
            for match_num in range(1, num_matches + 1):
                match_id = f"{round_info['prefix']}{match_num}"
                
                bracket_entry = {
                    "Category": category,
                    "Match_ID": match_id,
                    "Round": round_name,
                    "Match_Number": match_num,
                    "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
                    "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
                    "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending",
                    "Total_Votes": 0, "Vote_History": "[]", "Last_Vote_Time": "",
                    "Next_Match": f"{bracket_structure['rounds'][round_num + 1]['prefix']}{((match_num + 1) // 2)}" if round_num + 1 < len(bracket_structure['rounds']) else "",
                    "Next_Position": "top" if match_num % 2 == 1 else "bottom" if round_num + 1 < len(bracket_structure['rounds']) else ""
                }
                
                all_brackets.append(bracket_entry)
        
        # Agregar entrada para el campeón
        all_brackets.append({
            "Category": category,
            "Match_ID": "CHAMPION",
            "Round": "Champion",
            "Match_Number": 1,
            "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
            "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
            "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending",
            "Total_Votes": 0, "Vote_History": "[]", "Last_Vote_Time": "",
            "Next_Match": "", "Next_Position": ""
        })
        
        # Convertir a DataFrame
        new_brackets_df = pd.DataFrame(all_brackets)
        brackets_df = pd.concat([brackets_df, new_brackets_df], ignore_index=True)
        
        # Asignar participantes a la primera ronda
        assign_participants_to_first_round(brackets_df, category, participants)
        
        save_brackets(brackets_df)
        
        # Actualizar estado de inscripciones
        for participant in participants:
            inscriptions_df.loc[inscriptions_df['ID'] == participant['ID'], 'Estado'] = 'Emparejado'
        
        save_inscriptions(inscriptions_df)
        
        log_event("DYNAMIC_BRACKETS_GENERATED", 
                 f"Categoría: {category}, Participantes: {num_participants}, "
                 f"Rondas: {len(bracket_structure['rounds'])}, "
                 f"Byes: {bracket_structure['byes']}")
        
        return True
        
    except Exception as e:
        st.error(f"Error generando brackets dinámicos: {str(e)}")
        log_event("ERROR_GENERATE_DYNAMIC_BRACKETS", str(e))
        return False






def calculate_bracket_structure(num_participants):
    """Calcula la estructura del bracket según el número de participantes"""
    
    # Encontrar la potencia de 2 más cercana (hacia arriba)
    next_power_of_two = 1
    while next_power_of_two < num_participants:
        next_power_of_two *= 2
    
    # Calcular byes (participantes que pasan directo a segunda ronda)
    byes = next_power_of_two - num_participants
    
    # Calcular número de rondas
    num_rounds = int(math.log2(next_power_of_two))
    
    rounds = []
    match_prefixes = ["R64", "R32", "R16", "QF", "SF", "F"]  # Round of 64, 32, 16, Quarter, Semi, Final
    
    # Determinar en qué ronda comienza
    start_round = 0
    current_matches = next_power_of_two // 2
    
    while current_matches > num_participants - byes:
        start_round += 1
        current_matches //= 2
    
    # Crear estructura de rondas
    match_count = next_power_of_two // 2
    for i in range(num_rounds):
        if i >= start_round:
            if i - start_round < len(match_prefixes):
                prefix = match_prefixes[i - start_round]
            else:
                prefix = f"R{i+1}"
            
            round_name = get_round_name(i - start_round, match_count)
            rounds.append({
                "name": round_name,
                "matches": match_count,
                "prefix": prefix,
                "round_num": i - start_round
            })
        
        match_count //= 2
        if match_count < 1:
            match_count = 1
    
    return {
        "participants": num_participants,
        "total_slots": next_power_of_two,
        "byes": byes,
        "rounds": rounds,
        "total_rounds": len(rounds)
    }

def get_round_name(round_num, match_count):
    """Devuelve el nombre de la ronda según el número"""
    round_names = {
        0: "First Round",
        1: "Second Round",
        2: "Round of 16",
        3: "Quarterfinals",
        4: "Semifinals",
        5: "Finals"
    }
    
    if round_num in round_names:
        return round_names[round_num]
    elif match_count == 4:
        return "Quarterfinals"
    elif match_count == 2:
        return "Semifinals"
    elif match_count == 1:
        return "Finals"
    else:
        return f"Round {round_num + 1}"

def assign_participants_to_first_round(brackets_df, category, participants):
    """Asigna participantes a la primera ronda del bracket"""
    
    # Obtener la primera ronda
    category_brackets = brackets_df[brackets_df['Category'] == category]
    first_round = category_brackets[category_brackets['Round'] == 'First Round']
    
    if first_round.empty:
        # Si no hay "First Round", buscar la primera ronda disponible
        round_order = ["First Round", "Second Round", "Round of 16", "Quarterfinals", "Semifinals", "Finals"]
        for round_name in round_order:
            first_round = category_brackets[category_brackets['Round'] == round_name]
            if not first_round.empty:
                break
    
    num_matches = len(first_round)
    num_participants = len(participants)
    
    # Calcular byes
    next_power_of_two = 1
    while next_power_of_two < num_participants:
        next_power_of_two *= 2
    byes = next_power_of_two - num_participants
    
    # Asignar participantes
    participant_index = 0
    bye_count = 0
    
    for match_idx, (_, match_row) in enumerate(first_round.iterrows()):
        match_id = match_row['Match_ID']
        
        # Determinar si este match tiene bye
        has_bye = bye_count < byes
        
        if has_bye:
            # Bye: un participante pasa directo
            if participant_index < num_participants:
                p1 = participants[participant_index]
                
                brackets_df.loc[(brackets_df['Category'] == category) & 
                               (brackets_df['Match_ID'] == match_id),
                               ['P1_Name', 'P1_ID', 'P1_Dojo', 'Winner', 'Winner_ID', 'Status']] = [
                    p1['Nombre_Completo'], p1['ID'], p1['Dojo'],
                    p1['Nombre_Completo'], p1['ID'], 'Walkover'
                ]
                
                participant_index += 1
                bye_count += 1
        else:
            # Match normal: dos participantes
            if participant_index + 1 < num_participants:
                p1 = participants[participant_index]
                p2 = participants[participant_index + 1]
                
                brackets_df.loc[(brackets_df['Category'] == category) & 
                               (brackets_df['Match_ID'] == match_id),
                               ['P1_Name', 'P1_ID', 'P1_Dojo', 
                                'P2_Name', 'P2_ID', 'P2_Dojo', 'Status']] = [
                    p1['Nombre_Completo'], p1['ID'], p1['Dojo'],
                    p2['Nombre_Completo'], p2['ID'], p2['Dojo'], 'Scheduled'
                ]
                
                participant_index += 2
            elif participant_index < num_participants:
                # Último participante sin pareja (bye automático)
                p1 = participants[participant_index]
                
                brackets_df.loc[(brackets_df['Category'] == category) & 
                               (brackets_df['Match_ID'] == match_id),
                               ['P1_Name', 'P1_ID', 'P1_Dojo', 'Winner', 'Winner_ID', 'Status']] = [
                    p1['Nombre_Completo'], p1['ID'], p1['Dojo'],
                    p1['Nombre_Completo'], p1['ID'], 'Walkover'
                ]
                
                participant_index += 1
    
    return brackets_df














def close_registration_and_generate_brackets():
    """Cierra las inscripciones y genera brackets dinámicos"""
    try:
        if not set_registration_status(False):
            return False
        
        brackets_created = 0
        for category in ALL_CATEGORIES:
            if generate_dynamic_brackets_for_category(category):
                brackets_created += 1
        
        if brackets_created > 0:
            set_tournament_stage('competition')
            create_backup("pre_competition")
            
            st.success(f"✅ Se generaron brackets dinámicos para {brackets_created} categorías!")
            log_event("REGISTRATION_CLOSED_DYNAMIC", 
                     f"Brackets generados: {brackets_created}, "
                     f"Etapa: competencia")
            return True
        return False
    except Exception as e:
        st.error(f"Error cerrando inscripciones: {str(e)}")
        log_event("ERROR_CLOSE_REGISTRATION_DYNAMIC", str(e))
        return False





# --- 17. VISTA DE BRACKETS PROFESIONALES ---








# Versión de prueba mínima
def render_dynamic_bracket_view():
    """Renderiza brackets dinámicos según la cantidad de participantes"""
    cat = st.session_state.cat
    st.markdown(f"### 🏆 COMPETENCIA: {cat}")
    
    brackets_df = load_brackets()
    if brackets_df.empty:
        st.info("Los brackets se están generando. Por favor espera.")
        return

    cat_df = brackets_df[brackets_df['Category'] == cat]
    
    if cat_df.empty:
        st.warning(f"No hay brackets generados para {cat} aún.")
        return
    
    # Obtener estructura del bracket
    structure = analyze_bracket_structure(cat_df)
    
    # Mostrar información del bracket
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Participantes", structure['participants'])
    with col2:
        st.metric("Rondas", structure['total_rounds'])
    with col3:
        st.metric("Partidos", len(cat_df[cat_df['Round'] != 'Champion']))
    with col4:
        st.metric("Byes", structure['byes'])
    
    # Renderizar el bracket
    render_bracket_visualization(cat_df, structure)
    
    # Sistema de votación
    render_voting_system(cat_df)
    
    st.markdown("---")
    if st.button("🏠 VOLVER AL INICIO", use_container_width=True):
        st.session_state.view = "HOME"
        st.rerun()



    # Si esto funciona, el problema está en tu HTML generado





def analyze_bracket_structure(cat_df):
    """Analiza la estructura del bracket"""
    participants = set()
    rounds = []
    
    for _, match in cat_df.iterrows():
        if match['P1_ID'] and match['P1_ID'] != 'nan':
            participants.add(match['P1_ID'])
        if match['P2_ID'] and match['P2_ID'] != 'nan':
            participants.add(match['P2_ID'])
        
        if match['Round'] not in rounds and match['Round'] != 'Champion':
            rounds.append(match['Round'])
    
    # Ordenar rondas por progresión
    round_order = ["First Round", "Second Round", "Round of 16", "Quarterfinals", "Semifinals", "Finals"]
    rounds_sorted = [r for r in round_order if r in rounds]
    
    # Calcular byes (matches con walkover en primera ronda)
    first_round = cat_df[cat_df['Round'] == rounds_sorted[0]] if rounds_sorted else pd.DataFrame()
    byes = len(first_round[first_round['Status'] == 'Walkover']) if not first_round.empty else 0
    
    return {
        'participants': len(participants),
        'rounds': rounds_sorted,
        'total_rounds': len(rounds_sorted),
        'byes': byes
    }

def render_bracket_visualization(cat_df, structure):
    """Renderiza la visualización del bracket"""
    
    # Crear contenedor principal
    bracket_html = '<div class="bracket-wrapper">'
    
    # Renderizar cada ronda
    for round_name in structure['rounds']:
        round_matches = cat_df[cat_df['Round'] == round_name].sort_values('Match_Number')
        
        bracket_html += f'<div class="bracket-round">'
        bracket_html += f'<div class="round-header">{round_name.upper()}</div>'
        
        for _, match in round_matches.iterrows():
            bracket_html += '<div class="bracket-match">'
            
            # Jugador 1
            p1_name = "BYE" if match['Status'] == 'Walkover' and not match['P2_Name'] else (str(match['P1_Name']) if not pd.isna(match['P1_Name']) else "TBD")
            p1_dojo = str(match['P1_Dojo']) if not pd.isna(match['P1_Dojo']) else "---"
            p1_class = "winner" if match['Winner_ID'] == match['P1_ID'] else ""
            
            bracket_html += f'''
            <div class="bracket-player top {p1_class}">
                <span class="player-name">{p1_name}</span>
                <span class="player-dojo">{p1_dojo}</span>
            </div>
            '''
            
            # Jugador 2 (si existe)
            if not pd.isna(match['P2_Name']) and match['P2_Name'] != 'nan':
                p2_name = str(match['P2_Name'])
                p2_dojo = str(match['P2_Dojo']) if not pd.isna(match['P2_Dojo']) else "---"
                p2_class = "winner" if match['Winner_ID'] == match['P2_ID'] else ""
                
                bracket_html += f'''
                <div class="bracket-player bottom {p2_class}">
                    <span class="player-name">{p2_name}</span>
                    <span class="player-dojo">{p2_dojo}</span>
                </div>
                '''
            elif match['Status'] != 'Walkover':
                # Espacio para jugador pendiente
                bracket_html += f'''
                <div class="bracket-player bottom">
                    <span class="player-name">TBD</span>
                    <span class="player-dojo">---</span>
                </div>
                '''
            
            bracket_html += '</div>'
        
        bracket_html += '</div>'
    
    # Mostrar campeón
    champion_match = cat_df[cat_df['Round'] == 'Champion']
    if not champion_match.empty and not pd.isna(champion_match.iloc[0]['Winner']):
        champ = champion_match.iloc[0]
        bracket_html += f'''
        <div class="bracket-round">
            <div style="margin-top:40px; text-align:center;">
                <div class="round-header">🏆 CAMPEÓN</div>
                <div class="champion-box">
                    {champ["Winner"]}
                    <div class="champion-dojo">{champ.get('P1_Dojo', '') or champ.get('P2_Dojo', '')}</div>
                </div>
            </div>
        </div>
        '''
    
    bracket_html += '</div>'
    
    # Renderizar HTML
    st.markdown(bracket_html, unsafe_allow_html=True)

def render_voting_system(cat_df):
    """Renderiza el sistema de votación"""
    if get_tournament_stage() == "competition":
        st.markdown("---")
        st.markdown("#### 🗳️ SISTEMA DE VOTACIÓN")
        
        active_matches = cat_df[cat_df['Status'] == 'Live']
        if not active_matches.empty:
            st.info(f"Hay {len(active_matches)} partido(s) activo(s) para votar")
            
            for _, match in active_matches.iterrows():
                with st.container():
                    st.markdown(f"**{match['Round']} - Partido {match['Match_Number']}**")
                    
                    col1, col2, col3 = st.columns([2, 1, 2])
                    with col1:
                        p1_name = str(match['P1_Name']) if not pd.isna(match['P1_Name']) else "TBD"
                        p1_dojo = str(match['P1_Dojo']) if not pd.isna(match['P1_Dojo']) else "---"
                        st.markdown(f"**{p1_name}**")
                        st.caption(p1_dojo)
                        
                        if st.button(f"Votar por {p1_name[:15]}...", 
                                   key=f"vote_p1_{match['Match_ID']}",
                                   use_container_width=True):
                            register_vote(match['Match_ID'], match['P1_ID'])
                    
                    with col2:
                        st.markdown("**VS**", help="Partido en vivo")
                        st.metric("", f"{int(match['P1_Votes'])} - {int(match['P2_Votes'])}")
                    
                    with col3:
                        if not pd.isna(match['P2_Name']):
                            p2_name = str(match['P2_Name'])
                            p2_dojo = str(match['P2_Dojo']) if not pd.isna(match['P2_Dojo']) else "---"
                            st.markdown(f"**{p2_name}**")
                            st.caption(p2_dojo)
                            
                            if st.button(f"Votar por {p2_name[:15]}...", 
                                       key=f"vote_p2_{match['Match_ID']}",
                                       use_container_width=True):
                                register_vote(match['Match_ID'], match['P2_ID'])
                    
                    st.markdown("---")
        else:
            st.info("No hay partidos activos para votar en este momento.")

def register_vote(match_id, player_id):
    """Registra un voto para un jugador"""
    try:
        brackets_df = load_brackets()
        match_mask = brackets_df['Match_ID'] == match_id
        
        if not brackets_df[match_mask].empty:
            match = brackets_df[match_mask].iloc[0]
            
            if player_id == match['P1_ID']:
                brackets_df.loc[match_mask, 'P1_Votes'] = match['P1_Votes'] + 1
            elif player_id == match['P2_ID']:
                brackets_df.loc[match_mask, 'P2_Votes'] = match['P2_Votes'] + 1
            
            brackets_df.loc[match_mask, 'Total_Votes'] = match['Total_Votes'] + 1
            brackets_df.loc[match_mask, 'Last_Vote_Time'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Actualizar historial de votos
            vote_history = json.loads(match['Vote_History']) if match['Vote_History'] else []
            vote_history.append({
                "player_id": player_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "match_id": match_id
            })
            brackets_df.loc[match_mask, 'Vote_History'] = json.dumps(vote_history)
            
            save_brackets(brackets_df)
            
            # Verificar si hay ganador
            check_and_update_winner(match_id)
            
            st.success("✅ Voto registrado exitosamente!")
            st.rerun()
            
    except Exception as e:
        st.error(f"Error registrando voto: {str(e)}")
        log_event("ERROR_REGISTER_VOTE", str(e))

def check_and_update_winner(match_id):
    """Verifica y actualiza el ganador de un match"""
    try:
        brackets_df = load_brackets()
        match_mask = brackets_df['Match_ID'] == match_id
        
        if not brackets_df[match_mask].empty:
            match = brackets_df[match_mask].iloc[0]
            
            # Solo actualizar si el match está en vivo y ambos jugadores tienen votos
            if match['Status'] == 'Live' and match['P1_Votes'] + match['P2_Votes'] > 0:
                # Determinar ganador (más votos)
                if match['P1_Votes'] > match['P2_Votes']:
                    winner_id = match['P1_ID']
                    winner_name = match['P1_Name']
                elif match['P2_Votes'] > match['P1_Votes']:
                    winner_id = match['P2_ID']
                    winner_name = match['P2_Name']
                else:
                    # Empate - no hay ganador aún
                    return
                
                # Actualizar match
                brackets_df.loc[match_mask, 'Winner_ID'] = winner_id
                brackets_df.loc[match_mask, 'Winner'] = winner_name
                brackets_df.loc[match_mask, 'Status'] = 'Completed'
                brackets_df.loc[match_mask, 'Live'] = False
                
                # Avanzar ganador al siguiente match
                if match['Next_Match'] and winner_id:
                    next_match_mask = (brackets_df['Match_ID'] == match['Next_Match']) & (brackets_df['Category'] == match['Category'])
                    
                    if not brackets_df[next_match_mask].empty:
                        next_match = brackets_df[next_match_mask].iloc[0]
                        
                        if match['Next_Position'] == 'top':
                            brackets_df.loc[next_match_mask, 'P1_ID'] = winner_id
                            brackets_df.loc[next_match_mask, 'P1_Name'] = winner_name
                            brackets_df.loc[next_match_mask, 'P1_Dojo'] = match['P1_Dojo'] if winner_id == match['P1_ID'] else match['P2_Dojo']
                        else:
                            brackets_df.loc[next_match_mask, 'P2_ID'] = winner_id
                            brackets_df.loc[next_match_mask, 'P2_Name'] = winner_name
                            brackets_df.loc[next_match_mask, 'P2_Dojo'] = match['P1_Dojo'] if winner_id == match['P1_ID'] else match['P2_Dojo']
                        
                        # Si ambos jugadores están asignados, activar el match
                        if (not pd.isna(brackets_df.loc[next_match_mask, 'P1_ID'].iloc[0]) and 
                            not pd.isna(brackets_df.loc[next_match_mask, 'P2_ID'].iloc[0])):
                            brackets_df.loc[next_match_mask, 'Status'] = 'Live'
                            brackets_df.loc[next_match_mask, 'Live'] = True
                
                save_brackets(brackets_df)
                
                log_event("MATCH_COMPLETED", 
                         f"Match: {match_id}, Ganador: {winner_name}, "
                         f"Votos: {match['P1_Votes']}-{match['P2_Votes']}")
                
    except Exception as e:
        log_event("ERROR_CHECK_WINNER", str(e))






    with tab1:
        st.markdown("### 📂 SELECCIONA TU CATEGORÍA")
        
        # Mostrar categorías con información de inscritos
        inscriptions_df = load_inscriptions()
        
        for group, subcategories in CATEGORIES_CONFIG.items():
            st.markdown(f"#### {group}")
            cols = st.columns(len(subcategories))
            
            for idx, subcat in enumerate(subcategories):
                full_cat = f"{group} | {subcat}"
                
                # Contar inscritos confirmados en esta categoría
                cat_inscriptions = inscriptions_df[
                    (inscriptions_df['Categoria'] == full_cat) & 
                    (inscriptions_df['Estado_Pago'] == 'Confirmado')
                ]
                num_inscritos = len(cat_inscriptions)
                
                with cols[idx]:
                    button_text = f"{subcat}\n\n"
                    button_text += f"📊 {num_inscritos} inscrito{'s' if num_inscritos != 1 else ''}"
                    
                    if st.button(button_text, key=f"cat_{full_cat}", use_container_width=True):
                        st.session_state.view = "BRACKET"
                        st.session_state.cat = full_cat
                        st.rerun()
    
    with tab2:
        if tournament_stage == "competition":
            st.warning("⚠️ Las inscripciones están cerradas. El torneo está en etapa de competencia.")
            if st.button("🏆 VER BRACKETS", type="primary", use_container_width=True):
                st.session_state.view = "BRACKET"
                st.session_state.cat = ALL_CATEGORIES[0] if ALL_CATEGORIES else ""
                st.rerun()
        else:
            if st.button("📝 COMENZAR INSCRIPCIÓN", type="primary", use_container_width=True):
                st.session_state.view = "INSCRIPTION"
                st.rerun()
    
    with tab3:
        inscriptions_df = load_inscriptions()
        if not inscriptions_df.empty and 'Nombre_Completo' in inscriptions_df.columns:
            # Filtros
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filter_category = st.selectbox("Filtrar por categoría", ["Todas"] + list(inscriptions_df['Categoria'].unique()))
            with col_filter2:
                filter_status = st.selectbox("Filtrar por estado", ["Todos", "Confirmado", "Pendiente"])
            
            # Aplicar filtros
            filtered_df = inscriptions_df.copy()
            if filter_category != "Todas":
                filtered_df = filtered_df[filtered_df['Categoria'] == filter_category]
            if filter_status != "Todos":
                if filter_status == "Confirmado":
                    filtered_df = filtered_df[filtered_df['Estado_Pago'] == 'Confirmado']
                else:
                    filtered_df = filtered_df[filtered_df['Estado_Pago'] != 'Confirmado']
            
            st.dataframe(
                filtered_df[['Nombre_Completo', 'Categoria', 'Dojo', 'Estado_Pago', 'Fecha_Inscripcion']],
                column_config={
                    "Nombre_Completo": "Nombre",
                    "Categoria": "Categoría",
                    "Dojo": "Dojo",
                    "Estado_Pago": "Estado Pago",
                    "Fecha_Inscripcion": "Fecha Inscripción"
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Botón para descargar datos
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 DESCARGAR DATOS",
                data=csv,
                file_name=f"inscripciones_wkb_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No hay inscripciones registradas aún.")
    
    with tab4:
        # Sistema de login admin
        if not st.session_state.get('is_admin', False):
            st.markdown("#### 🔒 ACCESO ADMINISTRADOR")
            admin_pass = st.text_input("Contraseña Admin", type="password")
            
            if st.button("🔓 INGRESAR", type="primary", use_container_width=True):
                if check_admin(admin_pass):
                    st.session_state.is_admin = True
                    st.success("✅ Acceso concedido")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
        else:
            st.success("✅ SESIÓN ADMIN ACTIVA")
            
            if st.button("🚪 CERRAR SESIÓN", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
            
            st.markdown("---")
            st.markdown("#### ⚙️ CONFIGURACIÓN DEL TORNEO")
            
            # Estado actual
            current_stage = get_tournament_stage()
            reg_open = is_registration_open()
            
            col_stage1, col_stage2 = st.columns(2)
            with col_stage1:
                st.metric("Etapa Actual", "Inscripción" if current_stage == "inscription" else "Competencia")
            with col_stage2:
                st.metric("Inscripciones", "Abiertas" if reg_open else "Cerradas")
            
            # Acciones admin
            st.markdown("#### 🎯 ACCIONES RÁPIDAS")
            
            col_action1, col_action2 = st.columns(2)
            with col_action1:
                if current_stage == "inscription":
                    if st.button("🚀 CERRAR INSCRIPCIONES", type="primary", use_container_width=True):
                        with st.spinner("Cerrando inscripciones y generando brackets..."):
                            if close_registration_and_generate_brackets():
                                st.success("✅ Inscripciones cerradas y brackets generados!")
                                time.sleep(2)
                                st.rerun()
                else:
                    if st.button("📝 REABRIR INSCRIPCIONES", use_container_width=True):
                        set_tournament_stage('inscription')
                        set_registration_status(True)
                        st.success("✅ Inscripciones reabiertas!")
                        time.sleep(2)
                        st.rerun()
            
            with col_action2:
                if st.button("💾 CREAR BACKUP", use_container_width=True):
                    with st.spinner("Creando backup..."):
                        if create_backup("manual"):
                            st.success("✅ Backup creado exitosamente!")
            
            # Sistema de reset
            st.markdown("---")
            st.markdown("#### ⚠️ SISTEMA DE RESET")
            
            if st.button("🔄 RESETEAR TODO EL SISTEMA", type="secondary", use_container_width=True):
                with st.expander("Confirmar reset completo"):
                    confirm = st.checkbox("Confirmo que quiero borrar TODOS los datos")
                    if confirm:
                        if st.button("✅ CONFIRMAR RESET COMPLETO", type="primary"):
                            if initialize_sheets():
                                st.success("✅ Sistema reseteado exitosamente")
                                time.sleep(2)
                                st.rerun()

# --- 19. GESTIÓN PRINCIPAL DE LA APLICACIÓN ---
def main():
    """Función principal de la aplicación"""
    
    # Inicializar variables de sesión
    if 'view' not in st.session_state:
        st.session_state.view = "HOME"
    if 'cat' not in st.session_state:
        st.session_state.cat = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    
    # Verificar e inicializar configuración
    try:
        config_df = load_config()
        if config_df.empty:
            with st.spinner("Inicializando sistema..."):
                initialize_sheets()
    except Exception as e:
        log_event("ERROR_INITIAL_CHECK", str(e))
        with st.spinner("Inicializando sistema por primera vez..."):
            initialize_sheets()
    
    # Navegación entre vistas
    if st.session_state.view == "HOME":
        render_home_view()
    elif st.session_state.view == "INSCRIPTION":
        render_inscription_view()
    elif st.session_state.view == "BRACKET":
        render_dynamic_bracket_view()  # <-- USAR LA NUEVA FUNCIÓN

# --- 20. EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Error crítico en la aplicación: {str(e)}")
        log_event("CRITICAL_ERROR", str(e))
        st.info("""
        **🛠️ Solución de problemas:**
        1. Recarga la página
        2. Verifica tu conexión a internet
        3. Si el problema persiste, contacta al administrador
        
        **📧 Contacto:** admin@wkbchile.cl
        """)
        
        # Opción para resetear la aplicación
        if st.button("🔄 REINICIAR APLICACIÓN", type="primary"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()
