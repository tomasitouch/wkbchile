import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import hashlib
import json
import datetime
from datetime import timedelta

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
""", unsafe_allow_html=True)

# LINK GOOGLE SHEET
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

# --- 2. SEGURIDAD MEJORADA ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 3. ESTILOS CSS PRO MEJORADO RESPONSIVO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    @keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    
    /* BASE RESPONSIVA */
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
        padding: 20px 0; 
        display: flex; 
        justify-content: center; 
        animation: fadeIn 0.8s ease-out; 
        -webkit-overflow-scrolling: touch;
        scrollbar-width: thin;
    }
    
    .bracket-container::-webkit-scrollbar {
        height: 6px;
    }
    
    .bracket-container::-webkit-scrollbar-track {
        background: #1f2937;
    }
    
    .bracket-container::-webkit-scrollbar-thumb {
        background: #ef4444;
        border-radius: 3px;
    }
    
    .round { 
        min-width: 240px; 
        margin: 0 10px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-around; 
        flex-shrink: 0;
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
    
    .player-box { 
        background: #1f2937; 
        padding: 12px; 
        margin: 6px 0; 
        border-radius: 6px; 
        position: relative; 
        z-index: 2; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        border: 1px solid #374151; 
        transition: 0.3s;
        min-height: 70px;
    }
    .player-box:hover { transform: scale(1.02); z-index: 10; border-color: #666; }
    
    /* AKA / SHIRO */
    .border-red { 
        border-left: 6px solid #ef4444; 
        background: linear-gradient(90deg, rgba(239,68,68,0.1) 0%, rgba(31,41,55,1) 60%); 
    }
    .border-white { 
        border-left: 6px solid #ffffff; 
        background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(31,41,55,1) 60%); 
    }
    
    /* TEXT RESPONSIVO */
    .p-name { 
        font-size: clamp(12px, 1.5vw, 14px); 
        font-weight: bold; 
        color: white; 
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .p-details { 
        font-size: clamp(10px, 1.2vw, 11px); 
        color: #9ca3af; 
        display: flex; 
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 5px;
    }
    .p-vote-bar { 
        height: 4px; 
        background: #374151; 
        margin-top: 8px; 
        border-radius: 2px; 
        overflow: hidden; 
    }
    .p-vote-fill { height: 100%; transition: width 0.5s ease; }
    
    /* CHAMPION RESPONSIVE */
    .champion-box { 
        background: radial-gradient(circle, #FDB931 0%, #d9a024 100%); 
        color: black !important; 
        text-align: center; 
        padding: clamp(15px, 3vw, 20px); 
        border-radius: 8px; 
        font-weight: bold; 
        font-size: clamp(14px, 2vw, 18px);
        box-shadow: 0 0 25px rgba(253, 185, 49, 0.4); 
        animation: fadeIn 1.5s;
        word-break: break-word;
    }
    
    /* LINES MEJORADAS */
    .line-r { 
        position: absolute; 
        right: -18px; 
        width: 18px; 
        border-bottom: 2px solid #6b7280; 
        top: 50%; 
        z-index: 1; 
    }
    .conn-v { 
        position: absolute; 
        right: -18px; 
        width: 10px; 
        border-right: 2px solid #6b7280; 
        z-index: 1; 
    }
    
    /* CONTENEDORES RESPONSIVOS */
    .category-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    .vote-buttons-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    /* MEJORAS PARA MÓVILES */
    @media (max-width: 1024px) {
        .header-container { 
            flex-direction: column !important; 
            text-align: center !important; 
            padding: 15px !important; 
            gap: 20px;
        }
        
        .header-title, .header-sponsors {
            align-items: center !important;
            text-align: center !important;
        }
        
        .sponsor-logos {
            justify-content: center !important;
        }
        
        .bracket-container { 
            flex-direction: row !important; 
            justify-content: flex-start !important;
            padding-bottom: 15px;
        }
        
        .round { 
            min-width: 85vw !important; 
            margin: 0 15px !important; 
        }
        
        .sponsor-logo { 
            height: 30px !important; 
            margin: 0 5px !important; 
        }
        
        .player-box {
            padding: 10px;
            min-height: 65px;
        }
    }
    
    @media (max-width: 768px) {
        .round { 
            min-width: 90vw !important; 
            margin: 0 10px !important; 
        }
        
        .category-grid {
            grid-template-columns: 1fr;
        }
        
        .vote-buttons-container {
            grid-template-columns: 1fr;
        }
        
        .p-name { 
            font-size: 13px !important; 
        }
        .p-details { 
            font-size: 10px !important; 
            flex-direction: column;
            gap: 2px;
        }
        
        .stButton > button {
            font-size: 13px !important;
            padding: 10px !important;
        }
        
        h1 { font-size: 24px !important; }
        h2 { font-size: 20px !important; }
        h3 { font-size: 18px !important; }
        h4 { font-size: 16px !important; }
    }
    
    @media (max-width: 480px) {
        .header-container {
            padding: 10px !important;
        }
        
        .header-title img {
            height: 40px !important;
        }
        
        .sponsor-logo {
            height: 25px !important;
            max-width: 100px;
        }
        
        .round { 
            min-width: 95vw !important; 
            margin: 0 5px !important; 
        }
        
        .player-box {
            padding: 8px;
            min-height: 60px;
        }
        
        .p-name { 
            font-size: 12px !important; 
        }
        
        .p-details { 
            font-size: 9px !important; 
        }
        
        .champion-box {
            padding: 12px !important;
            font-size: 16px !important;
        }
    }
    
    /* ORIENTACIÓN HORIZONTAL */
    @media (orientation: landscape) and (max-height: 600px) {
        .bracket-container {
            padding: 10px 0;
        }
        
        .player-box {
            min-height: 50px;
            padding: 8px;
            margin: 4px 0;
        }
        
        .p-name {
            font-size: 11px !important;
        }
    }
    
    /* TAMAÑOS DE TEXTO RESPONSIVOS */
    .responsive-text-lg { font-size: clamp(18px, 2.5vw, 24px) !important; }
    .responsive-text-md { font-size: clamp(14px, 1.8vw, 18px) !important; }
    .responsive-text-sm { font-size: clamp(12px, 1.2vw, 14px) !important; }
    
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

def save_data(df):
    conn = get_connection()
    try:
        conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
        create_backup(df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

def create_backup(df):
    """Crea backup automático de los datos"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_data = df.to_dict(orient='records')
        
        if 'backups' not in st.session_state:
            st.session_state.backups = {}
        
        st.session_state.backups[timestamp] = backup_data
        return timestamp
    except Exception as e:
        st.error(f"Error creando backup: {e}")

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

main_df = load_data()

# --- 5. NAVEGACIÓN MEJORADA ---
if 'view' not in st.session_state: st.session_state.view = "HOME"
if 'cat' not in st.session_state: st.session_state.cat = None
if 'page' not in st.session_state: st.session_state.page = 0
if 'voted_matches' not in st.session_state: st.session_state.voted_matches = set()

def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

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

# --- 6. VISTA HOME MEJORADA CON PAGINACIÓN RESPONSIVA ---
if st.session_state.view == "HOME":
    render_header()
    
    errors = validate_data(main_df)
    if errors and st.session_state.get('is_admin', False):
        with st.expander("⚠️ Errores de Validación", expanded=False):
            for error in errors:
                st.error(error)
    
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
                # Usar grid responsivo en lugar de columns
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
    
    # Vista de estadísticas
    if st.session_state.get('is_admin', False):
        with st.expander("📊 ESTADÍSTICAS DEL TORNEO", expanded=False):
            st.subheader("🏆 Top Dojos")
            all_dojos = pd.concat([main_df['P1_Dojo'], main_df['P2_Dojo']])
            dojo_counts = all_dojos.value_counts().head(10)
            st.bar_chart(dojo_counts)
            
            st.subheader("🔥 Partidos Más Votados")
            main_df['Total_Votes'] = main_df['P1_Votes'] + main_df['P2_Votes']
            top_matches = main_df.nlargest(5, 'Total_Votes')[['Category', 'Match_ID', 'Total_Votes']]
            st.dataframe(top_matches, use_container_width=True)
    
    # Recarga automática
    st.html("<script>setTimeout(function(){window.location.reload();}, 60000);</script>")

# --- 7. VISTA BRACKET MEJORADA CON RESPONSIVIDAD ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    cat_df = main_df[main_df['Category'] == cat].set_index('Match_ID')
    
    def get_row(mid): 
        try: return cat_df.loc[mid]
        except: return pd.Series()
    
    def get_val(row, col): 
        return row[col] if col in row and pd.notna(row[col]) and row[col] != "" else "..."
    
    def generate_share_link():
        """Genera link para compartir"""
        import urllib.parse
        base_url = "https://wkb-hub.streamlit.app/"
        params = {"category": urllib.parse.quote(cat)}
        return f"{base_url}?{params}"

    render_header()
    
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

    # --- VOTACIÓN MEJORADA CON DISEÑO RESPONSIVO ---
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
    
    # Mostrar botones de votación con diseño responsivo
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
            
            # Contenedor responsivo para cada match
            col = st.container()
            with col:
                st.markdown(f"""
                <div style="
                    background: #1f2937; 
                    padding: 15px; 
                    border-radius: 8px; 
                    border: 1px solid #374151;
                    margin-bottom: 10px;
                ">
                    <div style="color: #FDB931; font-weight: bold; margin-bottom: 10px; font-size: 14px;">
                        {live_indicator}Match {m}
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 13px;">
                        <span>🔴 {p1[:12]}{'...' if len(p1) > 12 else ''}</span>
                        <span>vs</span>
                        <span>⚪ {p2[:12]}{'...' if len(p2) > 12 else ''}</span>
                    </div>
                    
                    <div style="background: #374151; height: 6px; border-radius: 3px; margin-bottom: 10px; overflow: hidden;">
                        <div style="width: {pct1}%; height: 100%; background: #ef4444; float: left;"></div>
                        <div style="width: {pct2}%; height: 100%; background: #ffffff; float: left;"></div>
                    </div>
                    
                    <div style="display: flex; gap: 8px; margin-bottom: 10px;">
                        <div style="flex: 1;">
                            <button onclick="voteFor('{m}', 'P1')" style="
                                width: 100%; 
                                padding: 8px; 
                                background: #ef4444; 
                                color: white; 
                                border: none; 
                                border-radius: 4px; 
                                cursor: pointer; 
                                font-size: 12px;
                                font-family: 'Roboto Condensed', sans-serif;">
                                🔴 Votar
                            </button>
                        </div>
                        <div style="flex: 1;">
                            <button onclick="voteFor('{m}', 'P2')" style="
                                width: 100%; 
                                padding: 8px; 
                                background: #ffffff; 
                                color: black; 
                                border: none; 
                                border-radius: 4px; 
                                cursor: pointer; 
                                font-size: 12px;
                                font-family: 'Roboto Condensed', sans-serif;">
                                ⚪ Votar
                            </button>
                        </div>
                    </div>
                    
                    <div style="font-size: 11px; color: #9ca3af; text-align: center;">
                        Total votos: {v1 + v2} | 🔴 {int(pct1)}% - ⚪ {int(pct2)}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Script para manejar votos
    st.markdown("""
    <script>
    function voteFor(matchId, player) {
        // Esta función se implementaría con Streamlit's JavaScript API
        // Por ahora es un placeholder
        alert(`Función de voto para ${player} en ${matchId} - Implementar con Streamlit`);
    }
    </script>
    """, unsafe_allow_html=True)

    # --- GENERADOR BRACKET RESPONSIVO ---
    def render_player(row, p_prefix, color_class):
        name = get_val(row, f'{p_prefix}_Name')
        dojo = get_val(row, f'{p_prefix}_Dojo')
        
        v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
        v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
        total = v1 + v2
        pct = 50
        
        if total > 0:
            pct = (v1 / total * 100) if p_prefix == 'P1' else (v2 / total * 100)
        
        bar_bg = "#ef4444" if p_prefix == 'P1' else "#ffffff"
        
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

    # Generar HTML del bracket responsivo
    html = f"""
    <div class="bracket-container">
        <div class="round">
            <div style="text-align:center;color:#666;font-size:12px; margin-bottom: 10px;">CUARTOS</div>
            {render_player(r_q1, 'P1', 'border-red')}
            {render_player(r_q1, 'P2', 'border-white')}
            <div style="height:20px"></div>
            {render_player(r_q2, 'P1', 'border-red')}
            {render_player(r_q2, 'P2', 'border-white')}
            <div style="height:20px"></div>
            {render_player(r_q3, 'P1', 'border-red')}
            {render_player(r_q3, 'P2', 'border-white')}
            <div style="height:20px"></div>
            {render_player(r_q4, 'P1', 'border-red')}
            {render_player(r_q4, 'P2', 'border-white')}
        </div>

        <div class="round">
            <div style="text-align:center;color:#666;font-size:12px; margin-bottom: 10px;">SEMIS</div>
            <div style="height:50%;display:flex;flex-direction:column;justify-content:center;position:relative;">
                <div class="conn-v" style="top:25%;bottom:25%;border-left:2px solid #6b7280;border-right:none;border-top:2px solid #6b7280;border-bottom:2px solid #6b7280;left:-18px;"></div>
                <div class="player-box border-red"><div class="p-name">{w_q1}</div></div>
                <div class="player-box border-white"><div class="p-name">{w_q2}</div><div class="line-r"></div></div>
            </div>
            <div style="height:50%;display:flex;flex-direction:column;justify-content:center;position:relative;">
                <div class="conn-v" style="top:25%;bottom:25%;border-left:2px solid #6b7280;border-right:none;border-top:2px solid #6b7280;border-bottom:2px solid #6b7280;left:-18px;"></div>
                <div class="player-box border-red"><div class="p-name">{w_q3}</div></div>
                <div class="player-box border-white"><div class="p-name">{w_q4}</div><div class="line-r"></div></div>
            </div>
        </div>

        <div class="round">
            <div style="text-align:center;color:#666;font-size:12px; margin-bottom: 10px;">FINAL</div>
            <div style="height:100%;display:flex;flex-direction:column;justify-content:center;position:relative;">
                <div class="conn-v" style="top:38%;bottom:38%;border-left:2px solid #6b7280;border-right:none;border-top:2px solid #6b7280;border-bottom:2px solid #6b7280;left:-18px;"></div>
                <div class="player-box border-red"><div class="p-name">{w_s1}</div></div>
                <div class="player-box border-white"><div class="p-name">{w_s2}</div><div class="line-r"></div></div>
            </div>
        </div>

        <div class="round">
            <div style="text-align:center;color:#FDB931;font-size:12px; margin-bottom: 10px;">CAMPEÓN</div>
            <div style="height:100%;display:flex;flex-direction:column;justify-content:center;">
                <div class="champion-box">
                    {w_f1 if w_f1 != "..." else "POR DEFINIR"} 🏆
                </div>
            </div>
        </div>
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
        st.html("<script>setTimeout(function(){window.location.reload();}, 15000);</script>")
    else:
        st.info("🔄 Recarga automática desactivada en modo admin")
