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

# Meta tags para móviles
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
""", unsafe_allow_html=True)

# --- 2. CONSTANTES Y CONFIGURACIÓN ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
ADMIN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9" # pass: wkbadmin123

SHEET_NAMES = {
    "brackets": "Brackets",
    "inscriptions": "Inscripciones",
    "config": "Configuracion",
    "votes": "Votos"
}

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATEGORIES = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

# --- 3. ESTILOS CSS (DISEÑO HORIZONTAL Y MODERNO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #0e1117; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Roboto Condensed', sans-serif; text-transform: uppercase; }
    
    /* Header */
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        padding: 15px 20px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%);
        border-bottom: 1px solid #374151; margin-bottom: 20px; flex-wrap: wrap;
    }
    
    /* Bracket Container Horizontal */
    .bracket-container { 
        overflow-x: auto; padding: 20px 10px; display: flex; 
        justify-content: center; min-height: 500px;
    }
    .rounds-wrapper { display: flex; gap: 40px; min-width: min-content; }
    .round { display: flex; flex-direction: column; justify-content: space-around; min-width: 260px; }
    
    /* Player Box */
    .player-box { 
        background: linear-gradient(145deg, #1f2937, #111827); padding: 10px; margin: 10px 0;
        border-radius: 8px; border: 1px solid #374151; position: relative; z-index: 2;
        min-height: 70px; display: flex; flex-direction: column; justify-content: center;
    }
    .border-red { border-left: 5px solid #ef4444; }
    .border-white { border-left: 5px solid #ffffff; }
    
    .p-name { font-weight: bold; font-size: 14px; color: white; }
    .p-details { font-size: 11px; color: #9ca3af; display: flex; justify-content: space-between; }
    
    /* Conectores Visuales del Bracket */
    .line-r { position: absolute; right: -42px; width: 42px; height: 2px; background: #6b7280; top: 50%; }
    .conn-v { position: absolute; right: -42px; width: 2px; background: #6b7280; top: 50%; transform: translateY(-50%); }
    
    /* Botones */
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    
    /* Badges */
    .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .open { background: #10B981; color: white; }
    .closed { background: #EF4444; color: white; }
    
    /* Champion Box */
    .champion-box {
        background: linear-gradient(135deg, #FDB931, #d9a024); color: black;
        padding: 20px; border-radius: 10px; text-align: center; font-weight: bold;
        box-shadow: 0 0 15px rgba(253, 185, 49, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- 4. GESTIÓN DE DATOS (BACKEND) ---

@st.cache_resource
def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_HASH

def initialize_sheets():
    """Crea la estructura base vacía en Google Sheets"""
    conn = get_conn()
    
    # 1. Brackets (Estructura fija para todas las categorías)
    brackets_data = []
    for cat in ALL_CATEGORIES:
        # Creamos los placeholders para Cuartos (Q), Semis (S) y Final (F)
        for i in range(1, 5): # Q1-Q4
            brackets_data.append({"Category": cat, "Match_ID": f"Q{i}", "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": "", "Live": False})
        for i in range(1, 3): # S1-S2
            brackets_data.append({"Category": cat, "Match_ID": f"S{i}", "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": "", "Live": False})
        # F1
        brackets_data.append({"Category": cat, "Match_ID": "F1", "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": "", "Live": False})

    brackets_df = pd.DataFrame(brackets_data)
    
    # 2. Inscripciones (Vacía)
    inscriptions_df = pd.DataFrame(columns=[
        "ID", "Nombre_Completo", "Dojo", "Categoria", "Tipo_Inscripcion", 
        "Estado_Pago", "Fecha_Inscripcion", "Estado" # Estado: Inscrito, Emparejado, Eliminado
    ])
    
    # 3. Configuración (Estado inicial)
    config_df = pd.DataFrame([
        {"setting": "tournament_stage", "value": "inscription"}, # inscription / competition
        {"setting": "registration_open", "value": "true"}
    ])
    
    # 4. Votos (Vacía)
    votes_df = pd.DataFrame(columns=["match_id", "category", "vote_for", "timestamp"])

    try:
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["brackets"], data=brackets_df)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["inscriptions"], data=inscriptions_df)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["config"], data=config_df)
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES["votes"], data=votes_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error inicializando sheets: {e}")
        return False

# Carga de datos con caché
def load_data(sheet_name):
    conn = get_conn()
    try:
        return conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[sheet_name], ttl=5)
    except:
        return pd.DataFrame()

def save_data(df, sheet_name):
    conn = get_conn()
    conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[sheet_name], data=df)
    st.cache_data.clear()

# --- 5. LÓGICA DEL TORNEO ---

def get_config_value(key):
    df = load_data("config")
    if not df.empty:
        row = df[df['setting'] == key]
        if not row.empty:
            return row.iloc[0]['value']
    return None

def set_config_value(key, value):
    df = load_data("config")
    if not df.empty:
        df.loc[df['setting'] == key, 'value'] = str(value)
        save_data(df, "config")

def generate_brackets_logic():
    """Lógica principal: Convierte lista de inscritos en llaves"""
    insc_df = load_data("inscriptions")
    brackets_df = load_data("brackets")
    
    # Iterar por cada categoría
    for cat in ALL_CATEGORIES:
        # Obtener atletas confirmados de la categoría
        participants = insc_df[
            (insc_df['Categoria'] == cat) & 
            (insc_df['Estado'] == 'Inscrito')
        ].to_dict('records')
        
        # Mezclar aleatoriamente
        random.shuffle(participants)
        
        # Llenar Brackets (Q1, Q2, Q3, Q4)
        # Tomamos pares. Si sobra uno, el ultimo tiene "BYE"
        
        match_slots = ['Q1', 'Q2', 'Q3', 'Q4']
        
        for i, match_id in enumerate(match_slots):
            # Encontrar la fila en brackets_df
            mask = (brackets_df['Category'] == cat) & (brackets_df['Match_ID'] == match_id)
            
            p1 = participants.pop(0) if participants else None
            p2 = participants.pop(0) if participants else None
            
            if p1:
                brackets_df.loc[mask, 'P1_Name'] = p1['Nombre_Completo']
                brackets_df.loc[mask, 'P1_Dojo'] = p1['Dojo']
                # Actualizar estado del atleta
                insc_df.loc[insc_df['ID'] == p1['ID'], 'Estado'] = 'Emparejado'
                
                if p2:
                    brackets_df.loc[mask, 'P2_Name'] = p2['Nombre_Completo']
                    brackets_df.loc[mask, 'P2_Dojo'] = p2['Dojo']
                    insc_df.loc[insc_df['ID'] == p2['ID'], 'Estado'] = 'Emparejado'
                else:
                    # BYE - Pasa directo
                    brackets_df.loc[mask, 'P2_Name'] = "BYE (Pasa Directo)"
                    brackets_df.loc[mask, 'P2_Dojo'] = "-"
                    brackets_df.loc[mask, 'Winner'] = p1['Nombre_Completo'] # Gana automáticamente
                    
                    # Mover a S1 o S2 automáticamente
                    target_semi = 'S1' if match_id in ['Q1', 'Q2'] else 'S2'
                    target_spot = 'P1' if match_id in ['Q1', 'Q3'] else 'P2'
                    
                    s_mask = (brackets_df['Category'] == cat) & (brackets_df['Match_ID'] == target_semi)
                    brackets_df.loc[s_mask, f'{target_spot}_Name'] = p1['Nombre_Completo']
                    brackets_df.loc[s_mask, f'{target_spot}_Dojo'] = p1['Dojo']

    save_data(brackets_df, "brackets")
    save_data(insc_df, "inscriptions")
    set_config_value("tournament_stage", "competition")
    set_config_value("registration_open", "false")

# --- 6. VISTAS (FRONTEND) ---

def render_header():
    stage = get_config_value("tournament_stage")
    status_text = "INSCRIPCIONES ABIERTAS" if stage == "inscription" else "COMPETENCIA EN CURSO"
    status_class = "open" if stage == "inscription" else "closed"
    
    st.markdown(f"""
    <div class="header-container">
        <div>
            <h2 style="color:white; margin:0;">WKB CHILE 2024</h2>
            <span class="status-badge {status_class}">{status_text}</span>
        </div>
        <div style="text-align:right;">
            <small style="color:#FDB931;">OFFICIAL HUB</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_inscription():
    if get_config_value("registration_open") == "false":
        st.warning("⚠️ Las inscripciones están cerradas. El torneo ha comenzado.")
        if st.button("Ir a Brackets"):
            st.session_state.view = "HOME"
            st.rerun()
        return

    st.subheader("📝 Formulario de Inscripción")
    
    with st.form("inscription_form"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre Completo")
        dojo = col2.text_input("Dojo")
        cat = st.selectbox("Categoría", ALL_CATEGORIES)
        tipo = st.radio("Tipo", ["Individual ($50.000)", "Colectiva (Desc. Grupal)"], horizontal=True)
        
        if st.form_submit_button("Registrarse"):
            if nombre and dojo:
                new_data = pd.DataFrame([{
                    "ID": str(uuid.uuid4())[:8],
                    "Nombre_Completo": nombre,
                    "Dojo": dojo,
                    "Categoria": cat,
                    "Tipo_Inscripcion": tipo,
                    "Estado_Pago": "Pendiente",
                    "Fecha_Inscripcion": str(datetime.datetime.now()),
                    "Estado": "Inscrito"
                }])
                
                current_df = load_data("inscriptions")
                updated_df = pd.concat([current_df, new_data], ignore_index=True)
                save_data(updated_df, "inscriptions")
                st.success(f"✅ {nombre} inscrito correctamente en {cat}")
            else:
                st.error("Faltan datos")

def render_bracket_visual(cat):
    brackets = load_data("brackets")
    cat_data = brackets[brackets['Category'] == cat].set_index('Match_ID')
    
    def get_val(mid, col):
        try:
            val = cat_data.loc[mid, col]
            return val if pd.notna(val) else ""
        except:
            return ""

    def render_player(mid, p_type, border):
        name = get_val(mid, f'{p_type}_Name')
        dojo = get_val(mid, f'{p_type}_Dojo')
        votes = float(get_val(mid, f'{p_type}_Votes') or 0)
        
        # Calcular porcentaje
        opp_type = 'P2' if p_type == 'P1' else 'P1'
        opp_votes = float(get_val(mid, f'{opp_type}_Votes') or 0)
        total = votes + opp_votes
        pct = int((votes / total * 100)) if total > 0 else 0
        
        if not name: name = "..."
        if name == "BYE (Pasa Directo)": border = "border-white"

        return f"""
        <div class="player-box {border}">
            <div class="p-name">{name}</div>
            <div class="p-details">
                <span>{dojo}</span>
                <span>{pct}% ({int(votes)})</span>
            </div>
            <div style="height:4px; background:#374151; margin-top:5px; border-radius:2px;">
                <div style="width:{pct}%; height:100%; background:{'#ef4444' if p_type=='P1' else 'white'};"></div>
            </div>
            <div class="line-r"></div>
        </div>
        """

    # HTML Structure
    html = f"""
    <div class="bracket-container">
        <div class="rounds-wrapper">
            <div class="round">
                <div style="text-align:center; color:#FDB931; font-weight:bold; margin-bottom:10px;">CUARTOS</div>
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
                <div style="text-align:center; color:#FDB931; font-weight:bold; margin-bottom:10px;">SEMIFINAL</div>
                <div style="height:50%; display:flex; flex-direction:column; justify-content:center; position:relative;">
                     <div class="conn-v" style="height:140px; top:50%; transform:translateY(-50%);"></div>
                     {render_player('S1', 'P1', 'border-red')}
                     {render_player('S1', 'P2', 'border-white')}
                </div>
                <div style="height:50%; display:flex; flex-direction:column; justify-content:center; position:relative;">
                     <div class="conn-v" style="height:140px; top:50%; transform:translateY(-50%);"></div>
                     {render_player('S2', 'P1', 'border-red')}
                     {render_player('S2', 'P2', 'border-white')}
                </div>
            </div>

            <div class="round">
                <div style="text-align:center; color:#FDB931; font-weight:bold; margin-bottom:10px;">FINAL</div>
                <div style="height:100%; display:flex; flex-direction:column; justify-content:center; position:relative;">
                     <div class="conn-v" style="height:180px; top:50%; transform:translateY(-50%);"></div>
                     {render_player('F1', 'P1', 'border-red')}
                     {render_player('F1', 'P2', 'border-white')}
                </div>
            </div>

            <div class="round">
                <div style="text-align:center; color:#FDB931; font-weight:bold; margin-bottom:10px;">CAMPEÓN</div>
                <div style="height:100%; display:flex; align-items:center;">
                    <div class="champion-box">
                        {get_val('F1', 'Winner') if get_val('F1', 'Winner') else "🏆"}
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    st.html(html)

    # Lógica de Votación
    st.subheader("🗳️ Vota por tu favorito")
    col1, col2, col3, col4 = st.columns(4)
    matches = ['Q1', 'Q2', 'Q3', 'Q4']
    
    for i, mid in enumerate(matches):
        p1 = get_val(mid, 'P1_Name')
        p2 = get_val(mid, 'P2_Name')
        
        if p1 and p2 and p2 != "BYE (Pasa Directo)" and not get_val(mid, 'Winner'):
            with [col1, col2, col3, col4][i]:
                st.markdown(f"**{mid}**")
                if st.button(f"🔴 {p1}", key=f"vote_p1_{mid}"):
                    # Incrementar voto P1
                    idx = brackets[(brackets['Category'] == cat) & (brackets['Match_ID'] == mid)].index[0]
                    brackets.at[idx, 'P1_Votes'] += 1
                    save_data(brackets, "brackets")
                    st.toast("Voto registrado!")
                    st.rerun()
                if st.button(f"⚪ {p2}", key=f"vote_p2_{mid}"):
                    # Incrementar voto P2
                    idx = brackets[(brackets['Category'] == cat) & (brackets['Match_ID'] == mid)].index[0]
                    brackets.at[idx, 'P2_Votes'] += 1
                    save_data(brackets, "brackets")
                    st.toast("Voto registrado!")
                    st.rerun()

# --- 7. APP PRINCIPAL ---

def main():
    # Inicializar estado
    if 'view' not in st.session_state: st.session_state.view = "HOME"
    if 'is_admin' not in st.session_state: st.session_state.is_admin = False
    
    # Intentar cargar config, si falla, inicializar sheets
    try:
        if load_data("config").empty:
            initialize_sheets()
    except:
        initialize_sheets()

    render_header()
    
    # Navegación Sidebar Admin
    with st.sidebar:
        st.header("⚙️ Admin")
        if not st.session_state.is_admin:
            pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                if check_admin(pwd):
                    st.session_state.is_admin = True
                    st.rerun()
        else:
            if st.button("Logout"):
                st.session_state.is_admin = False
                st.rerun()
                
            st.divider()
            
            # CONTROL DE ETAPAS
            current_stage = get_config_value("tournament_stage")
            
            if current_stage == "inscription":
                st.info("Etapa: Inscripción")
                if st.button("🔒 CERRAR INSCRIPCIONES Y SORTEAR LLAVES", type="primary"):
                    with st.spinner("Generando llaves aleatorias..."):
                        generate_brackets_logic()
                        st.success("¡Brackets Generados!")
                        time.sleep(2)
                        st.rerun()
            else:
                st.success("Etapa: Competencia")
                if st.button("🔙 Volver a abrir inscripciones"):
                    set_config_value("tournament_stage", "inscription")
                    set_config_value("registration_open", "true")
                    st.rerun()
            
            st.divider()
            # RESET TOTAL
            if st.button("🚨 RESET TOTAL (Borrar Todo)"):
                initialize_sheets()
                st.warning("Sistema reiniciado a cero.")
                time.sleep(1)
                st.rerun()

    # Navegación Principal
    tab1, tab2, tab3 = st.tabs(["🏆 Categorías y Brackets", "📝 Inscripciones", "👥 Lista de Inscritos"])
    
    with tab1:
        if get_config_value("tournament_stage") == "inscription":
            st.info("El torneo aún está en fase de inscripción. Las llaves se generarán al cierre.")
            st.image("https://www.wkbofficial.com/wp-content/uploads/2023/05/logo-wkb.png", width=100)
        else:
            cat = st.selectbox("Seleccionar Categoría", ALL_CATEGORIES)
            render_bracket_visual(cat)
            
    with tab2:
        render_inscription()
        
    with tab3:
        insc_df = load_data("inscriptions")
        if not insc_df.empty:
            st.dataframe(insc_df[["Nombre_Completo", "Dojo", "Categoria", "Estado"]])
        else:
            st.write("No hay inscritos aún.")

if __name__ == "__main__":
    main()
