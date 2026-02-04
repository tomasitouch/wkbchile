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
import math

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Official Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">', unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN DE HOJAS GOOGLE SHEETS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
SHEET_NAMES = {
    "brackets": "Brackets",
    "inscriptions": "Inscripciones",
    "config": "Configuracion",
    "payments": "Pagos"
}

# --- 3. CREDENCIALES MERCADO PAGO ---
MP_PUBLIC_KEY = st.secrets["mercadopago"]["public_key"]
MP_ACCESS_TOKEN = st.secrets["mercadopago"]["access_token"]

def init_mercadopago():
    try:
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        return sdk
    except Exception as e:
        st.error("Error inicializando Mercado Pago: " + str(e))
        return None

# --- 4. SEGURIDAD ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 5. ESTILOS CSS MEJORADOS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #0e1117; color: white; font-family: 'Inter', sans-serif !important; }
    h1, h2, h3, h4 { font-family: 'Roboto Condensed', sans-serif !important; text-transform: uppercase; }
    
    .header-container { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 20px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;
    }
    
    .sponsor-logo { height: 40px; filter: grayscale(20%); transition: 0.3s; }
    .sponsor-logo:hover { filter: grayscale(0%); transform: scale(1.05); }

    /* Brackets dinámicos */
    .bracket-wrapper { display: flex; flex-direction: row; padding: 20px; overflow-x: auto; gap: 0; align-items: center; }
    .bracket-round { display: flex; flex-direction: column; justify-content: space-around; width: 220px; flex-shrink: 0; min-height: 500px; }
    .bracket-match { display: flex; flex-direction: column; margin: 15px 0; position: relative; padding: 10px 0; }
    .bracket-player { 
        background: #1f2937; border: 1px solid #374151; padding: 10px; width: 180px; 
        font-size: 12px; color: #e5e7eb; position: relative;
    }
    .bracket-player.top { border-radius: 4px 4px 0 0; border-bottom: none; }
    .bracket-player.bottom { border-radius: 0 0 4px 4px; }
    .bracket-player.winner { border-color: #FDB931; color: #FDB931; font-weight: bold; }
    .player-dojo { font-size: 9px; color: #9ca3af; display: block; text-transform: uppercase; }
    .round-header { text-align: center; color: #FDB931; font-weight: bold; margin-bottom: 15px; font-size: 14px; }

    .mercado-pago-btn {
        background: linear-gradient(135deg, #00B1EA, #009EE3); color: white; border: none;
        padding: 18px; font-size: 16px; font-weight: bold; border-radius: 8px; width: 100%; cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# --- 6. CONFIGURACIÓN DEL TORNEO ---
CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATEGORIES = [g + " | " + s for g, s in CATEGORIES_CONFIG.items() for s in s]

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

# --- 7. CONEXIÓN Y DATOS ---
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=15)
def load_brackets():
    try: return get_connection().read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], ttl=15)
    except: return pd.DataFrame()

@st.cache_data(ttl=15)
def load_inscriptions():
    try: return get_connection().read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], ttl=15)
    except: return pd.DataFrame()

@st.cache_data(ttl=15)
def load_config():
    try: return get_connection().read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], ttl=15)
    except: return pd.DataFrame(columns=["setting", "value", "description"])

def save_inscriptions(df):
    get_connection().update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=df)
    st.cache_data.clear()

def save_brackets(df):
    get_connection().update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=df)
    st.cache_data.clear()

def save_config(df):
    get_connection().update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=df)
    st.cache_data.clear()

# --- 8. FUNCIONES DE GESTIÓN ---
def get_tournament_stage():
    config_df = load_config()
    if config_df.empty: return "inscription"
    res = config_df[config_df['setting'] == 'tournament_stage']
    return res.iloc[0]['value'] if not res.empty else "inscription"

def is_registration_open():
    config_df = load_config()
    if config_df.empty: return True
    res = config_df[config_df['setting'] == 'registration_open']
    return str(res.iloc[0]['value']).lower() == 'true' if not res.empty else True

# --- 9. UTILIDADES Y HEADERS ---
def render_header():
    org_img = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-PCwsXVnqhlX-vNev8BDqbszitBpm3cC8GQ&s"
    sp1 = "https://scontent-scl3-1.cdninstagram.com/v/t51.2885-19/531710545_17844263151552626_3122797905502597978_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-scl3-1.cdninstagram.com&_nc_cat=102&_nc_oc=Q6cZ2QEti-3-IaLrWUfBpoWCCkBzz8U8hQ0sagf0iIkZLFTRsWS92shvGPLiqsqevgO0rL0&_nc_ohc=Jx0u8BGF6Y0Q7kNvwFp0z-D&_nc_gid=5pWUWepwuNN5pujdtMu7dg&edm=AP4sbd4BAAAA&ccb=7-5&oh=00_AfslihQ-4PF9QvV6Ogmi_M5B6WKMI62wyqv4zS8I-XYfNQ&oe=69896A53&_nc_sid=7a9f4b"
    sp2 = "https://inertiax.store/cdn/shop/files/wmremove-transformed-removebg-preview.png?v=1743950875&width=500"
    
    html = '<div class="header-container">'
    html += '<div class="header-title"><img src="' + org_img + '" style="height:60px; margin-right:15px;">'
    html += '<div><h1 style="margin:0; font-size:20px;">WKB Chile</h1><p style="margin:0; color:#FDB931; font-size:12px;">Official Hub</p></div></div>'
    html += '<div class="header-sponsors"><div>'
    html += '<img src="' + sp1 + '" class="sponsor-logo" style="margin-right:10px; border-radius:50%;">'
    html += '<img src="' + sp2 + '" class="sponsor-logo">'
    html += '</div></div></div>'
    st.markdown(html, unsafe_allow_html=True)

def generate_inscription_code():
    return "WKB" + datetime.datetime.now().strftime("%y%m%d%H%M") + "".join(random.choices(string.ascii_uppercase, k=4))

def calculate_price(count, type):
    return 50000 * count # Simplificado para el ejemplo

def confirm_inscription_manually(code):
    try:
        df = load_inscriptions()
        mask = df["Codigo_Pago"] == code
        if not df[mask].empty:
            df.loc[mask, "Estado_Pago"] = "Confirmado"
            df.loc[mask, "MP_Status"] = "approved"
            df.loc[mask, "Estado"] = "Inscrito"
            save_inscriptions(df)
            return True
        return False
    except: return False

# --- 10. LÓGICA DE BRACKETS DINÁMICOS ---
def generate_brackets_for_category(category):
    try:
        inscriptions_df = load_inscriptions()
        confirmed = inscriptions_df[(inscriptions_df['Categoria'] == category) & (inscriptions_df['Estado_Pago'] == 'Confirmado')].to_dict('records')
        n = len(confirmed)
        if n < 2: return False
        
        num_slots = 2**math.ceil(math.log2(n))
        random.shuffle(confirmed)
        
        participants = confirmed + [{"Nombre_Completo": "BYE", "ID": "BYE", "Dojo": ""}] * (num_slots - n)
        temp_brackets = []
        
        # Ronda 1
        num_matches = num_slots // 2
        for i in range(num_matches):
            p1, p2 = participants[i*2], participants[i*2 + 1]
            match = {
                "Category": category, "Match_ID": "R1-M" + str(i+1), "Round": "Ronda 1", "Match_Number": i + 1,
                "P1_Name": p1['Nombre_Completo'], "P1_ID": p1['ID'], "P1_Dojo": p1['Dojo'], "P1_Votes": 0,
                "P2_Name": p2['Nombre_Completo'], "P2_ID": p2['ID'], "P2_Dojo": p2['Dojo'], "P2_Votes": 0,
                "Winner": "", "Winner_ID": "", "Live": False, "Status": "Scheduled"
            }
            if p2['ID'] == "BYE":
                match["Winner"] = p1['Nombre_Completo']
                match["Winner_ID"] = p1['ID']
                match["Status"] = "Walkover"
            temp_brackets.append(match)

        # Rondas subsiguientes
        round_idx = 2
        num_matches //= 2
        while num_matches >= 1:
            name = "Final" if num_matches == 1 else "Ronda " + str(round_idx)
            for i in range(num_matches):
                temp_brackets.append({
                    "Category": category, "Match_ID": "R" + str(round_idx) + "-M" + str(i+1),
                    "Round": name, "Match_Number": i + 1,
                    "P1_Name": "", "P1_ID": "", "P1_Dojo": "", "P1_Votes": 0,
                    "P2_Name": "", "P2_ID": "", "P2_Dojo": "", "P2_Votes": 0,
                    "Winner": "", "Winner_ID": "", "Live": False, "Status": "Pending"
                })
            num_matches //= 2
            round_idx += 1
            
        old_brackets = load_brackets()
        new_df = pd.concat([old_brackets[old_brackets['Category'] != category], pd.DataFrame(temp_brackets)], ignore_index=True)
        save_brackets(new_df)
        return True
    except: return False

# --- 11. VISTAS ---

def render_bracket_view():
    cat = st.session_state.cat
    render_header()
    st.markdown("### 🏆 LLAVES DE COMPETENCIA: " + str(cat))
    
    df = load_brackets()
    cat_df = df[df['Category'] == cat]
    if cat_df.empty:
        st.info("Brackets no generados.")
    else:
        rounds = cat_df['Round'].unique()
        html = '<div class="bracket-wrapper">'
        for r in rounds:
            matches = cat_df[cat_df['Round'] == r].sort_values('Match_Number')
            html += '<div class="bracket-round"><div class="round-header">' + r.upper() + '</div>'
            for _, m in matches.iterrows():
                win1 = "winner" if m['Winner_ID'] == m['P1_ID'] and m['P1_ID'] != "" else ""
                win2 = "winner" if m['Winner_ID'] == m['P2_ID'] and m['P2_ID'] != "" else ""
                html += '<div class="bracket-match">'
                html += '<div class="bracket-player top ' + win1 + '">' + str(m["P1_Name"] or "TBD") + '<br><span class="player-dojo">' + str(m["P1_Dojo"]) + '</span></div>'
                html += '<div class="bracket-player bottom ' + win2 + '">' + str(m["P2_Name"] or "TBD") + '<br><span class="player-dojo">' + str(m["P2_Dojo"]) + '</span></div>'
                html += '</div>'
            html += '</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        
    if st.button("🏠 INICIO"):
        st.session_state.view = "HOME"
        st.rerun()

def show_payment_section():
    render_header()
    st.markdown("#### 💳 PAGO")
    
    count = 1 if st.session_state.inscription_type == "individual" else len(st.session_state.group_participants)
    total = count * 50000
    
    st.info("### RESUMEN\n**Total a pagar: $" + str(total) + " CLP**")
    
    if not st.session_state.inscription_code:
        st.session_state.inscription_code = generate_inscription_code()
        plist = [st.session_state.current_participant] if st.session_state.inscription_type == "individual" else st.session_state.group_participants
        save_participants_temporarily(plist, st.session_state.inscription_type, st.session_state.inscription_code)

    payment_url = "https://www.mercadopago.cl" # Placeholder
    btn_html = '<a href="' + payment_url + '" target="_blank">'
    btn_html += '<button class="mercado-pago-btn">💳 PAGAR CON MERCADO PAGO</button></a>'
    st.markdown(btn_html, unsafe_allow_html=True)
    
    st.markdown("---")
    with st.expander("🛠️ DESARROLLADOR"):
        if st.button("✅ CONFIRMAR MANUALMENTE", use_container_width=True):
            if confirm_inscription_manually(st.session_state.inscription_code):
                st.session_state.payment_processed = True
                st.session_state.payment_status = "success"
                st.rerun()

def show_payment_success():
    render_header()
    st.balloons()
    st.success("# ¡PAGO EXITOSO!")
    st.info("**CÓDIGO:** " + str(st.session_state.inscription_code))
    if st.button("🏠 INICIO"):
        st.session_state.view = "HOME"
        st.session_state.payment_processed = False
        st.rerun()

# --- 12. FLUJO PRINCIPAL ---

def render_home_view():
    render_header()
    tournament_stage = get_tournament_stage()
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 CATEGORÍAS", "📝 INSCRIBIRSE", "👥 INSCRITOS", "⚙️ ADMIN"])
    
    with tab1:
        for cat in ALL_CATEGORIES:
            if st.button(cat.split(" | ")[-1], key="c"+cat, use_container_width=True):
                st.session_state.view = "BRACKET"
                st.session_state.cat = cat
                st.rerun()
    
    with tab2:
        if tournament_stage == "competition":
            st.warning("Inscripciones cerradas.")
        else:
            if st.button("📝 COMENZAR", type="primary", use_container_width=True):
                st.session_state.view = "INSCRIPTION"
                st.rerun()

    with tab4:
        if not st.session_state.get('is_admin', False):
            admin_pass = st.text_input("Pass", type="password")
            if st.button("Entrar"):
                if check_admin(admin_pass): 
                    st.session_state.is_admin = True
                    st.rerun()
        else:
            if st.button("Cerrar inscripciones y generar brackets"):
                for c in ALL_CATEGORIES: generate_brackets_for_category(c)
                st.success("Brackets generados.")

def main():
    if 'view' not in st.session_state: st.session_state.view = "HOME"
    if 'payment_processed' not in st.session_state: st.session_state.payment_processed = False
    
    if st.session_state.payment_processed: show_payment_success()
    elif st.session_state.view == "HOME": render_home_view()
    elif st.session_state.view == "INSCRIPTION": 
        if st.session_state.get('inscription_step', 1) == 3: show_payment_section()
        else: render_inscription_view() # Asumiendo que esta función existe en tu código original
    elif st.session_state.view == "BRACKET": render_bracket_view()

if __name__ == "__main__":
    main()
