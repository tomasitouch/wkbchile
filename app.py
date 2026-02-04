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
    "votes": "Votos"
}

# --- 3. SEGURIDAD MEJORADA ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # sha256("wkbadmin123")

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 4. ESTILOS CSS MEJORADOS ---
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
    }
    
    /* Animación para inscripción exitosa */
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
</style>
""", unsafe_allow_html=True)

# --- 5. CONFIGURACIÓN DEL TORNEO ---
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

# --- 6. CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# --- 7. FUNCIONES DE INICIALIZACIÓN DE HOJAS ---
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
            ["auto_confirm_payment", "true", "Confirmar pago automáticamente"]
        ]
        
        config_df = pd.DataFrame(config_data[1:], columns=config_data[0])
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=config_df)
        
        # 2. Hoja de Inscripciones
        inscriptions_columns = [
            "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", "Grado_Valor",
            "Dojo", "Organizacion", "Telefono", "Email", "Categoria", 
            "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64",
            "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID", "Estado"
        ]
        
        inscriptions_df = pd.DataFrame(columns=inscriptions_columns)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=inscriptions_df)
        
        # 3. Hoja de Brackets
        brackets_columns = [
            "Category", "Match_ID", "Round", "Match_Number",
            "P1_Name", "P1_ID", "P1_Dojo", "P1_Votes",
            "P2_Name", "P2_ID", "P2_Dojo", "P2_Votes",
            "Winner", "Winner_ID", "Live", "Status"
        ]
        
        # Crear estructura inicial para todas las categorías
        all_brackets = []
        for category in ALL_CATEGORIES:
            # Cuartos de final (Q1-Q4)
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
            # Semifinales (S1-S2)
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
            # Final (F1)
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
        
        # 4. Hoja de Votos (opcional)
        votes_columns = [
            "vote_id", "category", "match_id", "voter_id", "voted_for",
            "timestamp", "ip_address", "user_agent"
        ]
        
        votes_df = pd.DataFrame(columns=votes_columns)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["votes"], data=votes_df)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error inicializando hojas: {str(e)}")
        return False

# --- 8. FUNCIONES DE CARGA DE DATOS CON MANEJO DE ERRORES ---
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

def save_brackets(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando brackets: {str(e)}")

def save_inscriptions(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando inscripciones: {str(e)}")

def save_config(df):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando configuración: {str(e)}")

# --- 9. FUNCIONES DE GESTIÓN DEL TORNEO CON MANEJO DE ERRORES ---
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

def is_auto_confirm_payment():
    """Verifica si el sistema debe confirmar pagos automáticamente"""
    try:
        config_df = load_config()
        if config_df.empty:
            return True  # Por defecto, confirmar automáticamente
        
        auto_row = config_df[config_df['setting'] == 'auto_confirm_payment']
        if auto_row.empty:
            return True
        
        value = auto_row.iloc[0]['value']
        if pd.isna(value):
            return True
        
        return str(value).lower() == 'true'
    except:
        return True

# --- 10. FUNCIONES DE UTILIDAD ---
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

def generate_payment_code():
    """Genera un código de pago único"""
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    random_chars = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"WKB{timestamp}{random_chars}"

def generate_participant_id():
    """Genera un ID único para el participante"""
    return f"P{str(uuid.uuid4())[:8].upper()}"

def generate_group_id():
    """Genera un ID único para grupos"""
    return f"G{str(uuid.uuid4())[:6].upper()}"

# --- 11. FUNCIONES DE INSCRIPCIÓN AUTOMÁTICA ---
def save_participant_auto(participant_data, inscription_type, group_id=None, payment_code=None):
    """
    Guarda un participante automáticamente con estado CONFIRMADO
    """
    try:
        inscriptions_df = load_inscriptions()
        
        # Generar IDs únicos
        participant_id = generate_participant_id()
        
        # Estado de pago: CONFIRMADO automáticamente
        payment_status = "Confirmado" if is_auto_confirm_payment() else "Pendiente"
        
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
            "Codigo_Pago": payment_code if payment_code else generate_payment_code(),
            "Fecha_Inscripcion": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Foto_Base64": participant_data.get("foto_base64", ""),
            "Consentimiento": participant_data["consentimiento"],
            "Descargo": participant_data["descargo"],
            "Estado_Pago": payment_status,
            "Grupo_ID": group_id if inscription_type == "colectivo" else "",
            "Estado": "Inscrito"
        }
        
        new_row = pd.DataFrame([new_participant])
        inscriptions_df = pd.concat([inscriptions_df, new_row], ignore_index=True)
        
        save_inscriptions(inscriptions_df)
        return participant_id, payment_status
    except Exception as e:
        st.error(f"Error guardando participante: {str(e)}")
        return None, None

def process_inscription_payment(participants_list, inscription_type):
    """
    Procesa el pago y guarda todos los participantes automáticamente
    """
    try:
        # Generar código de pago único para toda la transacción
        payment_code = generate_payment_code()
        
        # Generar group_id si es inscripción colectiva
        group_id = generate_group_id() if inscription_type == "colectivo" else None
        
        saved_ids = []
        for participant in participants_list:
            participant_id, payment_status = save_participant_auto(
                participant, 
                inscription_type, 
                group_id, 
                payment_code
            )
            if participant_id:
                saved_ids.append((participant_id, payment_status))
        
        return saved_ids, payment_code
    except Exception as e:
        st.error(f"Error procesando inscripción: {str(e)}")
        return [], None

# --- 12. FUNCIONES DE BRACKETS ---
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

# --- 13. FUNCIÓN DE RESET ---
def reset_all_data():
    try:
        initialize_sheets()
        
        keys_to_clear = ['view', 'cat', 'page', 'voted_matches', 
                        'inscription_type', 'group_participants', 
                        'current_participant', 'inscription_step',
                        'payment_code', 'is_admin', 'confirm_reset']
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error reseteando datos: {str(e)}")
        return False





def render_header():
    logo_org = "https://cdn-icons-png.flaticon.com/512/1603/1603754.png" 
    logo_spon1 = "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg" 
    logo_spon2 = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
    
    # Mostrar etapa actual del torneo
    tournament_stage = get_tournament_stage()
    stage_text = "INSCRIPCIONES ABIERTAS" if tournament_stage == "inscription" else "COMPETICIÓN EN CURSO"
    stage_class = "stage-open" if tournament_stage == "inscription" else "stage-closed"
    
    st.markdown(f"""
    <div class="header-container">
        <div class="header-title">
            <img src="{logo_org}" height="50" style="margin-right:15px; filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));">
            <div>
                <h2 style="margin:0; color:white;">WKB CHILE 
                    <span class="stage-badge {stage_class}">{stage_text}</span>
                </h2>
                <small style="color:#FDB931; font-weight:bold; letter-spacing: 1px;">OFFICIAL TOURNAMENT HUB</small>
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


    

# --- 14. VISTA DE INSCRIPCIÓN MEJORADA (AUTOMÁTICA) ---
def render_inscription_view():
    """Vista principal de inscripción con confirmación automática"""
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
    if 'inscription_complete' not in st.session_state:
        st.session_state.inscription_complete = False
    if 'last_payment_code' not in st.session_state:
        st.session_state.last_payment_code = ""
    
    # Si ya se completó una inscripción, mostrar mensaje de éxito
    if st.session_state.inscription_complete:
        show_inscription_success()
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
    
    # Paso 1: Selección de tipo
    if st.session_state.inscription_step == 1:
        show_inscription_type_selection()
    
    # Paso 2: Formulario de inscripción
    elif st.session_state.inscription_step == 2:
        show_inscription_form()
    
    # Paso 3: Sistema de pago
    elif st.session_state.inscription_step == 3:
        show_payment_section()

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
    - **Inscripción inmediata:** Una vez completado el pago, tu inscripción será automática
    - **Individual:** $50.000 CLP por persona
    - **Grupal (3+ personas):** 10% descuento ($45.000 c/u)
    - **Grupal (5+ personas):** 20% descuento ($40.000 c/u)
    - **Sistema automático:** No requiere confirmación manual
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
    """Muestra la sección de pago con confirmación automática"""
    st.markdown("#### 💳 SISTEMA DE PAGO AUTOMÁTICO")
    
    # Calcular total
    if st.session_state.inscription_type == "individual":
        participants_count = 1
        participants_list = [st.session_state.current_participant]
    else:
        participants_count = len(st.session_state.group_participants)
        participants_list = st.session_state.group_participants
    
    total_price = calculate_price(participants_count, st.session_state.inscription_type)
    
    # Mostrar resumen
    st.markdown(f"""
    <div style='background: #1f2937; padding: 20px; border-radius: 10px; border-left: 5px solid #FDB931;'>
        <h4 style='margin-top: 0; color: #FDB931;'>RESUMEN DE INSCRIPCIÓN</h4>
        <p><strong>Tipo:</strong> {st.session_state.inscription_type.upper()}</p>
        <p><strong>Participantes:</strong> {participants_count}</p>
        <p><strong>Total a pagar:</strong> <span style='color: #FDB931; font-size: 24px;'>${total_price:,.0f} CLP</span></p>
        <p><strong>Estado:</strong> <span style='color: #10B981; font-weight: bold;'>INSCRIPCIÓN AUTOMÁTICA</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Detalles de participantes
    with st.expander("📋 VER DETALLES DE PARTICIPANTES"):
        for i, p in enumerate(participants_list, 1):
            st.markdown(f"**{i}. {p['nombre_completo']}** - {p['categoria']} - {p['dojo']}")
    
    # Sistema de pago simplificado
    st.markdown("---")
    st.markdown("#### 🔄 PROCESO DE PAGO")
    
    # Información de pago
    st.info("""
    **💰 MÉTODO DE PAGO: TRANSFERENCIA BANCARIA**
    
    **Cuenta de destino:**
    - **Banco:** Banco de Chile
    - **Cuenta:** 1234567890
    - **Titular:** WKB Chile Organización
    - **RUT:** 12.345.678-9
    
    **⚠️ IMPORTANTE:**
    1. Realiza la transferencia por el monto exacto
    2. En el comentario escribe: **"WKB TORNEO"**
    3. Guarda el comprobante de transferencia
    """)
    
    # Botón para confirmar pago
    st.markdown("---")
    st.markdown("##### ✅ CONFIRMACIÓN DE PAGO")
    
    # Simulación de pago (en producción esto sería integrado con MercadoPago/Transbank)
    if st.button(f"💰 CONFIRMAR PAGO DE ${total_price:,.0f} CLP", 
                type="primary", 
                use_container_width=True,
                key="confirm_payment_btn"):
        
        with st.spinner("🔄 Procesando inscripción automática..."):
            # Procesar la inscripción automáticamente
            saved_ids, payment_code = process_inscription_payment(
                participants_list, 
                st.session_state.inscription_type
            )
            
            if saved_ids and payment_code:
                # Guardar código de pago
                st.session_state.last_payment_code = payment_code
                
                # Marcar como completado
                st.session_state.inscription_complete = True
                
                # Mostrar animación de éxito
                st.markdown("""
                <div id="confetti-container"></div>
                <script>
                function createConfetti() {
                    const container = document.getElementById('confetti-container');
                    for(let i = 0; i < 50; i++) {
                        const confetti = document.createElement('div');
                        confetti.className = 'confetti';
                        confetti.style.left = Math.random() * 100 + 'vw';
                        confetti.style.animationDelay = Math.random() * 2 + 's';
                        confetti.style.backgroundColor = i % 3 === 0 ? '#FDB931' : (i % 3 === 1 ? '#EF4444' : '#10B981');
                        container.appendChild(confetti);
                    }
                }
                createConfetti();
                </script>
                """, unsafe_allow_html=True)
                
                # Rerun para mostrar pantalla de éxito
                st.rerun()
            else:
                st.error("❌ Error al procesar la inscripción. Por favor intenta nuevamente.")
    
    # Botón para volver
    st.markdown("---")
    if st.button("🔙 VOLVER A MODIFICAR PARTICIPANTES", 
                use_container_width=True,
                type="secondary"):
        st.session_state.inscription_step = 2
        st.rerun()

def show_inscription_success():
    """Muestra la pantalla de éxito después de la inscripción automática"""
    render_header()
    
    # Animación de confeti
    st.markdown("""
    <style>
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
    </style>
    
    <div class="success-animation">
        <div class="success-icon">🎉</div>
        <h1 style="color: #10B981;">¡INSCRIPCIÓN EXITOSA!</h1>
        <p style="font-size: 20px; color: #9ca3af;">Tu inscripción ha sido procesada automáticamente</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar detalles
    st.markdown(f"""
    <div style='background: #1f2937; padding: 30px; border-radius: 15px; margin: 30px 0; border: 2px solid #10B981;'>
        <h3 style='color: #FDB931; text-align: center;'>📋 DETALLES DE TU INSCRIPCIÓN</h3>
        
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;'>
            <div style='background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 10px;'>
                <div style='color: #9ca3af; font-size: 14px;'>CÓDIGO DE INSCRIPCIÓN</div>
                <div style='color: #FDB931; font-size: 24px; font-weight: bold; letter-spacing: 2px;'>{st.session_state.last_payment_code}</div>
            </div>
            
            <div style='background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 10px;'>
                <div style='color: #9ca3af; font-size: 14px;'>TIPO</div>
                <div style='color: white; font-size: 20px; font-weight: bold;'>{st.session_state.inscription_type.upper()}</div>
            </div>
            
            <div style='background: rgba(16, 185, 129, 0.1); padding: 15px; border-radius: 10px;'>
                <div style='color: #9ca3af; font-size: 14px;'>ESTADO</div>
                <div style='color: #10B981; font-size: 20px; font-weight: bold;'>CONFIRMADO ✓</div>
            </div>
        </div>
        
        <div style='margin-top: 30px; padding: 20px; background: rgba(253, 185, 49, 0.1); border-radius: 10px;'>
            <h4 style='color: #FDB931; margin-top: 0;'>📧 INFORMACIÓN IMPORTANTE</h4>
            <p style='color: #e5e7eb;'>
                • Tu inscripción está <strong>CONFIRMADA</strong> automáticamente<br>
                • Recibirás un correo con los detalles en <strong>{st.session_state.current_participant.get('email', 'tu correo') if st.session_state.inscription_type == 'individual' else 'los correos registrados'}</strong><br>
                • Guarda tu código de inscripción para cualquier consulta<br>
                • El estado de pago es: <span style='color: #10B981; font-weight: bold;'>CONFIRMADO</span>
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Acciones posteriores a la inscripción
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏠 VOLVER AL INICIO", type="primary", use_container_width=True):
            # Resetear estado de inscripción
            st.session_state.inscription_step = 1
            st.session_state.current_participant = {}
            st.session_state.group_participants = []
            st.session_state.inscription_complete = False
            st.session_state.view = "HOME"
            st.rerun()
    
    # Mostrar participantes inscritos
    if st.session_state.inscription_type == "colectivo" and st.session_state.group_participants:
        st.markdown("---")
        st.markdown("#### 👥 PARTICIPANTES INSCRITOS")
        
        for i, participant in enumerate(st.session_state.group_participants, 1):
            with st.container():
                st.markdown(f"""
                <div style='background: rgba(31, 41, 55, 0.5); padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #FDB931;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <strong style='color: white; font-size: 16px;'>{i}. {participant['nombre_completo']}</strong><br>
                            <span style='color: #9ca3af;'>{participant['categoria']} | {participant['dojo']}</span>
                        </div>
                        <span style='color: #10B981; font-weight: bold;'>✓ CONFIRMADO</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- 15. VISTA DE BRACKETS (sin cambios significativos) ---
def render_bracket_view():
    """Vista de brackets y competencia"""
    cat = st.session_state.cat
    brackets_df = load_brackets()
    
    if brackets_df.empty:
        st.error("No hay datos de brackets disponibles")
        st.info("Los brackets se generarán automáticamente cuando se cierren las inscripciones.")
        return
    
    cat_df = brackets_df[brackets_df['Category'] == cat]
    if cat_df.empty:
        st.warning(f"No hay brackets generados para {cat}")
        return
    
    cat_df = cat_df.set_index('Match_ID')
    
    def get_row(mid):
        try:
            return cat_df.loc[mid]
        except:
            return pd.Series()
    
    def get_val(row, col):
        if not row.empty and col in row.index:
            value = row[col]
            if pd.isna(value) or value == "":
                return "..."
            return str(value)
        return "..."
    
    render_header()
    
    # Barra superior
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 INICIO", use_container_width=True):
            st.session_state.view = "HOME"
            st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align:center; color:#FDB931; margin-top:0;'>{cat}</h3>", 
                   unsafe_allow_html=True)
    
    # Panel de control admin
    if st.session_state.get('is_admin', False):
        with st.sidebar:
            st.header("🔧 Panel Admin")
            
            tournament_stage = get_tournament_stage()
            
            if tournament_stage == "inscription":
                if st.button("🚀 CERRAR INSCRIPCIONES Y GENERAR BRACKETS", 
                           type="primary", use_container_width=True):
                    with st.spinner("Generando brackets..."):
                        if close_registration_and_generate_brackets():
                            st.success("✅ Brackets generados exitosamente!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Error generando brackets")
            
            st.subheader("✏️ Editar Match")
            match_to_edit = st.selectbox("Seleccionar match", ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1'])
            
            with st.form(f"edit_{match_to_edit}"):
                row = get_row(match_to_edit)
                
                col_edit1, col_edit2 = st.columns(2)
                with col_edit1:
                    p1_name = st.text_input("Rojo - Nombre", get_val(row, 'P1_Name'))
                    p1_dojo = st.text_input("Rojo - Dojo", get_val(row, 'P1_Dojo'))
                
                with col_edit2:
                    p2_name = st.text_input("Blanco - Nombre", get_val(row, 'P2_Name'))
                    p2_dojo = st.text_input("Blanco - Dojo", get_val(row, 'P2_Dojo'))
                
                winner = st.selectbox("Ganador", ["", p1_name, p2_name])
                
                if st.form_submit_button("💾 GUARDAR"):
                    try:
                        mask = (brackets_df['Category'] == cat) & (brackets_df['Match_ID'] == match_to_edit)
                        brackets_df.loc[mask, 'P1_Name'] = p1_name
                        brackets_df.loc[mask, 'P1_Dojo'] = p1_dojo
                        brackets_df.loc[mask, 'P2_Name'] = p2_name
                        brackets_df.loc[mask, 'P2_Dojo'] = p2_dojo
                        brackets_df.loc[mask, 'Winner'] = winner
                        
                        save_brackets(brackets_df)
                        st.success("✅ Cambios guardados!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando cambios: {str(e)}")
    
    # Sistema de votación
    st.markdown("##### 📊 PREDICCIÓN DEL PÚBLICO")
    
    if 'voted_matches' not in st.session_state:
        st.session_state.voted_matches = set()
    
    def vote(match_id, player):
        """Registra un voto para un match"""
        match_key = f"{cat}_{match_id}"
        
        if match_key in st.session_state.voted_matches:
            st.warning("Ya votaste en este match!")
            return
        
        try:
            mask = (brackets_df['Category'] == cat) & (brackets_df['Match_ID'] == match_id)
            
            if player == 'P1':
                current_votes = int(brackets_df.loc[mask, 'P1_Votes'].iloc[0] if not brackets_df.loc[mask, 'P1_Votes'].empty else 0)
                brackets_df.loc[mask, 'P1_Votes'] = current_votes + 1
            else:
                current_votes = int(brackets_df.loc[mask, 'P2_Votes'].iloc[0] if not brackets_df.loc[mask, 'P2_Votes'].empty else 0)
                brackets_df.loc[mask, 'P2_Votes'] = current_votes + 1
            
            save_brackets(brackets_df)
            st.session_state.voted_matches.add(match_key)
            st.success("✅ Voto registrado!")
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.error(f"Error registrando voto: {str(e)}")
    
    # Mostrar botones de votación para cuartos
    st.markdown('<div class="vote-buttons-container">', unsafe_allow_html=True)
    
    for match_id in ['Q1', 'Q2', 'Q3', 'Q4']:
        row = get_row(match_id)
        p1_name = get_val(row, 'P1_Name')
        p2_name = get_val(row, 'P2_Name')
        
        if p1_name != "..." and p2_name != "...":
            try:
                v1 = int(row['P1_Votes']) if 'P1_Votes' in row and not pd.isna(row['P1_Votes']) else 0
                v2 = int(row['P2_Votes']) if 'P2_Votes' in row and not pd.isna(row['P2_Votes']) else 0
                total = v1 + v2
                
                pct1 = (v1 / total * 100) if total > 0 else 0
                pct2 = (v2 / total * 100) if total > 0 else 0
            except:
                v1, v2, total = 0, 0, 0
                pct1, pct2 = 0, 0
            
            col_match = st.columns(1)[0]
            with col_match:
                col_vote1, col_vote2 = st.columns(2)
                with col_vote1:
                    if st.button(f"🔴 VOTAR {p1_name[:15]}", 
                               key=f"vote_{match_id}_p1",
                               use_container_width=True):
                        vote(match_id, 'P1')
                with col_vote2:
                    if st.button(f"⚪ VOTAR {p2_name[:15]}", 
                               key=f"vote_{match_id}_p2",
                               use_container_width=True):
                        vote(match_id, 'P2')
                
                # Barra de votación
                st.markdown(f"""
                <div style="background: #374151; height: 10px; border-radius: 5px; margin-top: 10px; overflow: hidden;">
                    <div style="width: {pct1}%; height: 100%; background: #ef4444; float: left;"></div>
                    <div style="width: {pct2}%; height: 100%; background: white; float: left;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #9ca3af; margin-top: 5px;">
                    <span>{int(pct1)}%</span>
                    <span>Total: {v1 + v2}</span>
                    <span>{int(pct2)}%</span>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Renderizar bracket visual
    st.markdown("---")
    st.markdown("#### 🏆 BRACKET OFICIAL")
    
    # Obtener datos de todos los matches
    r_q1, r_q2, r_q3, r_q4 = get_row('Q1'), get_row('Q2'), get_row('Q3'), get_row('Q4')
    r_s1, r_s2, r_f1 = get_row('S1'), get_row('S2'), get_row('F1')
    
    w_q1, w_q2 = get_val(r_q1, 'Winner'), get_val(r_q2, 'Winner')
    w_q3, w_q4 = get_val(r_q3, 'Winner'), get_val(r_q4, 'Winner')
    w_s1, w_s2 = get_val(r_s1, 'Winner'), get_val(r_s2, 'Winner')
    w_f1 = get_val(r_f1, 'Winner')
    
    # Función para renderizar un jugador
    def render_player_box(row, player_prefix, color_class):
        name = get_val(row, f'{player_prefix}_Name')
        dojo = get_val(row, f'{player_prefix}_Dojo')
        
        if player_prefix == 'P1':
            votes = int(row['P1_Votes']) if 'P1_Votes' in row and not pd.isna(row['P1_Votes']) else 0
        else:
            votes = int(row['P2_Votes']) if 'P2_Votes' in row and not pd.isna(row['P2_Votes']) else 0
        
        total_votes = 0
        try:
            v1 = int(row['P1_Votes']) if 'P1_Votes' in row and not pd.isna(row['P1_Votes']) else 0
            v2 = int(row['P2_Votes']) if 'P2_Votes' in row and not pd.isna(row['P2_Votes']) else 0
            total_votes = v1 + v2
        except:
            pass
        
        pct = (votes / total_votes * 100) if total_votes > 0 else 0
        
        return f"""
        <div class="player-box {color_class}">
            <div class="p-name">{name}</div>
            <div class="p-details">
                <span>🥋 {dojo}</span>
                <span>{int(pct)}%</span>
            </div>
            <div class="p-vote-bar">
                <div class="p-vote-fill" style="width:{pct}%; 
                    background:{'#ef4444' if color_class == 'border-red' else 'white'};"></div>
            </div>
            <div class="line-r"></div>
        </div>
        """
    
    # HTML del bracket horizontal
    html = f"""
    <div class="bracket-container">
        <div class="rounds-wrapper">
            <!-- CUARTOS DE FINAL -->
            <div class="round">
                <div class="round-title">CUARTOS DE FINAL</div>
                {render_player_box(r_q1, 'P1', 'border-red')}
                {render_player_box(r_q1, 'P2', 'border-white')}
                <div style="height:40px; position: relative;">
                    <div class="conn-v" style="height: 80px; top: -40px;"></div>
                </div>
                {render_player_box(r_q2, 'P1', 'border-red')}
                {render_player_box(r_q2, 'P2', 'border-white')}
                <div style="height:40px; position: relative;">
                    <div class="conn-v" style="height: 80px; top: -40px;"></div>
                </div>
                {render_player_box(r_q3, 'P1', 'border-red')}
                {render_player_box(r_q3, 'P2', 'border-white')}
                <div style="height:40px; position: relative;">
                    <div class="conn-v" style="height: 80px; top: -40px;"></div>
                </div>
                {render_player_box(r_q4, 'P1', 'border-red')}
                {render_player_box(r_q4, 'P2', 'border-white')}
            </div>
            
            <!-- SEMIFINALES -->
            <div class="round">
                <div class="round-title">SEMIFINALES</div>
                <div style="height: 50%; position: relative; margin-top: 20px;">
                    <div class="conn-v" style="height: 120px; top: 50%; transform: translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top: 60px;">
                        <div class="p-name">{w_q1}</div>
                        <div class="line-r"></div>
                    </div>
                    <div class="player-box border-white">
                        <div class="p-name">{w_q2}</div>
                        <div class="line-r"></div>
                    </div>
                </div>
                <div style="height: 50%; position: relative; margin-top: 40px;">
                    <div class="conn-v" style="height: 120px; top: 50%; transform: translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top: 60px;">
                        <div class="p-name">{w_q3}</div>
                        <div class="line-r"></div>
                    </div>
                    <div class="player-box border-white">
                        <div class="p-name">{w_q4}</div>
                        <div class="line-r"></div>
                    </div>
                </div>
            </div>
            
            <!-- FINAL -->
            <div class="round">
                <div class="round-title">FINAL</div>
                <div style="height: 100%; position: relative;">
                    <div class="conn-v" style="height: 160px; top: 50%; transform: translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top: 80px;">
                        <div class="p-name">{w_s1}</div>
                        <div class="line-r"></div>
                    </div>
                    <div class="player-box border-white">
                        <div class="p-name">{w_s2}</div>
                        <div class="line-r"></div>
                    </div>
                </div>
            </div>
            
            <!-- CAMPEÓN -->
            <div class="round">
                <div class="round-title">CAMPEÓN 🏆</div>
                <div style="height: 100%; display: flex; align-items: center;">
                    <div class="champion-box">
                        {w_f1 if w_f1 != "..." else "POR DEFINIR"}
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    
    st.html(html)

# --- 16. VISTA HOME PRINCIPAL ---
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
            
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.metric("Total Inscritos", total_inscritos)
            with col_stats2:
                st.metric("Confirmados", confirmados)
            
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
            
            # Configuración de confirmación automática
            st.markdown("#### ⚡ CONFIRMACIÓN AUTOMÁTICA")
            auto_confirm = is_auto_confirm_payment()
            
            if auto_confirm:
                st.success("✅ Confirmación automática ACTIVADA")
                if st.button("🔴 DESACTIVAR CONFIRMACIÓN AUTOMÁTICA", use_container_width=True):
                    try:
                        config_df = load_config()
                        config_df.loc[config_df['setting'] == 'auto_confirm_payment', 'value'] = 'false'
                        save_config(config_df)
                        st.success("✅ Confirmación automática desactivada")
                        time.sleep(1)
                        st.rerun()
                    except:
                        st.error("Error al actualizar configuración")
            else:
                st.warning("⚠️ Confirmación automática DESACTIVADA")
                if st.button("🟢 ACTIVAR CONFIRMACIÓN AUTOMÁTICA", use_container_width=True):
                    try:
                        config_df = load_config()
                        config_df.loc[config_df['setting'] == 'auto_confirm_payment', 'value'] = 'true'
                        save_config(config_df)
                        st.success("✅ Confirmación automática activada")
                        time.sleep(1)
                        st.rerun()
                    except:
                        st.error("Error al actualizar configuración")
            
            # Sistema de reset
            st.markdown("---")
            st.markdown("#### ⚠️ SISTEMA DE RESET")
            
            if st.button("🔄 RESETEAR TODO EL SISTEMA", type="secondary", use_container_width=True):
                confirm = st.checkbox("Confirmo que quiero borrar TODOS los datos")
                if confirm:
                    if st.button("✅ CONFIRMAR RESET COMPLETO", type="primary"):
                        if reset_all_data():
                            st.rerun()

# --- 17. GESTIÓN PRINCIPAL DE LA APLICACIÓN ---
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

# --- 18. EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    main()
