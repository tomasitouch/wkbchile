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

# --- 2. CONFIGURACIÓN DE HOJAS GOOGLE SHEETS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

# Nombres de las hojas requeridas
SHEET_NAMES = {
    "brackets": "Brackets",
    "inscriptions": "Inscripciones",
    "config": "Configuracion",
    "payments": "Pagos"  # Nueva hoja para registrar pagos
}

# --- 3. CREDENCIALES MERCADO PAGO ---
# Configuración de Mercado Pago (usa tus credenciales reales)

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
            return True
        return False
    except Exception as e:
        st.error(f"Error en confirmación manual: {str(e)}")
        return False


MP_PUBLIC_KEY = st.secrets["mercadopago"]["public_key"]
MP_ACCESS_TOKEN = st.secrets["mercadopago"]["access_token"]

# Inicializar SDK de Mercado Pago
def init_mercadopago():
    try:
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        return sdk
    except Exception as e:
        st.error(f"Error inicializando Mercado Pago: {str(e)}")
        return None

# --- 4. SEGURIDAD MEJORADA ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # sha256("wkbadmin123")

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 5. ESTILOS CSS MEJORADOS ---
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
    
    .border-red { 
        border-left: 6px solid #ef4444; 
        background: linear-gradient(90deg, rgba(239,68,68,0.15) 0%, rgba(31,41,55,0.9) 60%); 
    }
    
    .border-white { 
        border-left: 6px solid #ffffff; 
        background: linear-gradient(90deg, rgba(255,255,255,0.15) 0%, rgba(31,41,55,0.9) 60%); 
    }
    
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
        
        .round { 
            min-width: 240px; 
            max-width: 260px;
        }
        
        .payment-method {
            width: 120px;
            padding: 15px;
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
    
    /* QR Code styling */
    .qr-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        display: inline-block;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. CONFIGURACIÓN DEL TORNEO ---
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

# --- 7. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# --- 8. FUNCIONES DE INICIALIZACIÓN DE HOJAS ---
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
            ["inscription_price", "5", "Precio de inscripción individual en CLP"],
            ["group_discount_3", "0.9", "Descuento para 3 personas (10%)"],
            ["group_discount_5", "0.8", "Descuento para 5 personas (20%)"],
            ["mp_public_key", MP_PUBLIC_KEY, "Public key de Mercado Pago"],
            ["mp_access_token", MP_ACCESS_TOKEN, "Access token de Mercado Pago"],
            ["auto_confirm_payment", "true", "Confirmar inscripción automáticamente al pagar"]
        ]
        
        config_df = pd.DataFrame(config_data[1:], columns=config_data[0])
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=config_df)
        
        # 2. Hoja de Inscripciones
        inscriptions_columns = [
            "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", "Grado_Valor",
            "Dojo", "Organizacion", "Telefono", "Email", "Categoria", 
            "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64",
            "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID", "Estado",
            "MP_Payment_ID", "MP_Status", "MP_Date_Approved"
        ]
        
        inscriptions_df = pd.DataFrame(columns=inscriptions_columns)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=inscriptions_df)
        
        # 3. Hoja de Pagos
        payments_columns = [
            "payment_id", "inscription_id", "transaction_amount", "currency_id",
            "status", "status_detail", "date_created", "date_approved",
            "payment_method_id", "payment_type_id", "payer_email",
            "payer_identification", "notification_url", "webhook_received"
        ]
        
        payments_df = pd.DataFrame(columns=payments_columns)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["payments"], data=payments_df)
        
        # 4. Hoja de Brackets
        brackets_columns = [
            "Category", "Match_ID", "Round", "Match_Number",
            "P1_Name", "P1_ID", "P1_Dojo", "P1_Votes",
            "P2_Name", "P2_ID", "P2_Dojo", "P2_Votes",
            "Winner", "Winner_ID", "Live", "Status"
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
                    "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending"
                })
            for i in range(1, 3):
                all_brackets.append({
                    "Category": category,
                    "Match_ID": f"S{i}",
                    "Round": "Semifinal",
                    "Match_Number": i,
                    "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
                    "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
                    "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending"
                })
            all_brackets.append({
                "Category": category,
                "Match_ID": "F1",
                "Round": "Final",
                "Match_Number": 1,
                "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
                "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
                "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending"
            })
        
        brackets_df = pd.DataFrame(all_brackets)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=brackets_df)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error inicializando hojas: {str(e)}")
        return False

# --- 9. FUNCIONES DE CARGA DE DATOS ---
@st.cache_data(ttl=15)
def load_brackets():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], ttl=15)
        return df
    except Exception as e:
        st.error(f"Error cargando brackets: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=15)
def load_inscriptions():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], ttl=15)
        return df
    except Exception as e:
        st.error(f"Error cargando inscripciones: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=15)
def load_config():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=15)
        if df.empty:
            initialize_sheets()
            df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=15)
        return df
    except Exception as e:
        try:
            initialize_sheets()
            conn = get_connection()
            df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=15)
            return df
        except:
            return pd.DataFrame(columns=["setting", "value", "description"])

@st.cache_data(ttl=15)
def load_payments():
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["payments"], ttl=15)
        return df
    except Exception as e:
        st.error(f"Error cargando pagos: {str(e)}")
        return pd.DataFrame()

def save_inscriptions(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando inscripciones: {str(e)}")

def save_payments(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["payments"], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando pagos: {str(e)}")

def save_brackets(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando brackets: {str(e)}")

def save_config(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando configuración: {str(e)}")

# --- 10. FUNCIONES DE GESTIÓN DEL TORNEO ---
def get_tournament_stage():
    try:
        config_df = load_config()
        if config_df.empty:
            return "inscription"
        stage_row = config_df[config_df['setting'] == 'tournament_stage']
        if stage_row.empty:
            return "inscription"
        return stage_row.iloc[0]['value']
    except:
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
    except:
        return True

def set_registration_status(status):
    try:
        config_df = load_config()
        if config_df.empty:
            return False
        config_df.loc[config_df['setting'] == 'registration_open', 'value'] = str(status).lower()
        save_config(config_df)
        return True
    except:
        return False

def set_tournament_stage(stage):
    try:
        config_df = load_config()
        if config_df.empty:
            return False
        config_df.loc[config_df['setting'] == 'tournament_stage', 'value'] = stage
        save_config(config_df)
        return True
    except:
        return False

# --- 11. FUNCIONES DE MERCADO PAGO ---
def create_mercadopago_preference(total_amount, description, participant_email, inscription_id, return_url=None):
    """
    Crea una preferencia de pago en Mercado Pago
    """
    try:
        sdk = init_mercadopago()
        if not sdk:
            return None
        
        # URL de notificación (webhook)
        base_url = st.secrets.get("public_url", "https://wkbchile-br5ucwq5ptkox2fnxasjyp.streamlit.app/")
        notification_url = f"{base_url}/webhook"
        
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
                "installments": 1  # Solo pago al contado
            },
            "back_urls": {
                "success": return_url or f"{base_url}/?payment=success",
                "failure": return_url or f"{base_url}/?payment=failure",
                "pending": return_url or f"{base_url}/?payment=pending"
            },
            "auto_return": "approved",
            "notification_url": notification_url,
            "external_reference": inscription_id,
            "statement_descriptor": "WKB TORNEO"
        }
        
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response and "response" in preference_response:
            return preference_response["response"]
        else:
            st.error(f"Error creando preferencia: {preference_response}")
            return None
            
    except Exception as e:
        st.error(f"Error en Mercado Pago: {str(e)}")
        return None

def process_mercadopago_payment(payment_data):
    """
    Procesa la respuesta de pago de Mercado Pago
    """
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
            "webhook_received": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Guardar en hoja de pagos
        new_payment = pd.DataFrame([payment_info])
        payments_df = pd.concat([payments_df, new_payment], ignore_index=True)
        save_payments(payments_df)
        
        # Actualizar estado de la inscripción
        if payment_info["status"] == "approved":
            inscriptions_df = load_inscriptions()
            mask = inscriptions_df["Codigo_Pago"] == payment_info["inscription_id"]
            
            if not inscriptions_df[mask].empty:
                inscriptions_df.loc[mask, "Estado_Pago"] = "Confirmado"
                inscriptions_df.loc[mask, "MP_Payment_ID"] = payment_info["payment_id"]
                inscriptions_df.loc[mask, "MP_Status"] = payment_info["status"]
                inscriptions_df.loc[mask, "MP_Date_Approved"] = payment_info["date_approved"]
                
                save_inscriptions(inscriptions_df)
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Error procesando pago: {str(e)}")
        return False

def get_payment_status(payment_id):
    """
    Consulta el estado de un pago en Mercado Pago
    """
    try:
        sdk = init_mercadopago()
        if not sdk:
            return None
        
        payment_response = sdk.payment().get(payment_id)
        
        if payment_response and "response" in payment_response:
            return payment_response["response"]
        return None
        
    except Exception as e:
        st.error(f"Error consultando pago: {str(e)}")
        return None

# --- 12. FUNCIONES DE UTILIDAD ---

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
            return base_price * participants_count * discount
        else:
            return base_price * participants_count
    except:
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

# --- 13. FUNCIONES DE INSCRIPCIÓN ---
def save_participants_temporarily(participants_list, inscription_type, payment_code):
    """
    Guarda participantes temporalmente (antes del pago)
    """
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
                "MP_Date_Approved": ""
            }
            
            new_row = pd.DataFrame([new_participant])
            inscriptions_df = pd.concat([inscriptions_df, new_row], ignore_index=True)
            saved_ids.append(participant_id)
        
        save_inscriptions(inscriptions_df)
        return saved_ids, group_id
        
    except Exception as e:
        st.error(f"Error guardando participantes: {str(e)}")
        return [], ""

# --- 14. VISTA DE INSCRIPCIÓN CON MERCADO PAGO ---
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
    
    # Verificar si hay parámetros de pago en la URL
    query_params = st.query_params
    if "payment" in query_params:
        handle_payment_callback(query_params["payment"])
        return
    
    st.markdown("### 📝 SISTEMA DE INSCRIPCIÓN - WKB CHILE 2024")
    
    # Verificar si las inscripciones están abiertas
    if not is_registration_open():
        st.warning("⚠️ **LAS INSCRIPCIONES ESTÁN CERRADAS**")
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

def handle_payment_callback(payment_status):
    """Maneja el callback de Mercado Pago"""
    if payment_status == "success":
        st.session_state.payment_processed = True
        st.session_state.payment_status = "success"
        st.success("✅ ¡Pago procesado exitosamente!")
    elif payment_status == "failure":
        st.session_state.payment_processed = True
        st.session_state.payment_status = "failure"
        st.error("❌ El pago fue rechazado. Por favor intenta nuevamente.")
    elif payment_status == "pending":
        st.session_state.payment_processed = True
        st.session_state.payment_status = "pending"
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
    st.info("""
    **💡 INFORMACIÓN IMPORTANTE:**
    - **Pago seguro:** Utilizamos Mercado Pago para procesar tus pagos
    - **Individual:** $50.000 CLP por persona
    - **Grupal (3+ personas):** 10% descuento ($45.000 c/u)
    - **Grupal (5+ personas):** 20% descuento ($40.000 c/u)
    - **Múltiples métodos:** Tarjeta de crédito/débito, transferencia, efectivo
    - **Inscripción inmediata:** Confirmación automática al pagar
    """)

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
            edad = st.number_input("Edad *", min_value=5, max_value=80, value=18)
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
            if not all([nombre_completo, dojo, organizacion, telefono, email, categoria]):
                st.error("❌ Por favor completa todos los campos obligatorios (*)")
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
                else:
                    st.session_state.group_participants.append(participant_data)
                    st.success(f"✅ Participante agregado. Total: {len(st.session_state.group_participants)}")
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
                        st.rerun()
        
        col_proceed1, col_proceed2, col_proceed3 = st.columns([1, 2, 1])
        with col_proceed2:
            if st.button("🚀 PROCEDER AL PAGO", type="primary", 
                       use_container_width=True):
                st.session_state.inscription_step = 3
                st.rerun()

def show_payment_section():
    """Muestra la sección de pago con Mercado Pago"""
    st.markdown("#### 💳 PAGO CON MERCADO PAGO")
    
    # Calcular total
    if st.session_state.inscription_type == "individual":
        participants_count = 1
        participants_list = [st.session_state.current_participant]
        primary_email = st.session_state.current_participant["email"]
        description = f"Individual - {st.session_state.current_participant['nombre_completo']}"
    else:
        participants_count = len(st.session_state.group_participants)
        participants_list = st.session_state.group_participants
        primary_email = st.session_state.group_participants[0]["email"] if participants_list else ""
        description = f"Grupal - {participants_count} participantes"
    
    total_price = calculate_price(participants_count, st.session_state.inscription_type)
    
    # Mostrar resumen
    st.markdown(f"""
    <div style='background: #1f2937; padding: 20px; border-radius: 10px; border-left: 5px solid #FDB931;'>
        <h4 style='margin-top: 0; color: #FDB931;'>RESUMEN DE INSCRIPCIÓN</h4>
        <p><strong>Tipo:</strong> {st.session_state.inscription_type.upper()}</p>
        <p><strong>Participantes:</strong> {participants_count}</p>
        <p><strong>Total a pagar:</strong> <span style='color: #FDB931; font-size: 24px;'>${total_price:,.0f} CLP</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Detalles de participantes
    with st.expander("📋 VER DETALLES DE PARTICIPANTES"):
        for i, p in enumerate(participants_list, 1):
            st.markdown(f"**{i}. {p['nombre_completo']}** - {p['categoria']} - {p['dojo']}")
    
    # Métodos de pago
    st.markdown("---")
    st.markdown("#### 💰 MÉTODOS DE PAGO DISPONIBLES")
    
    # Mostrar métodos de pago
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="payment-method">
            <div class="payment-icon">💳</div>
            <div>Tarjeta de Crédito</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="payment-method">
            <div class="payment-icon">🏦</div>
            <div>Tarjeta de Débito</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="payment-method">
            <div class="payment-icon">📱</div>
            <div>Mercado Pago</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="payment-method">
            <div class="payment-icon">💰</div>
            <div>Efectivo</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("💡 **Todos los pagos son procesados de forma segura por Mercado Pago**")
    
    # Botón de pago con Mercado Pago
    st.markdown("---")
    
    if not st.session_state.inscription_code:
        # Generar código de inscripción único
        st.session_state.inscription_code = generate_inscription_code()
        
        # Guardar participantes temporalmente
        saved_ids, group_id = save_participants_temporarily(
            participants_list,
            st.session_state.inscription_type,
            st.session_state.inscription_code
        )
        
        if not saved_ids:
            st.error("❌ Error al guardar la inscripción. Por favor intenta nuevamente.")
            return
    
    # Crear preferencia de pago
    with st.spinner("🔄 Preparando pago seguro..."):
        preference = create_mercadopago_preference(
            total_amount=total_price,
            description=description,
            participant_email=primary_email,
            inscription_id=st.session_state.inscription_code,
            return_url=st.secrets.get("public_url", "https://wkb-torneo.streamlit.app")
        )
    
    if preference and "init_point" in preference:
        # Mostrar botón de pago
        payment_url = preference["init_point"]
        
        st.markdown(f""
        <a href="{payment_url}" target="_blank">
            <button class="mercado-pago-btn">
                PAGAR ${total_price} CON MERCADO PAGO
            </button>
        </a>
        "", unsafe_allow_html=True)
        
        # Mostrar ID de la preferencia para debugging
        st.caption(f"ID de preferencia: {preference.get('id')}")
        
        # QR Code para pagos móviles
        st.markdown("---")
        st.markdown("#### 📱 PAGO CON CÓDIGO QR")
        st.info("Escanea este código QR con la app de Mercado Pago para pagar desde tu celular")
        
        # Generar URL para QR
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={payment_url}"
        st.image(qr_url, caption="Escanea para pagar", width=200)
        
    else:
        st.error("❌ Error al crear el pago. Por favor intenta nuevamente.")
    
    # Botón para volver
    st.markdown("---")
    if st.button("🔙 VOLVER A MODIFICAR PARTICIPANTES", 
                use_container_width=True,
                type="secondary"):
        st.session_state.inscription_step = 2
        st.rerun()
                    
# --- BOTÓN DE CONFIRMACIÓN DIRECTA (PARA PRUEBAS) ---
    st.markdown("---")
    with st.expander("🛠️ OPCIONES DE DESARROLLADOR"):
        st.warning("Este botón confirma la inscripción inmediatamente sin cobrar.")
        if st.button("✅ CONFIRMAR INSCRIPCIÓN DIRECTAMENTE", use_container_width=True):
            if confirm_inscription_manually(st.session_state.inscription_code):
                st.session_state.payment_processed = True
                st.session_state.payment_status = "success"
                st.success("Inscripción confirmada manualmente.")
                time.sleep(1)
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
    
    # Animación de éxito
    st.markdown("""
    <div class="success-animation">
        <div class="success-icon">🎉</div>
        <h1 style="color: #10B981;">¡PAGO EXITOSO!</h1>
        <p style="font-size: 20px; color: #9ca3af;">Tu inscripción ha sido confirmada</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar detalles
    st.markdown(f"""
    <div style='background: #1f2937; padding: 30px; border-radius: 15px; margin: 30px 0; border: 2px solid #10B981;'>
        <h3 style='color: #FDB931; text-align: center;'>✅ INSCRIPCIÓN CONFIRMADA</h3>
        
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;'>
            <div style='background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 10px;'>
                <div style='color: #9ca3af; font-size: 14px;'>CÓDIGO DE INSCRIPCIÓN</div>
                <div style='color: #FDB931; font-size: 24px; font-weight: bold; letter-spacing: 2px;'>{st.session_state.inscription_code}</div>
            </div>
            
            <div style='background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 10px;'>
                <div style='color: #9ca3af; font-size: 14px;'>ESTADO</div>
                <div style='color: #10B981; font-size: 20px; font-weight: bold;'>CONFIRMADO ✓</div>
            </div>
        </div>
        
        <div style='margin-top: 30px; padding: 20px; background: rgba(253, 185, 49, 0.1); border-radius: 10px;'>
            <h4 style='color: #FDB931; margin-top: 0;'>📧 PRÓXIMOS PASOS</h4>
            <p style='color: #e5e7eb;'>
                • Recibirás un correo de confirmación con todos los detalles<br>
                • Guarda tu código de inscripción para cualquier consulta<br>
                • Revisa las fechas y horarios del torneo<br>
                • Prepárate para competir
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Acciones posteriores
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 VOLVER AL INICIO", type="primary", use_container_width=True):
            # Resetear estado
            st.session_state.inscription_step = 1
            st.session_state.current_participant = {}
            st.session_state.group_participants = []
            st.session_state.payment_processed = False
            st.session_state.payment_status = None
            st.session_state.inscription_code = None
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
    </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    **📧 RECIBIRÁS UNA NOTIFICACIÓN**
    - Te enviaremos un correo cuando el pago sea aprobado
    - Si el pago no se completa en 24 horas, será cancelado automáticamente
    - Puedes reintentar el pago en cualquier momento
    """)
    
    # Botones de acción
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 VERIFICAR ESTADO", use_container_width=True):
            # Aquí podrías implementar la verificación del estado del pago
            st.info("El estado se actualizará automáticamente. Por favor, espera la confirmación por correo.")
    
    with col2:
        if st.button("🏠 VOLVER AL INICIO", use_container_width=True, type="secondary"):
            st.session_state.view = "HOME"
            st.session_state.inscription_step = 1
            st.session_state.current_participant = {}
            st.session_state.group_participants = []
            st.session_state.payment_processed = False
            st.session_state.payment_status = None
            st.session_state.inscription_code = None
            st.rerun()

# --- 15. FUNCIONES DE BRACKETS (similares a antes) ---
def generate_brackets_for_category(category):
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
        
        if len(category_inscriptions) < 2:
            st.warning(f"No hay suficientes inscritos confirmados en {category} (mínimo 2)")
            return False
        
        participants = category_inscriptions.to_dict('records')
        random.shuffle(participants)
        
        for i in range(1, 5):
            match_id = f"Q{i}"
            mask = (brackets_df['Category'] == category) & (brackets_df['Match_ID'] == match_id)
            
            if (i-1)*2 < len(participants):
                p1 = participants[(i-1)*2]
                p2 = participants[(i-1)*2 + 1] if (i-1)*2 + 1 < len(participants) else None
                
                brackets_df.loc[mask, 'P1_Name'] = p1['Nombre_Completo']
                brackets_df.loc[mask, 'P1_ID'] = p1['ID']
                brackets_df.loc[mask, 'P1_Dojo'] = p1['Dojo']
                brackets_df.loc[mask, 'P1_Votes'] = 0
                brackets_df.loc[mask, 'Status'] = 'Scheduled'
                
                if p2:
                    brackets_df.loc[mask, 'P2_Name'] = p2['Nombre_Completo']
                    brackets_df.loc[mask, 'P2_ID'] = p2['ID']
                    brackets_df.loc[mask, 'P2_Dojo'] = p2['Dojo']
                    brackets_df.loc[mask, 'P2_Votes'] = 0
                else:
                    brackets_df.loc[mask, 'Winner'] = p1['Nombre_Completo']
                    brackets_df.loc[mask, 'Winner_ID'] = p1['ID']
                    brackets_df.loc[mask, 'Status'] = 'Walkover'
        
        save_brackets(brackets_df)
        
        for participant in participants:
            inscriptions_df.loc[inscriptions_df['ID'] == participant['ID'], 'Estado'] = 'Emparejado'
        
        save_inscriptions(inscriptions_df)
        
        return True
    except Exception as e:
        st.error(f"Error generando brackets: {str(e)}")
        return False

def close_registration_and_generate_brackets():
    try:
        if not set_registration_status(False):
            return False
        
        brackets_created = 0
        for category in ALL_CATEGORIES:
            if generate_brackets_for_category(category):
                brackets_created += 1
        
        if brackets_created > 0:
            set_tournament_stage('competition')
            return True
        return False
    except Exception as e:
        st.error(f"Error cerrando inscripciones: {str(e)}")
        return False

# --- 16. WEBHOOK PARA MERCADO PAGO ---
def handle_webhook(request):
    """Función para manejar webhooks de Mercado Pago"""
    if request.method == "POST":
        try:
            data = request.get_json()
            
            # Verificar que es un webhook de Mercado Pago
            if data.get("type") == "payment":
                payment_id = data.get("data", {}).get("id")
                
                if payment_id:
                    # Consultar información completa del pago
                    payment_info = get_payment_status(payment_id)
                    
                    if payment_info:
                        # Procesar el pago
                        process_mercadopago_payment(payment_info)
                        
                        return {"status": "success", "message": "Payment processed"}
            
            return {"status": "error", "message": "Invalid webhook data"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    return {"status": "error", "message": "Method not allowed"}

# --- 17. VISTA HOME PRINCIPAL (simplificada) ---
def render_home_view():
    """Vista principal del sistema"""
    render_header()
    
    # Mostrar estado del torneo
    tournament_stage = get_tournament_stage()
    registration_open = is_registration_open()
    
    if tournament_stage == "inscription":
        st.success("🎯 **ETAPA DE INSCRIPCIÓN ABIERTA** - Puedes inscribirte en las categorías disponibles")
    else:
        st.info("🏆 **ETAPA DE COMPETICIÓN** - Los brackets están activos y puedes votar")
    
    # Navegación principal
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 CATEGORÍAS", "📝 INSCRIBIRSE", "👥 INSCRITOS", "⚙️ ADMIN"])
    
    with tab1:
        st.markdown("### 📂 SELECCIONA TU CATEGORÍA")
        
        # Mostrar categorías
        for category in ALL_CATEGORIES:
            cat_display = category.split(" | ")[-1]
            if st.button(cat_display, key=f"cat_{category}", use_container_width=True):
                st.session_state.view = "BRACKET"
                st.session_state.cat = category
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
            total_inscritos = len(inscriptions_df)
            confirmados = len(inscriptions_df[inscriptions_df['Estado_Pago'] == 'Confirmado']) if 'Estado_Pago' in inscriptions_df.columns else 0
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            with col_stats1:
                st.metric("Total Inscritos", total_inscritos)
            with col_stats2:
                st.metric("Confirmados", confirmados)
            with col_stats3:
                st.metric("Pendientes", total_inscritos - confirmados)
            
            # Estadísticas por categoría
            if 'Categoria' in inscriptions_df.columns:
                st.markdown("#### 📊 INSCRIPCIONES POR CATEGORÍA")
                insc_por_cat = inscriptions_df['Categoria'].value_counts()
                if not insc_por_cat.empty:
                    st.bar_chart(insc_por_cat)
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
            
            if current_stage == "inscription":
                if st.button("🚀 CERRAR INSCRIPCIONES Y GENERAR BRACKETS", 
                           type="primary", use_container_width=True):
                    with st.spinner("Generando brackets..."):
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
            
            # Sistema de reset
            st.markdown("---")
            st.markdown("#### ⚠️ SISTEMA DE RESET")
            
            if st.button("🔄 RESETEAR TODO EL SISTEMA", type="secondary", use_container_width=True):
                confirm = st.checkbox("Confirmo que quiero borrar TODOS los datos")
                if confirm:
                    if st.button("✅ CONFIRMAR RESET COMPLETO", type="primary"):
                        if initialize_sheets():
                            st.success("✅ Sistema reseteado exitosamente")
                            time.sleep(2)
                            st.rerun()

# --- 18. VISTA DE BRACKETS (simplificada) ---
def render_bracket_view():
    """Vista simplificada de brackets"""
    cat = st.session_state.cat
    
    st.markdown(f"### 🏆 {cat}")
    
    # Cargar brackets
    brackets_df = load_brackets()
    if brackets_df.empty:
        st.info("Los brackets se generarán automáticamente cuando se cierren las inscripciones.")
        if st.button("🏠 VOLVER AL INICIO"):
            st.session_state.view = "HOME"
            st.rerun()
        return
    
    cat_df = brackets_df[brackets_df['Category'] == cat]
    if cat_df.empty:
        st.warning(f"No hay brackets generados para {cat} aún.")
        return
    
    # Mostrar matches
    st.markdown("#### 🥋 PARTIDOS PROGRAMADOS")
    
    for _, match in cat_df.iterrows():
        if match['P1_Name'] and match['P2_Name']:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 3])
                with col1:
                    st.markdown(f"**🔴 {match['P1_Name']}**")
                    st.caption(f"{match['P1_Dojo']}")
                with col2:
                    st.markdown("**VS**", help="Cuartos de final")
                with col3:
                    st.markdown(f"**⚪ {match['P2_Name']}**")
                    st.caption(f"{match['P2_Dojo']}")
                
                st.markdown("---")
    
    if st.button("🏠 VOLVER AL INICIO"):
        st.session_state.view = "HOME"
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
            initialize_sheets()
    except:
        initialize_sheets()
    
    # Navegación entre vistas
    if st.session_state.view == "HOME":
        render_home_view()
    elif st.session_state.view == "INSCRIPTION":
        render_inscription_view()
    elif st.session_state.view == "BRACKET":
        render_bracket_view()

# --- 20. EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    # Configuración para Streamlit Cloud
    import os
    if "STREAMLIT_DEPLOYMENT" in os.environ:
        # Configurar URL pública para webhooks
        public_url = os.environ.get("PUBLIC_URL", "https://wkb-torneo.streamlit.app")
        st.secrets["public_url"] = public_url
    
    main()
