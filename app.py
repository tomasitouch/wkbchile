import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import hashlib
import datetime
import base64
from PIL import Image
import io
import urllib.parse
import random

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="WKB Official Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

# Meta tags para responsive
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#0e1117">
""", unsafe_allow_html=True)

# CONFIGURACIÓN
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9" # admin123
PAYMENT_CODE_TEST = "WKB2026" 

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 2. ESTILOS CSS PROFESIONALES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    .stApp { background-color: #0e1117; color: white; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, div, button { font-family: 'Roboto Condensed', sans-serif !important; text-transform: uppercase; }
    
    /* HEADER */
    .header-container { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 20px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;
    }
    .sponsor-logo { height: 35px; opacity: 0.7; filter: grayscale(100%); }

    /* TARJETAS DE LISTA (FASE 1) */
    .list-card {
        background: #1f2937; padding: 15px; border-radius: 8px; border: 1px solid #374151;
        display: flex; align-items: center; gap: 15px; margin-bottom: 10px;
    }
    .list-avatar {
        width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #FDB931;
    }

    /* BRACKET HORIZONTAL (FASE 2) */
    .bracket-wrapper {
        width: 100%; overflow-x: auto; padding-bottom: 20px;
    }
    .bracket-container { 
        display: flex; min-width: 900px; padding: 10px;
    }
    .round { min-width: 240px; margin: 0 10px; display: flex; flex-direction: column; justify-content: space-around; }

    /* TARJETAS DE BRACKET CON FOTO */
    .player-box { 
        background: #1f2937; padding: 8px; margin: 8px 0; border-radius: 6px; 
        position: relative; z-index: 2; box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        border: 1px solid #374151; min-height: 60px; display: flex; align-items: center; gap: 10px;
    }
    .player-img-small {
        width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: #000;
    }
    .border-red { border-left: 4px solid #ef4444; }
    .border-white { border-left: 4px solid #ffffff; }
    
    .p-info { flex: 1; overflow: hidden; }
    .p-name { font-size: 13px; font-weight: bold; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .p-dojo { font-size: 10px; color: #9ca3af; }
    
    /* CAMPEÓN */
    .champion-box { 
        background: radial-gradient(circle, #FDB931 0%, #d9a024 100%); 
        color: black !important; text-align: center; padding: 20px; 
        border-radius: 8px; font-weight: bold; font-size: 18px;
    }

    /* CONECTORES */
    .line-r { position: absolute; right: -22px; width: 22px; border-bottom: 2px solid #6b7280; top: 50%; z-index: 1; }
    .conn-v { position: absolute; right: -22px; width: 2px; background: #6b7280; top: 50%; z-index: 1; transform: translateY(-50%); }
    .live-indicator { display: inline-block; width: 6px; height: 6px; background-color: #ef4444; border-radius: 50%; animation: pulse 1s infinite; margin-right: 4px;}

    /* BOTONES */
    div.stButton > button { width: 100%; background: #1f2937; color: white; border: 1px solid #374151; }
    div.stButton > button:hover { border-color: #FDB931; color: #FDB931; }
</style>
""", unsafe_allow_html=True)

# --- 3. GESTIÓN DE DATOS ---

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

# Rate Limiter
if 'voted_matches' not in st.session_state: st.session_state.voted_matches = set()
if 'cart' not in st.session_state: st.session_state.cart = []

@st.cache_resource
def get_connection(): return st.connection("gsheets", type=GSheetsConnection)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=15)
def load_data():
    conn = get_connection()
    try:
        # Cargar Matches
        df_matches = conn.read(spreadsheet=SHEET_URL, worksheet="Matches", ttl=15)
        # Si está vacía o no existe, crear estructura
        if df_matches.empty or "P1_Foto" not in df_matches.columns:
            df_matches = pd.DataFrame(columns=["Category", "Match_ID", "P1_Name", "P1_Dojo", "P1_Foto", "P1_Votes", "P2_Name", "P2_Dojo", "P2_Foto", "P2_Votes", "Winner", "Live"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Matches", data=df_matches)
        
        # Cargar Inscripciones
        try:
            df_inscriptions = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones", ttl=15)
        except:
            df_inscriptions = pd.DataFrame(columns=["ID", "Nombre_Completo", "Dojo", "Categoria", "Foto_Base64"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df_inscriptions)
            
        return df_matches, df_inscriptions
    except Exception as e:
        st.error(f"Error conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Guardar
def save_registration(participants):
    conn = get_connection()
    try:
        existing = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones")
        new_df = pd.DataFrame(participants)
        final = pd.concat([existing, new_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=final)
        load_data.clear()
        return True
    except: return False

def save_matches(df):
    conn = get_connection()
    conn.update(spreadsheet=SHEET_URL, worksheet="Matches", data=df)
    load_data.clear()

df_matches, df_inscriptions = load_data()

# --- LÓGICA DE SORTEO ---
def generate_bracket_for_category(category):
    # 1. Obtener inscritos de la categoría
    if df_inscriptions.empty: return False, "No hay inscritos."
    players = df_inscriptions[df_inscriptions['Categoria'] == category].to_dict('records')
    
    if len(players) < 2:
        return False, "Necesitas al menos 2 inscritos para generar llaves."
    
    # 2. Mezclar (Sorteo)
    random.shuffle(players)
    
    # 3. Limpiar matches anteriores de esta categoría
    global df_matches
    df_matches = df_matches[df_matches['Category'] != category]
    
    # 4. Crear estructura de Cuartos (Q1-Q4) - Top 8
    new_matches = []
    match_ids = ['Q1', 'Q2', 'Q3', 'Q4']
    
    # Llenar los 4 partidos de cuartos
    for i, mid in enumerate(match_ids):
        idx_p1 = i * 2
        idx_p2 = i * 2 + 1
        
        p1 = players[idx_p1] if idx_p1 < len(players) else None
        p2 = players[idx_p2] if idx_p2 < len(players) else None
        
        new_matches.append({
            "Category": category, "Match_ID": mid,
            "P1_Name": p1['Nombre_Completo'] if p1 else "", 
            "P1_Dojo": p1['Dojo'] if p1 else "",
            "P1_Foto": p1['Foto_Base64'] if p1 else "",
            "P1_Votes": 0,
            "P2_Name": p2['Nombre_Completo'] if p2 else "", 
            "P2_Dojo": p2['Dojo'] if p2 else "",
            "P2_Foto": p2['Foto_Base64'] if p2 else "",
            "P2_Votes": 0,
            "Winner": None, "Live": False
        })
        
    # Crear Semis y Final vacías
    for m in ['S1', 'S2', 'F1']:
        new_matches.append({
            "Category": category, "Match_ID": m,
            "P1_Name": "", "P1_Dojo": "", "P1_Foto": "", "P1_Votes": 0,
            "P2_Name": "", "P2_Dojo": "", "P2_Foto": "", "P2_Votes": 0,
            "Winner": None, "Live": False
        })
        
    # 5. Guardar
    df_new = pd.DataFrame(new_matches)
    df_final = pd.concat([df_matches, df_new], ignore_index=True)
    save_matches(df_final)
    return True, "Llaves generadas y sorteo realizado con éxito."

# --- 4. NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = "HOME"
if 'cat' not in st.session_state: st.session_state.cat = None
if 'page' not in st.session_state: st.session_state.page = 0

def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

# --- HEADER ---
def render_header():
    logo_org = "https://cdn-icons-png.flaticon.com/512/1603/1603754.png"
    st.markdown(f"""
    <div class="header-container">
        <div style="display:flex;align-items:center;gap:15px;">
            <img src="{logo_org}" height="50">
            <div>
                <h2 style="margin:0;font-size:20px;">WKB CHILE</h2>
                <small style="color:#FDB931;">OFFICIAL HUB</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. VISTA: INSCRIPCIÓN ---
if st.session_state.view == "REGISTER":
    render_header()
    if st.button("⬅ VOLVER"): go("HOME")
    st.markdown("### 📝 INSCRIPCIÓN OFICIAL")
    
    with st.form("reg"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        dojo = c2.text_input("Dojo")
        cat_sel = st.selectbox("Categoría", ALL_CATS)
        # Reducir tamaño de foto para no saturar Sheets
        foto = st.file_uploader("Foto (Max 2MB)", type=['jpg','png'])
        consent = st.checkbox("Acepto términos y condiciones")
        
        if st.form_submit_button("AGREGAR AL CARRITO"):
            if nombre and dojo and foto and consent:
                # Comprimir imagen
                img = Image.open(foto)
                img.thumbnail((150, 150)) # Thumbnail pequeño para la web
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=70)
                img_str = base64.b64encode(buf.getvalue()).decode()
                
                st.session_state.cart.append({
                    "ID": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
                    "Nombre_Completo": nombre, "Dojo": dojo, "Categoria": cat_sel,
                    "Foto_Base64": img_str, "Tipo_Inscripcion": "Indiv", "Codigo_Pago": "",
                    "Fecha_Inscripcion": str(datetime.datetime.now())
                })
                st.success("Agregado al carrito")
            else: st.error("Faltan datos")

    if st.session_state.cart:
        st.markdown("### 🛒 CARRITO")
        st.dataframe(pd.DataFrame(st.session_state.cart)[["Nombre_Completo","Categoria"]])
        code = st.text_input("Código Pago (Prueba: WKB2026)")
        if st.button("CONFIRMAR") and code == PAYMENT_CODE_TEST:
            for p in st.session_state.cart: p["Codigo_Pago"] = code
            save_registration(st.session_state.cart)
            st.session_state.cart = []
            st.balloons(); st.success("Inscrito!"); time.sleep(2); go("HOME")

# --- 6. VISTA HOME ---
elif st.session_state.view == "HOME":
    render_header()
    if st.button("📝 INSCRIPCIÓN", type="primary"): go("REGISTER")
    st.markdown("---")
    st.markdown("### 📂 CATEGORÍAS")
    
    # Paginación
    start = st.session_state.page * 6
    cols = st.columns(2)
    for i, c in enumerate(ALL_CATS[start:start+6]):
        if cols[i%2].button(c.replace("KUMITE - ","").replace("KATA - ","🥋 "), key=c): go("BRACKET", c)
    
    c1,c2 = st.columns(2)
    if c1.button("⬅ Prev") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    if c2.button("Next ➡") and start+6 < len(ALL_CATS): st.session_state.page += 1; st.rerun()

# --- 7. VISTA CATEGORÍA (LISTA O BRACKET) ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    render_header()
    c1, c2 = st.columns([1,4])
    with c1: 
        if st.button("⬅ INICIO"): go("HOME")
    with c2: st.markdown(f"### {cat}")

    # 1. VERIFICAR SI HAY LLAVES GENERADAS
    matches_cat = df_matches[df_matches['Category'] == cat]
    bracket_active = not matches_cat.empty

    # --- ADMIN SIDEBAR ---
    with st.sidebar:
        st.header("Admin Panel")
        if not st.session_state.get('is_admin'):
            if st.button("Login") and check_admin(st.text_input("Pwd",type="password")):
                st.session_state.is_admin = True; st.rerun()
        else:
            st.success("Admin OK")
            # GENERADOR DE LLAVES
            st.markdown("---")
            st.markdown("#### ⚙️ Gestión de Llaves")
            if st.button("🎲 GENERAR/RESETEAR SORTEO", type="primary"):
                success, msg = generate_bracket_for_category(cat)
                if success: st.success(msg); time.sleep(1); st.rerun()
                else: st.error(msg)
            
            # EDITOR DE RESULTADOS (Solo si hay bracket)
            if bracket_active:
                st.markdown("---")
                mid = st.selectbox("Editar Match", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
                row = matches_cat[matches_cat['Match_ID'] == mid].iloc[0]
                with st.form("edit"):
                    win = st.selectbox("Ganador", ["", row['P1_Name'], row['P2_Name']])
                    live = st.checkbox("Live", row['Live'])
                    if st.form_submit_button("Actualizar"):
                        # Actualizar ganador y pasar a siguiente ronda (Lógica simplificada)
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==mid)].index[0]
                        df_matches.at[idx, 'Winner'] = win
                        df_matches.at[idx, 'Live'] = live
                        
                        # Propagar a Semis/Final (Ejemplo básico para Q1->S1)
                        if win and 'Q' in mid:
                            dest = 'S1' if mid in ['Q1','Q2'] else 'S2'
                            slot = 'P1' if mid in ['Q1','Q3'] else 'P2'
                            s_idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==dest)].index
                            if not s_idx.empty:
                                df_matches.at[s_idx[0], f'{slot}_Name'] = win
                                df_matches.at[s_idx[0], f'{slot}_Foto'] = row['P1_Foto'] if win == row['P1_Name'] else row['P2_Foto']
                                df_matches.at[s_idx[0], f'{slot}_Dojo'] = row['P1_Dojo'] if win == row['P1_Name'] else row['P2_Dojo']
                        
                        # Propagar a Final (S -> F)
                        if win and 'S' in mid:
                            slot = 'P1' if mid == 'S1' else 'P2'
                            f_idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']=='F1')].index
                            if not f_idx.empty:
                                df_matches.at[f_idx[0], f'{slot}_Name'] = win
                                df_matches.at[f_idx[0], f'{slot}_Foto'] = row['P1_Foto'] if win == row['P1_Name'] else row['P2_Foto']
                                df_matches.at[f_idx[0], f'{slot}_Dojo'] = row['P1_Dojo'] if win == row['P1_Name'] else row['P2_Dojo']

                        save_matches(df_matches); st.rerun()

    # --- VISUALIZACIÓN ---
    if not bracket_active:
        # FASE 1: LISTA DE INSCRITOS
        st.info("🕒 Torneo no iniciado. Lista de inscritos:")
        inscritos = df_inscriptions[df_inscriptions['Categoria'] == cat]
        
        if inscritos.empty:
            st.warning("No hay inscritos aún.")
        else:
            for _, p in inscritos.iterrows():
                # Renderizar tarjeta
                img_src = f"data:image/jpeg;base64,{p['Foto_Base64']}" if p['Foto_Base64'] else "https://via.placeholder.com/50"
                st.markdown(f"""
                <div class="list-card">
                    <img src="{img_src}" class="list-avatar">
                    <div>
                        <div style="font-weight:bold; font-size:16px;">{p['Nombre_Completo']}</div>
                        <div style="color:#aaa; font-size:12px;">🥋 {p['Dojo']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        # FASE 2: BRACKET
        cat_df = matches_cat.set_index('Match_ID')
        
        def get_val(m, c): 
            try: return cat_df.at[m,c] 
            except: return ""

        def card(mid):
            p1, p2 = get_val(mid,'P1_Name'), get_val(mid,'P2_Name')
            img1 = f"data:image/jpeg;base64,{get_val(mid,'P1_Foto')}" if get_val(mid,'P1_Foto') else ""
            img2 = f"data:image/jpeg;base64,{get_val(mid,'P2_Foto')}" if get_val(mid,'P2_Foto') else ""
            
            # HTML Solo visual (Sin botones)
            live = '<span class="live-indicator"></span>' if get_val(mid,'Live') else ''
            
            html = f"""
            <div class="player-box border-red">
                {f'<img src="{img1}" class="player-img-small">' if img1 else ''}
                <div class="p-info">
                    <div class="p-name">{live} {p1 if p1 else "..."}</div>
                    <div class="p-dojo">{get_val(mid,'P1_Dojo')}</div>
                </div>
            </div>
            <div class="player-box border-white">
                {f'<img src="{img2}" class="player-img-small">' if img2 else ''}
                <div class="p-info">
                    <div class="p-name">{p2 if p2 else "..."}</div>
                    <div class="p-dojo">{get_val(mid,'P2_Dojo')}</div>
                </div>
                <div class="line-r"></div>
            </div>
            """
            return html

        # Render HTML Bracket
        st.html(f"""
        <div class="bracket-wrapper">
            <div class="bracket-container">
                <div class="round">
                    <div style="text-align:center;font-size:10px;margin-bottom:10px">CUARTOS</div>
                    {card('Q1')}<div style="height:20px"></div>{card('Q2')}<div style="height:20px"></div>
                    {card('Q3')}<div style="height:20px"></div>{card('Q4')}
                </div>
                <div class="round">
                    <div style="text-align:center;font-size:10px;margin-bottom:10px">SEMIS</div>
                    <div style="height:50px"></div>{card('S1')}<div style="height:100px"></div>{card('S2')}
                </div>
                <div class="round">
                    <div style="text-align:center;font-size:10px;margin-bottom:10px">FINAL</div>
                    <div style="height:120px"></div>{card('F1')}
                </div>
                <div class="round">
                    <div style="text-align:center;font-size:10px;margin-bottom:10px">CAMPEÓN</div>
                    <div style="height:120px"></div>
                    <div class="champion-box">{get_val('F1','Winner') if get_val('F1','Winner') else "?"} 🏆</div>
                </div>
            </div>
        </div>
        """)

        # BOTONES DE VOTACIÓN (Nativos de Streamlit)
        st.write("---")
        st.caption("🗳️ Votación del Público")
        cols = st.columns(4)
        for i, m in enumerate(['Q1', 'Q2', 'Q3', 'Q4']):
            p1, p2 = get_val(m, 'P1_Name'), get_val(m, 'P2_Name')
            if p1 and p2 and not get_val(m, 'Winner'):
                with cols[i]:
                    st.caption(f"Match {m}")
                    c_a, c_b = st.columns(2)
                    if c_a.button("🔴", key=f"r{m}"): 
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==m)].index[0]
                        df_matches.at[idx, 'P1_Votes'] = int(df_matches.at[idx, 'P1_Votes']) + 1
                        save_matches(df_matches); st.toast("Voto Rojo!")
                    if c_b.button("⚪", key=f"w{m}"):
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==m)].index[0]
                        df_matches.at[idx, 'P2_Votes'] = int(df_matches.at[idx, 'P2_Votes']) + 1
                        save_matches(df_matches); st.toast("Voto Blanco!")

    if not st.session_state.get('is_admin'):
        st.html("<script>setTimeout(function(){window.location.reload();}, 30000);</script>")
