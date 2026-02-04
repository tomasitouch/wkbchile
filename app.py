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

# --- 3. SEGURIDAD ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # sha256("wkbadmin123")

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 4. ESTILOS CSS MEJORADOS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { 
        background-color: #0e1117; 
        color: white; 
        font-family: 'Inter', sans-serif !important;
    }
    
    h1, h2, h3, h4 { 
        font-family: 'Roboto Condensed', sans-serif !important; 
        text-transform: uppercase; 
    }
    
    /* HEADER */
    .header-container { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 20px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;
    }
    
    /* BRACKET HORIZONTAL */
    .bracket-container { 
        overflow-x: auto; overflow-y: hidden; padding: 20px 10px; 
        display: flex; justify-content: center; align-items: stretch;
        min-height: 500px; width: 100%; -webkit-overflow-scrolling: touch;
    }
    .rounds-wrapper {
        display: flex; justify-content: flex-start; align-items: stretch;
        gap: 30px; padding: 0 20px; min-width: min-content;
    }
    .round { 
        min-width: 280px; max-width: 320px; margin: 0;
        display: flex; flex-direction: column; justify-content: space-around;
        position: relative; background: rgba(31, 41, 55, 0.3);
        border-radius: 10px; padding: 15px; border: 1px solid rgba(55, 65, 81, 0.5);
    }
    
    /* PLAYER CARD */
    .player-box { 
        background: linear-gradient(145deg, #1f2937, #111827); padding: 15px; 
        margin: 10px 0; border-radius: 8px; position: relative; z-index: 2; 
        border: 1px solid #374151; min-height: 80px; display: flex; 
        flex-direction: column; justify-content: center;
    }
    .border-red { border-left: 6px solid #ef4444; background: linear-gradient(90deg, rgba(239,68,68,0.15) 0%, rgba(31,41,55,0.9) 60%); }
    .border-white { border-left: 6px solid #ffffff; background: linear-gradient(90deg, rgba(255,255,255,0.15) 0%, rgba(31,41,55,0.9) 60%); }
    
    .p-name { font-size: 16px; font-weight: bold; color: white; margin-bottom: 5px; }
    .p-details { font-size: 13px; color: #9ca3af; display: flex; justify-content: space-between; }
    
    /* CONNECTORS */
    .line-r { position: absolute; right: -32px; width: 32px; height: 2px; background: #6b7280; top: 50%; z-index: 1; }
    .conn-v { position: absolute; right: -32px; width: 2px; background: #6b7280; top: 50%; z-index: 1; transform: translateY(-50%); }
    
    /* BADGES */
    .stage-badge { padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 12px; margin-left: 10px; text-transform: uppercase; }
    .stage-open { background: #10B981; color: white; }
    .stage-closed { background: #EF4444; color: white; }
    
    /* VOTING */
    .p-vote-bar { height: 6px; background: #374151; margin-top: 10px; border-radius: 3px; overflow: hidden; }
    .p-vote-fill { height: 100%; transition: width 0.5s ease; }
    
    .champion-box { background: linear-gradient(135deg, #FDB931, #d9a024); color: black; padding: 25px; border-radius: 10px; font-weight: bold; text-align: center; }
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

# --- 7. INICIALIZACIÓN DE DATOS (AUTO-REPARACIÓN) ---
def initialize_sheets():
    """Inicializa/Repara todas las hojas necesarias si están vacías o dañadas."""
    try:
        conn = get_connection()
        
        # 1. Configuración
        config_data = [
            ["setting", "value", "description"],
            ["tournament_stage", "inscription", "Etapa del torneo"],
            ["registration_open", "true", "Estado inscripciones"],
            ["inscription_price", "50000", "Precio base"]
        ]
        config_df = pd.DataFrame(config_data[1:], columns=config_data[0])
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=config_df)
        
        # 2. Inscripciones
        insc_cols = [
            "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", "Grado_Valor",
            "Dojo", "Organizacion", "Telefono", "Email", "Categoria", 
            "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64",
            "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID", "Estado"
        ]
        insc_df = pd.DataFrame(columns=insc_cols)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=insc_df)
        
        # 3. Brackets (Estructura base)
        brackets_data = []
        for cat in ALL_CATEGORIES:
            # Cuartos (Q1-Q4)
            for i in range(1, 5):
                brackets_data.append({"Category": cat, "Match_ID": f"Q{i}", "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": "", "Live": False, "Status": "Pending"})
            # Semis (S1-S2)
            for i in range(1, 3):
                brackets_data.append({"Category": cat, "Match_ID": f"S{i}", "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": "", "Live": False, "Status": "Pending"})
            # Final (F1)
            brackets_data.append({"Category": cat, "Match_ID": "F1", "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": "", "Live": False, "Status": "Pending"})
        
        brackets_df = pd.DataFrame(brackets_data)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=brackets_df)
        
        # 4. Votos
        votes_df = pd.DataFrame(columns=["match_id", "category", "vote_for", "timestamp"])
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["votes"], data=votes_df)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error inicializando hojas: {str(e)}")
        return False

# --- 8. FUNCIONES DE CARGA (ROBUSTAS) ---
def safe_load_df(sheet_name, expected_columns=None):
    """Carga un DataFrame de manera segura, inicializando si es necesario."""
    try:
        conn = get_connection()
        df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[sheet_name], ttl=2)
        
        # Si está vacío o le faltan columnas clave, reinicializar
        if df.empty or (expected_columns and not all(col in df.columns for col in expected_columns)):
            initialize_sheets()
            df = conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[sheet_name], ttl=2)
        return df
    except:
        # En caso de error crítico, intentar reinicializar
        try:
            initialize_sheets()
            return conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[sheet_name], ttl=2)
        except:
            return pd.DataFrame(columns=expected_columns if expected_columns else [])

def load_brackets():
    return safe_load_df("brackets", ["Category", "Match_ID", "P1_Name"])

def load_inscriptions():
    return safe_load_df("inscriptions", ["ID", "Nombre_Completo", "Categoria"])

def load_config():
    return safe_load_df("config", ["setting", "value"])

def save_data(df, sheet_name):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[sheet_name], data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

# --- 9. GESTIÓN DEL TORNEO ---
def get_config_val(key):
    df = load_config()
    if not df.empty and 'setting' in df.columns:
        row = df[df['setting'] == key]
        if not row.empty:
            return row.iloc[0]['value']
    return "inscription" if key == "tournament_stage" else "true"

def set_config_val(key, val):
    df = load_config()
    if not df.empty:
        df.loc[df['setting'] == key, 'value'] = str(val)
        save_data(df, "config")

def generate_brackets_logic():
    """Genera los emparejamientos aleatorios."""
    insc_df = load_inscriptions()
    brackets_df = load_brackets()
    
    if insc_df.empty or brackets_df.empty:
        return
        
    for cat in ALL_CATEGORIES:
        # Obtener participantes activos
        parts = insc_df[
            (insc_df['Categoria'] == cat) & 
            (insc_df['Estado'] == 'Inscrito')
        ].to_dict('records')
        
        random.shuffle(parts)
        
        # Llenar Q1-Q4
        matches = ['Q1', 'Q2', 'Q3', 'Q4']
        for i, mid in enumerate(matches):
            mask = (brackets_df['Category'] == cat) & (brackets_df['Match_ID'] == mid)
            
            p1 = parts.pop(0) if parts else None
            p2 = parts.pop(0) if parts else None
            
            if p1:
                brackets_df.loc[mask, 'P1_Name'] = p1['Nombre_Completo']
                brackets_df.loc[mask, 'P1_Dojo'] = p1['Dojo']
                insc_df.loc[insc_df['ID'] == p1['ID'], 'Estado'] = 'Emparejado'
                
                if p2:
                    brackets_df.loc[mask, 'P2_Name'] = p2['Nombre_Completo']
                    brackets_df.loc[mask, 'P2_Dojo'] = p2['Dojo']
                    insc_df.loc[insc_df['ID'] == p2['ID'], 'Estado'] = 'Emparejado'
                else:
                    # BYE Logic
                    brackets_df.loc[mask, 'P2_Name'] = "BYE (Pasa Directo)"
                    brackets_df.loc[mask, 'Winner'] = p1['Nombre_Completo']
                    
                    # Avanzar a semis
                    next_round = 'S1' if mid in ['Q1', 'Q2'] else 'S2'
                    spot = 'P1' if mid in ['Q1', 'Q3'] else 'P2'
                    s_mask = (brackets_df['Category'] == cat) & (brackets_df['Match_ID'] == next_round)
                    brackets_df.loc[s_mask, f'{spot}_Name'] = p1['Nombre_Completo']
                    brackets_df.loc[s_mask, f'{spot}_Dojo'] = p1['Dojo']

    save_data(brackets_df, "brackets")
    save_data(insc_df, "inscriptions")
    set_config_val("tournament_stage", "competition")
    set_config_val("registration_open", "false")

def reset_all_data():
    """Resetea todo el sistema."""
    initialize_sheets()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.cache_data.clear()

# --- 10. VISTAS ---
def render_header():
    stage = get_config_val("tournament_stage")
    txt = "INSCRIPCIONES ABIERTAS" if stage == "inscription" else "COMPETENCIA EN CURSO"
    cls = "stage-open" if stage == "inscription" else "stage-closed"
    
    st.markdown(f"""
    <div class="header-container">
        <div>
            <h2 style="margin:0; color:white;">WKB CHILE <span class="stage-badge {cls}">{txt}</span></h2>
            <small style="color:#FDB931;">OFFICIAL TOURNAMENT HUB</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_inscription():
    if get_config_val("registration_open") == "false":
        st.warning("⚠️ Inscripciones cerradas.")
        if st.button("Ver Brackets"):
            st.session_state.view = "HOME"
            st.rerun()
        return

    with st.form("reg_form"):
        st.subheader("📝 Nueva Inscripción")
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        dojo = c2.text_input("Dojo")
        cat = st.selectbox("Categoría", ALL_CATEGORIES)
        
        if st.form_submit_button("Registrar"):
            if nombre and dojo:
                new_data = pd.DataFrame([{
                    "ID": str(uuid.uuid4())[:8],
                    "Nombre_Completo": nombre,
                    "Dojo": dojo,
                    "Categoria": cat,
                    "Estado": "Inscrito",
                    "Fecha_Inscripcion": str(datetime.datetime.now())
                }])
                current = load_inscriptions()
                # Asegurar columnas correctas
                if current.empty: 
                    current = new_data
                else:
                    current = pd.concat([current, new_data], ignore_index=True)
                
                save_data(current, "inscriptions")
                st.success("✅ Inscrito correctamente")
            else:
                st.error("Faltan datos")

def render_bracket_view():
    cat = st.session_state.cat
    brackets = load_brackets()
    
    # Check de seguridad
    if brackets.empty:
        st.info("Inicializando sistema...")
        initialize_sheets()
        st.rerun()
        return

    cat_df = brackets[brackets['Category'] == cat].set_index('Match_ID')
    
    render_header()
    
    c1, c2 = st.columns([1, 4])
    if c1.button("🏠 INICIO"):
        st.session_state.view = "HOME"
        st.rerun()
    c2.markdown(f"### {cat}")

    # Helpers de renderizado
    def get_val(mid, col):
        try: return cat_df.loc[mid, col] if pd.notna(cat_df.loc[mid, col]) else ""
        except: return ""

    def render_player(mid, p, color):
        name = get_val(mid, f'{p}_Name')
        if not name: name = "..."
        dojo = get_val(mid, f'{p}_Dojo')
        
        try:
            v = int(get_val(mid, f'{p}_Votes') or 0)
            ov = int(get_val(mid, f'P2_Votes' if p=='P1' else 'P1_Votes') or 0)
            tot = v + ov
            pct = int((v/tot)*100) if tot > 0 else 0
        except:
            v, pct = 0, 0
            
        return f"""
        <div class="player-box {color}">
            <div class="p-name">{name}</div>
            <div class="p-details"><span>{dojo}</span><span>{pct}% ({v})</span></div>
            <div class="p-vote-bar"><div class="p-vote-fill" style="width:{pct}%; background:{'#ef4444' if p=='P1' else 'white'}"></div></div>
            <div class="line-r"></div>
        </div>
        """

    # HTML Bracket
    st.markdown(f"""
    <div class="bracket-container">
        <div class="rounds-wrapper">
            <div class="round">
                <div class="round-title">CUARTOS</div>
                {render_player('Q1', 'P1', 'border-red')}
                {render_player('Q1', 'P2', 'border-white')}
                <div style="height:40px; position:relative;"><div class="conn-v" style="height:80px; top:-40px;"></div></div>
                {render_player('Q2', 'P1', 'border-red')}
                {render_player('Q2', 'P2', 'border-white')}
                <div style="height:40px; position:relative;"><div class="conn-v" style="height:80px; top:-40px;"></div></div>
                {render_player('Q3', 'P1', 'border-red')}
                {render_player('Q3', 'P2', 'border-white')}
                <div style="height:40px; position:relative;"><div class="conn-v" style="height:80px; top:-40px;"></div></div>
                {render_player('Q4', 'P1', 'border-red')}
                {render_player('Q4', 'P2', 'border-white')}
            </div>
            <div class="round">
                <div class="round-title">SEMIS</div>
                <div style="height:50%; position:relative; margin-top:20px;">
                    <div class="conn-v" style="height:120px; top:50%; transform:translateY(-50%);"></div>
                    {render_player('S1', 'P1', 'border-red')}
                    {render_player('S1', 'P2', 'border-white')}
                </div>
                <div style="height:50%; position:relative; margin-top:40px;">
                    <div class="conn-v" style="height:120px; top:50%; transform:translateY(-50%);"></div>
                    {render_player('S2', 'P1', 'border-red')}
                    {render_player('S2', 'P2', 'border-white')}
                </div>
            </div>
            <div class="round">
                <div class="round-title">FINAL</div>
                <div style="height:100%; position:relative;">
                    <div class="conn-v" style="height:160px; top:50%; transform:translateY(-50%);"></div>
                    {render_player('F1', 'P1', 'border-red')}
                    {render_player('F1', 'P2', 'border-white')}
                </div>
            </div>
            <div class="round">
                <div class="round-title">CAMPEÓN</div>
                <div style="height:100%; display:flex; align-items:center;">
                    <div class="champion-box">{get_val('F1', 'Winner') or '🏆'}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Votación
    st.subheader("🗳️ Votación en Vivo")
    cols = st.columns(4)
    matches = ['Q1', 'Q2', 'Q3', 'Q4']
    for i, mid in enumerate(matches):
        p1 = get_val(mid, 'P1_Name')
        p2 = get_val(mid, 'P2_Name')
        if p1 and p2 and "BYE" not in p2:
            with cols[i]:
                st.caption(f"Match {mid}")
                if st.button(f"🔴 {p1}", key=f"v1_{mid}"):
                    idx = brackets[(brackets['Category']==cat) & (brackets['Match_ID']==mid)].index[0]
                    brackets.at[idx, 'P1_Votes'] = int(brackets.at[idx, 'P1_Votes'] or 0) + 1
                    save_data(brackets, "brackets")
                    st.rerun()
                if st.button(f"⚪ {p2}", key=f"v2_{mid}"):
                    idx = brackets[(brackets['Category']==cat) & (brackets['Match_ID']==mid)].index[0]
                    brackets.at[idx, 'P2_Votes'] = int(brackets.at[idx, 'P2_Votes'] or 0) + 1
                    save_data(brackets, "brackets")
                    st.rerun()

# --- 11. MAIN APP ---
def main():
    if 'view' not in st.session_state: st.session_state.view = "HOME"
    if 'is_admin' not in st.session_state: st.session_state.is_admin = False
    
    # Auto-reparación inicial
    if load_config().empty:
        initialize_sheets()

    if st.session_state.view == "HOME":
        render_header()
        
        tab1, tab2, tab3 = st.tabs(["Categorías", "Inscripción", "Admin"])
        
        with tab1:
            for cat in ALL_CATEGORIES:
                if st.button(cat, key=cat):
                    st.session_state.view = "BRACKET"
                    st.session_state.cat = cat
                    st.rerun()
        
        with tab2:
            render_inscription()
            
        with tab3:
            if not st.session_state.is_admin:
                pwd = st.text_input("Password", type="password")
                if st.button("Login"):
                    if check_admin(pwd):
                        st.session_state.is_admin = True
                        st.rerun()
            else:
                st.success("Admin Logueado")
                if get_config_val("tournament_stage") == "inscription":
                    if st.button("🔒 CERRAR Y SORTEAR", type="primary"):
                        generate_brackets_logic()
                        st.success("Brackets generados!")
                        time.sleep(2)
                        st.rerun()
                
                if st.button("🚨 RESET TOTAL"):
                    reset_all_data()
                    st.rerun()
                    
    elif st.session_state.view == "BRACKET":
        render_bracket_view()

if __name__ == "__main__":
    main()
