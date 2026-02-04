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

# --- 3. ESTILOS CSS PRO (MANTENIDOS) ---
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
    
    /* BRACKET RESPONSIVE MEJORADO */
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
    .bracket-container::-webkit-scrollbar { height: 8px; }
    .bracket-container::-webkit-scrollbar-track { background: #1a202c; border-radius: 4px; }
    .bracket-container::-webkit-scrollbar-thumb { background: linear-gradient(90deg, #ef4444, #FDB931); border-radius: 4px; }
    
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
    
    .live-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #ef4444;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 1s infinite;
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
    
    /* MEDIA QUERIES PARA ADAPTACIÓN */
    @media (max-width: 1024px) {
        .header-container { flex-direction: column; text-align: center; padding: 15px; gap: 20px; }
        .header-title, .header-sponsors { align-items: center; text-align: center; width: 100%; }
        .sponsor-logos { justify-content: center; }
        .bracket-container { min-height: 450px; padding: 15px 5px; }
        .round { min-width: 260px; max-width: 280px; padding: 12px; }
    }
    
    @media (max-width: 480px) {
        .header-container { padding: 12px; }
        .header-title img { height: 40px; }
        .bracket-container { min-height: 350px; padding: 10px 5px; }
        .round { min-width: 200px; max-width: 220px; padding: 8px; }
        .player-box { min-height: 65px; padding: 8px; margin: 6px 0; }
        .p-name { font-size: 12px; }
        .line-r { right: -20px; width: 20px; }
        .conn-v { right: -20px; }
    }
    
    .responsive-text-md { font-size: clamp(14px, 1.8vw, 18px) !important; }
    .responsive-text-sm { font-size: clamp(12px, 1.2vw, 14px) !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. GESTIÓN DE DATOS ---

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

KARATE_GRADES = {
    "1": "Blanco (10º Kyu)", "2": "Amarillo (9º Kyu)", "3": "Naranja (8º Kyu)",
    "4": "Verde (7º Kyu)", "5": "Azul (6º Kyu)", "6": "Violeta (5º Kyu)",
    "7": "Marrón (4º-1º Kyu)", "8": "Negro (1º-3º Dan)", "9": "Negro (4º-6º Dan)",
    "10": "Negro (7º-10º Dan)"
}

class RateLimiter:
    def __init__(self, max_requests=3, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def allow_request(self, user_id, match_id):
        now = datetime.datetime.now()
        key = f"{user_id}_{match_id}"
        if key not in self.requests: self.requests[key] = []
        self.requests[key] = [req for req in self.requests[key] if now - req < timedelta(seconds=self.time_window)]
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
                "Winner": None, "Live": False
            })
    return pd.DataFrame(data)

@st.cache_data(ttl=30)
def get_initial_inscriptions_df():
    return pd.DataFrame(columns=[
        "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", 
        "Dojo", "Organizacion", "Telefono", "Email", "Categoria", 
        "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64",
        "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID"
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

# --- FUNCIONES DE LÓGICA DE NEGOCIO ---
def perform_automatic_matchmaking(category):
    """
    Empareja automáticamente a los inscritos en una categoría basándose en similitud.
    Criterios: Peso (principal), Estatura (secundario), Grado (terciario).
    """
    global main_df, inscriptions_df
    
    # Filtrar inscritos por categoría
    candidates = inscriptions_df[inscriptions_df['Categoria'] == category].copy()
    
    if len(candidates) < 2:
        return False, "Se necesitan al menos 2 competidores para generar brackets."
    
    # Convertir columnas a numérico para ordenar
    candidates['Peso'] = pd.to_numeric(candidates['Peso'], errors='coerce')
    candidates['Estatura'] = pd.to_numeric(candidates['Estatura'], errors='coerce')
    candidates['Grado_Int'] = candidates['Grado'].astype(int)
    
    # ORDENAR POR SIMILITUD (Peso similar pelean entre sí)
    # Ordenamos por peso ascendente, luego estatura, luego grado.
    candidates = candidates.sort_values(by=['Peso', 'Estatura', 'Grado_Int'])
    
    # Limpiar el bracket actual de esta categoría
    idx_cat = main_df[main_df['Category'] == category].index
    for i in idx_cat:
        main_df.at[i, 'P1_Name'] = ""
        main_df.at[i, 'P1_Dojo'] = ""
        main_df.at[i, 'P1_Votes'] = 0
        main_df.at[i, 'P2_Name'] = ""
        main_df.at[i, 'P2_Dojo'] = ""
        main_df.at[i, 'P2_Votes'] = 0
        main_df.at[i, 'Winner'] = None
    
    # Llenar Q1, Q2, Q3, Q4 (Máximo 8 competidores para cuartos de final)
    matches = ['Q1', 'Q2', 'Q3', 'Q4']
    match_idx = 0
    p_idx = 0
    
    while p_idx < len(candidates) and match_idx < 4:
        # Obtener Match ID actual
        current_match = matches[match_idx]
        row_idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == current_match)].index
        
        if not row_idx.empty:
            idx = row_idx[0]
            
            # Competidor 1
            p1 = candidates.iloc[p_idx]
            main_df.at[idx, 'P1_Name'] = p1['Nombre_Completo']
            main_df.at[idx, 'P1_Dojo'] = f"{p1['Dojo']} ({p1['Peso']}kg)"
            
            # Competidor 2 (si existe)
            if p_idx + 1 < len(candidates):
                p2 = candidates.iloc[p_idx + 1]
                main_df.at[idx, 'P2_Name'] = p2['Nombre_Completo']
                main_df.at[idx, 'P2_Dojo'] = f"{p2['Dojo']} ({p2['Peso']}kg)"
            else:
                # BYE (Pasa directo)
                main_df.at[idx, 'P2_Name'] = "BYE"
                main_df.at[idx, 'P2_Dojo'] = "-"
                main_df.at[idx, 'Winner'] = p1['Nombre_Completo'] # Ganador automático
                
        p_idx += 2
        match_idx += 1
        
    save_data(main_df)
    return True, f"Bracket generado para {category} con {len(candidates)} competidores."

def reset_entire_system():
    """Resetea toda la base de datos a su estado inicial"""
    try:
        # Reiniciar Inscripciones
        empty_inscriptions = get_initial_inscriptions_df()
        save_inscriptions(empty_inscriptions)
        
        # Reiniciar Brackets
        initial_brackets = get_initial_df()
        save_data(initial_brackets)
        
        return True
    except Exception as e:
        print(e)
        return False

# Cargar DataFrames
main_df = load_data()
inscriptions_df = load_inscriptions()

# --- 5. NAVEGACIÓN Y VARIABLES DE ESTADO ---
if 'view' not in st.session_state: st.session_state.view = "HOME"
if 'cat' not in st.session_state: st.session_state.cat = None
if 'page' not in st.session_state: st.session_state.page = 0
if 'voted_matches' not in st.session_state: st.session_state.voted_matches = set()
if 'inscription_type' not in st.session_state: st.session_state.inscription_type = "individual"
if 'group_participants' not in st.session_state: st.session_state.group_participants = []
if 'current_participant' not in st.session_state: st.session_state.current_participant = {}
if 'inscription_step' not in st.session_state: st.session_state.inscription_step = 1
if 'payment_code' not in st.session_state: st.session_state.payment_code = ""
if 'is_admin' not in st.session_state: st.session_state.is_admin = False

def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

# --- FUNCIONES AUXILIARES (PAGO, IMAGEN, GUARDADO) ---
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def save_participant(participant_data, inscription_type, group_id=None):
    import uuid
    try:
        participant_id = str(uuid.uuid4())[:8]
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
            "Grupo_ID": group_id if inscription_type == "colectivo" else ""
        }
        global inscriptions_df
        new_row = pd.DataFrame([new_participant])
        inscriptions_df = pd.concat([inscriptions_df, new_row], ignore_index=True)
        save_inscriptions(inscriptions_df)
        return participant_id
    except Exception as e:
        st.error(f"Error: {e}")
        return None

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
                <img src="{logo_spon1}" class="sponsor-logo"><img src="{logo_spon2}" class="sponsor-logo">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. BARRA LATERAL GLOBAL Y ADMINISTRACIÓN ---
def render_global_sidebar():
    with st.sidebar:
        st.header("🔧 Panel de Control")
        
        if not st.session_state.is_admin:
            st.subheader("Acceso Admin")
            admin_pass = st.text_input("Contraseña", type="password")
            if st.button("🔓 Entrar", use_container_width=True):
                if check_admin(admin_pass):
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
        else:
            st.success("✅ MODO ADMINISTRADOR ACTIVO")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.is_admin = False
                st.rerun()
            
            st.markdown("---")
            
            # --- SECCIÓN: AUTOMATIC MATCHMAKING ---
            st.subheader("🤖 Auto-Matchmaking")
            st.info("Empareja inscritos por peso/estatura similar.")
            match_cat = st.selectbox("Categoría a generar", ALL_CATS)
            
            if st.button("⚡ Generar Bracket Automático", use_container_width=True):
                with st.spinner("Analizando similitudes y generando cruces..."):
                    success, msg = perform_automatic_matchmaking(match_cat)
                    if success:
                        st.success(msg)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(msg)
            
            st.markdown("---")
            
            # --- SECCIÓN: RESETEO DEL SISTEMA ---
            st.subheader("⛔ ZONA DE PELIGRO")
            with st.expander("🗑️ RESETEAR TODO EL SISTEMA", expanded=False):
                st.warning("¡ESTO BORRARÁ TODOS LOS INSCRITOS Y RESULTADOS!")
                confirm_reset = st.checkbox("Entiendo que esta acción es irreversible")
                
                if st.button("EJECUTAR RESET TOTAL", type="primary", disabled=not confirm_reset, use_container_width=True):
                    with st.spinner("Formateando bases de datos..."):
                        if reset_entire_system():
                            st.success("Sistema reiniciado correctamente.")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Error al resetear.")

# RENDERIZAR SIDEBAR SIEMPRE
render_global_sidebar()
render_header()

# --- 7. VISTA HOME ---
if st.session_state.view == "HOME":
    tab1, tab2, tab3 = st.tabs(["🏆 TORNEO", "📝 INSCRIPCIÓN", "📊 ESTADÍSTICAS"])
    
    with tab1:
        st.markdown("### 📂 SELECCIONA TU CATEGORÍA")
        # PAGINACIÓN
        CATEGORIES_PER_PAGE = 8
        total_categories = len(ALL_CATS)
        total_pages = (total_categories + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE
        
        col_prev, col_page, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.session_state.page > 0:
                if st.button("◀ Anterior", use_container_width=True):
                    st.session_state.page -= 1
                    st.rerun()
        with col_page:
            st.markdown(f"<div style='text-align:center; color:#666; font-size:14px;'>Página {st.session_state.page + 1} de {total_pages}</div>", unsafe_allow_html=True)
        with col_next:
            if st.session_state.page < total_pages - 1:
                if st.button("Siguiente ▶", use_container_width=True):
                    st.session_state.page += 1
                    st.rerun()
        
        start_idx = st.session_state.page * CATEGORIES_PER_PAGE
        end_idx = min(start_idx + CATEGORIES_PER_PAGE, total_categories)
        current_cats = ALL_CATS[start_idx:end_idx]
        
        kumite_men = [c for c in current_cats if "KUMITE - MEN" in c]
        kumite_women = [c for c in current_cats if "KUMITE - WOMEN" in c]
        kata_cats = [c for c in current_cats if "KATA" in c]
        
        if kumite_men or kumite_women:
            with st.expander("👊 KUMITE SENIORS", expanded=True):
                if kumite_men:
                    st.markdown("<div style='color:#ef4444; margin-bottom:10px; font-weight:bold;'>MEN</div>", unsafe_allow_html=True)
                    st.markdown('<div class="category-grid">', unsafe_allow_html=True)
                    for idx, w in enumerate(kumite_men):
                        if st.button(w.split("| ")[-1], key=f"m_{w}_{idx}", use_container_width=True): go("BRACKET", w)
                    st.markdown('</div>', unsafe_allow_html=True)
                if kumite_women:
                    st.markdown("<div style='color:#ef4444; margin-top:20px; font-weight:bold;'>WOMEN</div>", unsafe_allow_html=True)
                    st.markdown('<div class="category-grid">', unsafe_allow_html=True)
                    for idx, w in enumerate(kumite_women):
                        if st.button(w.split("| ")[-1], key=f"w_{w}_{idx}", use_container_width=True): go("BRACKET", w)
                    st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown("### 📝 SISTEMA DE INSCRIPCIÓN")
        inscription_type = st.radio("Tipo:", ["Individual", "Colectiva"], horizontal=True)
        st.session_state.inscription_type = "individual" if inscription_type == "Individual" else "colectivo"
        
        if st.session_state.inscription_step == 1:
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    nombre = st.text_input("Nombre Completo *")
                    edad = st.number_input("Edad *", 5, 80, 18)
                    peso = st.number_input("Peso (kg) *", 30.0, 150.0, 70.0, 0.1)
                    estatura = st.number_input("Estatura (cm) *", 100, 220, 170)
                with col2:
                    grado_sel = st.selectbox("Grado *", list(KARATE_GRADES.keys()), format_func=lambda x: f"{x} - {KARATE_GRADES[x]}")
                    dojo = st.text_input("Dojo/Club *")
                    organizacion = st.text_input("Organización *")
                    telefono = st.text_input("Teléfono *")
                    email = st.text_input("Email *")
                
                cat_sel = st.selectbox("Categoría *", ALL_CATS)
                uploaded = st.file_uploader("Foto Carnet", ['jpg','png'])
                
                cons = st.checkbox("Consentimiento Informado")
                desc = st.checkbox("Descargo de Responsabilidad")
                
                if st.button("GUARDAR", type="primary", use_container_width=True):
                    if all([nombre, dojo, organizacion, telefono, email]) and cons and desc and uploaded:
                        p_data = {
                            "nombre_completo": nombre, "edad": edad, "peso": peso, "estatura": estatura,
                            "grado": grado_sel, "dojo": dojo, "organizacion": organizacion,
                            "telefono": telefono, "email": email, "categoria": cat_sel,
                            "foto_base64": image_to_base64(Image.open(uploaded)),
                            "consentimiento": cons, "descargo": desc
                        }
                        
                        if st.session_state.inscription_type == "individual":
                            st.session_state.current_participant = p_data
                            st.session_state.inscription_step = 2
                            st.rerun()
                        else:
                            st.session_state.group_participants.append(p_data)
                            st.success("Participante agregado")
                            
            if st.session_state.inscription_type == "colectivo" and st.session_state.group_participants:
                 st.dataframe(pd.DataFrame(st.session_state.group_participants)[['nombre_completo','categoria']])
                 if st.button("FINALIZAR GRUPO", type="primary"): 
                     st.session_state.inscription_step = 2
                     st.rerun()

        elif st.session_state.inscription_step == 2:
            st.markdown("#### 💳 PAGO")
            st.info("Ingresa el código proporcionado por la organización.")
            code = st.text_input("Código de Pago")
            if st.button("CONFIRMAR PAGO", type="primary"):
                if code:
                    st.session_state.payment_code = code
                    parts = [st.session_state.current_participant] if st.session_state.inscription_type == "individual" else st.session_state.group_participants
                    gid = 'GRP_' + hashlib.md5(str(time.time()).encode()).hexdigest()[:6] if len(parts) > 1 else None
                    
                    for p in parts:
                        save_participant(p, st.session_state.inscription_type, gid)
                    
                    st.session_state.inscription_step = 3
                    st.rerun()

        elif st.session_state.inscription_step == 3:
            st.success("✅ Inscripción Completada")
            if st.button("Volver al Inicio"):
                st.session_state.inscription_step = 1
                st.session_state.current_participant = {}
                st.session_state.group_participants = []
                st.rerun()

    with tab3:
        st.subheader("📊 ESTADÍSTICAS")
        if not inscriptions_df.empty:
            st.bar_chart(inscriptions_df['Categoria'].value_counts())
            if st.session_state.is_admin:
                st.dataframe(inscriptions_df)
        else:
            st.info("No hay datos aún.")

# --- 8. VISTA BRACKET ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    cat_df = main_df[main_df['Category'] == cat].set_index('Match_ID')
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("🏠 INICIO", use_container_width=True): go("HOME")
    with col2:
        st.markdown(f"<h3 style='text-align:center; color:#FDB931;'>{cat}</h3>", unsafe_allow_html=True)
    
    # FUNCIONES BRACKET
    def get_row(mid): 
        try: return cat_df.loc[mid] 
        except: return pd.Series()
    def get_val(row, col): return row[col] if col in row and pd.notna(row[col]) and row[col] != "" else "..."

    # EDITOR MANUAL (SOLO ADMIN) - Si falla el automático o se necesitan ajustes
    if st.session_state.is_admin:
        with st.expander("✏️ EDICIÓN MANUAL DE BRACKET", expanded=False):
            match_edit = st.selectbox("Editar Match", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
            with st.form("edit"):
                r = get_row(match_edit)
                c1, c2 = st.columns(2)
                with c1:
                    n1 = st.text_input("P1 Nombre", get_val(r,'P1_Name'))
                    d1 = st.text_input("P1 Dojo", get_val(r,'P1_Dojo'))
                with c2:
                    n2 = st.text_input("P2 Nombre", get_val(r,'P2_Name'))
                    d2 = st.text_input("P2 Dojo", get_val(r,'P2_Dojo'))
                w = st.selectbox("Ganador", ["", n1, n2])
                live = st.checkbox("En Vivo", r.get('Live', False) if not r.empty else False)
                
                if st.form_submit_button("GUARDAR"):
                    idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==match_edit)].index
                    if not idx.empty:
                        main_df.at[idx[0], 'P1_Name'] = n1
                        main_df.at[idx[0], 'P1_Dojo'] = d1
                        main_df.at[idx[0], 'P2_Name'] = n2
                        main_df.at[idx[0], 'P2_Dojo'] = d2
                        main_df.at[idx[0], 'Winner'] = w
                        main_df.at[idx[0], 'Live'] = live
                        
                        # LOGICA DE AVANCE (SIMPLE)
                        if w:
                            if 'Q' in match_edit:
                                target = 'S1' if match_edit in ['Q1','Q2'] else 'S2'
                                pos = 'P1' if match_edit in ['Q1','Q3'] else 'P2'
                                t_idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==target)].index
                                if not t_idx.empty:
                                    main_df.at[t_idx[0], f'{pos}_Name'] = w
                                    main_df.at[t_idx[0], f'{pos}_Dojo'] = d1 if w==n1 else d2
                            elif 'S' in match_edit:
                                t_idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']=='F1')].index
                                pos = 'P1' if match_edit == 'S1' else 'P2'
                                if not t_idx.empty:
                                    main_df.at[t_idx[0], f'{pos}_Name'] = w
                                    main_df.at[t_idx[0], f'{pos}_Dojo'] = d1 if w==n1 else d2
                        
                        save_data(main_df)
                        st.rerun()

    # RENDERIZADO VISUAL DEL BRACKET (HTML)
    def render_player(row, p, cls):
        name = get_val(row, f'{p}_Name')
        dojo = get_val(row, f'{p}_Dojo')
        v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
        v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
        tot = v1 + v2
        pct = (v1/tot*100) if tot > 0 and p=='P1' else (v2/tot*100) if tot > 0 else 50
        bg = "linear-gradient(90deg, #ef4444, #dc2626)" if p=='P1' else "linear-gradient(90deg, #ffffff, #d1d5db)"
        live = '<span class="live-indicator"></span>' if row.get('Live', False) else ""
        
        return f"""<div class="player-box {cls}">{live}<div class="p-name">{name}</div>
        <div class="p-details"><span>🥋 {dojo}</span><span>{int(pct)}%</span></div>
        <div class="p-vote-bar"><div class="p-vote-fill" style="width:{pct}%; background:{bg};"></div></div>
        {'<div class="line-r"></div>' if cls!='none' else ''}</div>"""

    # Obtener filas
    rows = {m: get_row(m) for m in ['Q1','Q2','Q3','Q4','S1','S2','F1']}
    ws = {m: get_val(rows[m], 'Winner') for m in rows}

    html = f"""
    <div class="bracket-container">
        <div class="rounds-wrapper">
            <div class="round"><div class="round-title">CUARTOS</div>
                {render_player(rows['Q1'], 'P1', 'border-red')}{render_player(rows['Q1'], 'P2', 'border-white')}
                <div style="height:40px;position:relative;"><div class="conn-v" style="height:80px;top:-40px;"></div></div>
                {render_player(rows['Q2'], 'P1', 'border-red')}{render_player(rows['Q2'], 'P2', 'border-white')}
                <div style="height:40px;position:relative;"><div class="conn-v" style="height:80px;top:-40px;"></div></div>
                {render_player(rows['Q3'], 'P1', 'border-red')}{render_player(rows['Q3'], 'P2', 'border-white')}
                <div style="height:40px;position:relative;"><div class="conn-v" style="height:80px;top:-40px;"></div></div>
                {render_player(rows['Q4'], 'P1', 'border-red')}{render_player(rows['Q4'], 'P2', 'border-white')}
            </div>
            <div class="round"><div class="round-title">SEMIFINALES</div>
                <div style="height:50%;display:flex;flex-direction:column;justify-content:center;position:relative;margin-top:20px;">
                    <div class="conn-v" style="height:120px;top:50%;transform:translateY(-50%);"></div>
                    <div class="player-box border-red"><div class="p-name">{ws['Q1']}</div></div>
                    <div class="player-box border-white"><div class="p-name">{ws['Q2']}</div><div class="line-r"></div></div>
                </div>
                <div style="height:50%;display:flex;flex-direction:column;justify-content:center;position:relative;margin-top:40px;">
                    <div class="conn-v" style="height:120px;top:50%;transform:translateY(-50%);"></div>
                    <div class="player-box border-red"><div class="p-name">{ws['Q3']}</div></div>
                    <div class="player-box border-white"><div class="p-name">{ws['Q4']}</div><div class="line-r"></div></div>
                </div>
            </div>
            <div class="round"><div class="round-title">FINAL</div>
                <div style="height:100%;display:flex;flex-direction:column;justify-content:center;position:relative;">
                    <div class="conn-v" style="height:160px;top:50%;transform:translateY(-50%);"></div>
                    <div class="player-box border-red" style="margin-top:80px;"><div class="p-name">{ws['S1']}</div></div>
                    <div class="player-box border-white"><div class="p-name">{ws['S2']}</div><div class="line-r"></div></div>
                </div>
            </div>
            <div class="round"><div class="round-title">CAMPEÓN 🏆</div>
                <div style="height:100%;display:flex;flex-direction:column;justify-content:center;">
                    <div class="champion-box">{ws['F1'] if ws['F1'] != "..." else "POR DEFINIR"}</div>
                </div>
            </div>
        </div>
    </div>
    """
    st.html(html)
    
    # SISTEMA DE VOTACIÓN
    st.markdown("##### 📊 PREDICCIÓN DEL PÚBLICO")
    
    def vote(mid, col):
        uid = st.session_state.get('user_id', 'anon')
        if rate_limiter.allow_request(uid, mid):
            idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==mid)].index
            if not idx.empty:
                main_df.at[idx[0], col] += 1
                save_data(main_df)
                st.toast("✅ Voto registrado")
    
    vote_cols = st.columns(4)
    for i, m in enumerate(['Q1','Q2','Q3','Q4']):
        r = rows[m]
        if get_val(r,'P1_Name') != "...":
            with vote_cols[i]:
                st.caption(f"MATCH {m}")
                if st.button(f"🔴 {get_val(r,'P1_Name')[:10]}", key=f"v1_{m}"): vote(m, 'P1_Votes')
                if st.button(f"⚪ {get_val(r,'P2_Name')[:10]}", key=f"v2_{m}"): vote(m, 'P2_Votes')

    if not st.session_state.is_admin:
        st.html("<script>setTimeout(function(){window.location.reload();}, 15000);</script>")
