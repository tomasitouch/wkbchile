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

# LINK GOOGLE SHEET
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

# --- 2. SEGURIDAD MEJORADA ---
# Hash de la contraseña admin (generado con: hashlib.sha256("admin123".encode()).hexdigest())
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 3. ESTILOS CSS PRO MEJORADO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&display=swap');
    
    @keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    
    .stApp { background-color: #0e1117; color: white; }
    h1, h2, h3, h4, div, button { font-family: 'Roboto Condensed', sans-serif !important; text-transform: uppercase; }
    
    /* HEADER RESPONSIVE */
    .header-container { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 20px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; animation: fadeIn 0.5s ease-out; margin-bottom: 20px;
    }
    .sponsor-logo { height: 45px; margin-left: 15px; opacity: 0.8; transition: 0.3s; filter: grayscale(100%); }
    .sponsor-logo:hover { opacity: 1; filter: grayscale(0%); transform: scale(1.05); }
    
    /* BOTONES */
    div.stButton > button {
        width: 100%; background: #1f2937; color: #e5e7eb; border: 1px solid #374151;
        padding: 12px; border-radius: 6px; text-align: left; font-size: 14px; transition: 0.2s;
    }
    div.stButton > button:hover { border-color: #ef4444; color: #ef4444; transform: translateX(5px); }
    
    /* BRACKET RESPONSIVE */
    .bracket-container { overflow-x: auto; padding: 20px 0; display: flex; justify-content: center; animation: fadeIn 0.8s ease-out; }
    .round { min-width: 240px; margin: 0 10px; display: flex; flex-direction: column; justify-content: space-around; }
    
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
        background: #1f2937; padding: 10px; margin: 6px 0; border-radius: 6px; 
        position: relative; z-index: 2; box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        border: 1px solid #374151; transition: 0.3s;
    }
    .player-box:hover { transform: scale(1.02); z-index: 10; border-color: #666; }
    
    /* AKA / SHIRO */
    .border-red { border-left: 6px solid #ef4444; background: linear-gradient(90deg, rgba(239,68,68,0.1) 0%, rgba(31,41,55,1) 60%); }
    .border-white { border-left: 6px solid #ffffff; background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(31,41,55,1) 60%); }
    
    /* TEXT */
    .p-name { font-size: 14px; font-weight: bold; color: white; margin-bottom: 2px; }
    .p-details { font-size: 11px; color: #9ca3af; display: flex; justify-content: space-between; }
    .p-vote-bar { height: 4px; background: #374151; margin-top: 6px; border-radius: 2px; overflow: hidden; }
    .p-vote-fill { height: 100%; transition: width 0.5s ease; }
    
    /* CHAMPION */
    .champion-box { 
        background: radial-gradient(circle, #FDB931 0%, #d9a024 100%); 
        color: black !important; text-align: center; padding: 20px; 
        border-radius: 8px; font-weight: bold; font-size: 18px;
        box-shadow: 0 0 25px rgba(253, 185, 49, 0.4); animation: fadeIn 1.5s;
    }
    
    /* LINES */
    .line-r { position: absolute; right: -18px; width: 18px; border-bottom: 2px solid #6b7280; top: 50%; z-index: 1; }
    .conn-v { position: absolute; right: -18px; width: 10px; border-right: 2px solid #6b7280; z-index: 1; }
    
    /* RESPONSIVE */
    @media (max-width: 768px) {
        .header-container { flex-direction: column !important; text-align: center !important; padding: 15px !important; }
        .bracket-container { flex-direction: column !important; align-items: center !important; }
        .round { min-width: 90% !important; margin: 10px 0 !important; }
        .sponsor-logo { height: 35px !important; margin: 5px !important; }
        .p-name { font-size: 12px !important; }
        .p-details { font-size: 10px !important; }
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
                "Live": False if m in ['S1', 'S2', 'F1'] else False  # Nueva columna para partidos en vivo
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
        create_backup(df)  # Crear backup automático
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

def create_backup(df):
    """Crea backup automático de los datos"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_data = df.to_dict(orient='records')
        
        # Guardar en session state para acceso inmediato
        if 'backups' not in st.session_state:
            st.session_state.backups = {}
        
        st.session_state.backups[timestamp] = backup_data
        
        # También puedes guardar en otra hoja de Google Sheets si quieres
        # conn = get_connection()
        # conn.update(spreadsheet=SHEET_URL, worksheet=f"Backup_{timestamp}", data=df)
        
        return timestamp
    except Exception as e:
        st.error(f"Error creando backup: {e}")

def validate_data(df):
    """Valida la integridad de los datos"""
    errors = []
    
    # Verificar que todas las categorías tengan todos los matches
    required_matches = ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']
    for cat in ALL_CATS:
        cat_matches = df[df['Category'] == cat]['Match_ID'].tolist()
        for rm in required_matches:
            if rm not in cat_matches:
                errors.append(f"Falta {rm} en {cat}")
    
    # Verificar ganadores válidos
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

# --- HEADER MEJORADO ---
def render_header():
    # URLs reales de logos
    logo_org = "https://cdn-icons-png.flaticon.com/512/1603/1603754.png" 
    logo_spon1 = "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg" 
    logo_spon2 = "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
    
    st.markdown(f"""
    <div class="header-container">
        <div style="display:flex; align-items:center;">
            <img src="{logo_org}" height="60" style="margin-right:15px; filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));">
            <div>
                <h2 style="margin:0; color:white; font-size: 24px; letter-spacing: 1px;">WKB CHILE</h2>
                <small style="color:#FDB931; font-weight:bold; letter-spacing: 2px;">OFFICIAL TOURNAMENT HUB</small>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="color:#666; font-size:9px; margin-bottom:5px; letter-spacing:1px;">POWERED BY</div>
            <div>
                <img src="{logo_spon1}" class="sponsor-logo">
                <img src="{logo_spon2}" class="sponsor-logo">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. VISTA HOME MEJORADA CON PAGINACIÓN ---
if st.session_state.view == "HOME":
    render_header()
    
    # Validar datos al inicio
    errors = validate_data(main_df)
    if errors and st.session_state.get('is_admin', False):
        with st.expander("⚠️ Errores de Validación", expanded=False):
            for error in errors:
                st.error(error)
    
    st.markdown("### 📂 SELECCIONA TU CATEGORÍA")
    
    # PAGINACIÓN
    CATEGORIES_PER_PAGE = 8
    total_categories = len(ALL_CATS)
    total_pages = (total_categories + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE
    
    # Control de páginas
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.session_state.page > 0:
            if st.button("◀ Anterior"):
                st.session_state.page -= 1
                st.rerun()
    
    with col_page:
        st.markdown(f"<div style='text-align:center; color:#666;'>Página {st.session_state.page + 1} de {total_pages}</div>", 
                   unsafe_allow_html=True)
    
    with col_next:
        if st.session_state.page < total_pages - 1:
            if st.button("Siguiente ▶"):
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
    
    if kumite_men or kumite_women:
        with st.expander("👊 KUMITE SENIORS", expanded=True):
            if kumite_men:
                st.markdown("<div style='color:#ef4444; margin-bottom:10px; font-weight:bold;'>MEN</div>", unsafe_allow_html=True)
                cols = st.columns(2)
                for idx, w in enumerate(kumite_men):
                    with cols[idx % 2]:
                        if st.button(w.split("| ")[-1], key=f"m_{w}_{idx}"):
                            go("BRACKET", w)
            
            if kumite_women:
                st.markdown("<div style='color:#ef4444; margin-top:20px; margin-bottom:10px; font-weight:bold;'>WOMEN</div>", unsafe_allow_html=True)
                cols = st.columns(2)
                for idx, w in enumerate(kumite_women):
                    with cols[idx % 2]:
                        if st.button(w.split("| ")[-1], key=f"w_{w}_{idx}"):
                            go("BRACKET", w)
    
    if kata_cats:
        with st.expander("🙏 KATA", expanded=True):
            cols = st.columns(2)
            for idx, cat in enumerate(kata_cats):
                with cols[idx % 2]:
                    if st.button(cat.split("| ")[-1], key=f"k_{cat}_{idx}"):
                        go("BRACKET", cat)
    
    # Vista de estadísticas (solo para admin)
    if st.session_state.get('is_admin', False):
        with st.expander("📊 ESTADÍSTICAS DEL TORNEO", expanded=False):
            # Top dojos
            st.subheader("🏆 Top Dojos")
            all_dojos = pd.concat([main_df['P1_Dojo'], main_df['P2_Dojo']])
            dojo_counts = all_dojos.value_counts().head(10)
            st.bar_chart(dojo_counts)
            
            # Partidos más votados
            st.subheader("🔥 Partidos Más Votados")
            main_df['Total_Votes'] = main_df['P1_Votes'] + main_df['P2_Votes']
            top_matches = main_df.nlargest(5, 'Total_Votes')[['Category', 'Match_ID', 'Total_Votes']]
            st.dataframe(top_matches, use_container_width=True)
    
    # Recarga automática
    st.html("<script>setTimeout(function(){window.location.reload();}, 60000);</script>")

# --- 7. VISTA BRACKET MEJORADA ---
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
    
    # Barra Superior Mejorada
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1:
        if st.button("🏠 INICIO"):
            go("HOME")
    with c2:
        st.markdown(f"<h3 style='text-align:center; color:#FDB931; margin-top:0;'>{cat}</h3>", 
                   unsafe_allow_html=True)
    with c3:
        share_link = generate_share_link()
        st.markdown(f"""
        <div style='text-align:right; font-size:12px;'>
            <span style='color:#666;'>SHARE:</span><br>
            <a href='{share_link}' target='_blank' style='color:#FDB931; text-decoration:none;'>
                🔗 COPIAR LINK
            </a>
        </div>
        """, unsafe_allow_html=True)

    # --- PANEL ADMIN MEJORADO ---
    with st.sidebar:
        st.header("🔧 Panel de Control")
        
        # Toggle modo oscuro/claro
        if 'dark_mode' not in st.session_state:
            st.session_state.dark_mode = True
        
        if st.toggle("🌙 Modo Oscuro / ☀️ Modo Claro", value=st.session_state.dark_mode):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
        
        # Admin Panel
        if 'is_admin' not in st.session_state: 
            st.session_state.is_admin = False
        
        if not st.session_state.is_admin:
            st.subheader("Acceso Admin")
            admin_pass = st.text_input("Contraseña", type="password")
            if st.button("🔓 Entrar") and check_admin(admin_pass):
                st.session_state.is_admin = True
                st.rerun()
        else:
            st.success("✅ Editor Activo")
            
            if st.button("🚪 Salir"):
                st.session_state.is_admin = False
                st.rerun()
            
            # Restaurar backup
            if 'backups' in st.session_state and st.session_state.backups:
                st.subheader("🔄 Restaurar Backup")
                backup_option = st.selectbox("Seleccionar backup", list(st.session_state.backups.keys()))
                if st.button("Restaurar este backup"):
                    backup_data = st.session_state.backups[backup_option]
                    restored_df = pd.DataFrame(backup_data)
                    save_data(restored_df)
                    st.success("Backup restaurado!")
                    st.rerun()
            
            # Editor de matches
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
                
                # Opciones de ganador
                winner_opts = ["", n1, n2] if n1 != "..." and n2 != "..." else [""]
                curr_w = get_val(row, 'Winner')
                w_idx = winner_opts.index(curr_w) if curr_w in winner_opts else 0
                winner = st.selectbox("GANADOR", winner_opts, index=w_idx)
                
                if st.form_submit_button("💾 GUARDAR CAMBIOS"):
                    idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==match_edit)].index
                    if not idx.empty:
                        main_df.at[idx[0], 'P1_Name'] = n1
                        main_df.at[idx[0], 'P1_Dojo'] = d1
                        main_df.at[idx[0], 'P2_Name'] = n2
                        main_df.at[idx[0], 'P2_Dojo'] = d2
                        main_df.at[idx[0], 'Winner'] = winner
                        main_df.at[idx[0], 'Live'] = live1
                        
                        # Si hay ganador y es un match de cuartos, propagar a semifinales
                        if winner and 'Q' in match_edit:
                            q_num = int(match_edit[1])
                            if q_num in [1, 2]:
                                # Va a S1
                                s1_idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']=='S1')].index
                                if not s1_idx.empty:
                                    if q_num == 1:
                                        main_df.at[s1_idx[0], 'P1_Name'] = winner
                                        main_df.at[s1_idx[0], 'P1_Dojo'] = d1 if winner == n1 else d2
                                    else:
                                        main_df.at[s1_idx[0], 'P2_Name'] = winner
                                        main_df.at[s1_idx[0], 'P2_Dojo'] = d1 if winner == n1 else d2
                            elif q_num in [3, 4]:
                                # Va a S2
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

    # --- VOTACIÓN MEJORADA CON RATE LIMITING ---
    st.markdown("##### 📊 PREDICCIÓN DEL PÚBLICO (EN VIVO)")
    
    def vote(mid, player_col, player_name):
        # Verificar si ya votó
        vote_key = f"{cat}_{mid}"
        if vote_key in st.session_state.voted_matches:
            st.warning(f"Ya votaste en este match!")
            return
        
        # Rate limiting
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
    
    # Mostrar botones de votación para cuartos
    vote_cols = st.columns(4)
    for i, m in enumerate(['Q1', 'Q2', 'Q3', 'Q4']):
        row = get_row(m)
        p1, p2 = get_val(row, 'P1_Name'), get_val(row, 'P2_Name')
        
        if p1 != "..." and p2 != "...":
            with vote_cols[i]:
                # Indicador de partido en vivo
                live_indicator = ""
                if row.get('Live', False):
                    live_indicator = '<span class="live-indicator"></span>'
                
                st.markdown(f"{live_indicator} **Match {m}**", unsafe_allow_html=True)
                
                # Estadísticas de votos
                v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
                v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
                total = v1 + v2
                
                if total > 0:
                    pct1 = (v1 / total * 100)
                    pct2 = (v2 / total * 100)
                    st.caption(f"🔴 {p1}: {int(pct1)}%  ⚪ {p2}: {int(pct2)}%")
                
                # Botones de votación
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"🔴 {p1[:10]}...", key=f"vote_red_{m}", use_container_width=True):
                        vote(m, 'P1_Votes', p1)
                with col_b:
                    if st.button(f"⚪ {p2[:10]}...", key=f"vote_white_{m}", use_container_width=True):
                        vote(m, 'P2_Votes', p2)

    # --- GENERADOR BRACKET MEJORADO ---
    def render_player(row, p_prefix, color_class):
        name = get_val(row, f'{p_prefix}_Name')
        dojo = get_val(row, f'{p_prefix}_Dojo')
        
        # Calcular porcentajes
        v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
        v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
        total = v1 + v2
        pct = 50
        
        if total > 0:
            pct = (v1 / total * 100) if p_prefix == 'P1' else (v2 / total * 100)
        
        bar_bg = "#ef4444" if p_prefix == 'P1' else "#ffffff"
        
        # Indicador de partido en vivo
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

    # Generar HTML del bracket
    html = f"""
    <div class="bracket-container">
        <div class="round">
            <div style="text-align:center;color:#666;font-size:10px;">CUARTOS</div>
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
            <div style="text-align:center;color:#666;font-size:10px;">SEMIS</div>
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
            <div style="text-align:center;color:#666;font-size:10px;">FINAL</div>
            <div style="height:100%;display:flex;flex-direction:column;justify-content:center;position:relative;">
                <div class="conn-v" style="top:38%;bottom:38%;border-left:2px solid #6b7280;border-right:none;border-top:2px solid #6b7280;border-bottom:2px solid #6b7280;left:-18px;"></div>
                <div class="player-box border-red"><div class="p-name">{w_s1}</div></div>
                <div class="player-box border-white"><div class="p-name">{w_s2}</div><div class="line-r"></div></div>
            </div>
        </div>

        <div class="round">
            <div style="text-align:center;color:#FDB931;font-size:10px;">CAMPEÓN</div>
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
        # Calcular estadísticas para esta categoría
        total_votes = cat_df['P1_Votes'].sum() + cat_df['P2_Votes'].sum()
        avg_votes_per_match = total_votes / len(cat_df) if len(cat_df) > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Votos Totales", f"{int(total_votes)}")
        with col2:
            st.metric("Partidos", f"{len(cat_df)}")
        with col3:
            st.metric("Promedio por Match", f"{avg_votes_per_match:.1f}")
        
        # Gráfico de votos por match
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
