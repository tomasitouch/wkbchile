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

# --- 2. ESTILOS CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    .stApp { background-color: #0e1117; color: white; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, div, button { font-family: 'Roboto Condensed', sans-serif !important; text-transform: uppercase; }
    
    /* HEADER */
    .header-container { 
        padding: 15px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; margin-bottom: 20px; display: flex; align-items: center; gap: 15px;
    }
    
    /* LISTA */
    .list-card {
        background: #1f2937; padding: 10px; border-radius: 8px; border: 1px solid #374151;
        display: flex; align-items: center; gap: 15px; margin-bottom: 8px;
    }
    .list-avatar { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 2px solid #FDB931; }

    /* BRACKET */
    .bracket-wrapper { width: 100%; overflow-x: auto; padding-bottom: 20px; -webkit-overflow-scrolling: touch; }
    .bracket-container { display: flex; min-width: 900px; padding: 10px; }
    .round { min-width: 220px; margin: 0 10px; display: flex; flex-direction: column; justify-content: space-around; }

    .player-box { 
        background: #1f2937; padding: 8px; margin: 6px 0; border-radius: 6px; 
        position: relative; z-index: 2; border: 1px solid #374151; min-height: 55px; 
        display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .img-mini { width: 35px; height: 35px; border-radius: 50%; object-fit: cover; background: #000; }
    .border-red { border-left: 4px solid #ef4444; }
    .border-white { border-left: 4px solid #ffffff; }
    
    .p-data { flex: 1; overflow: hidden; }
    .p-name { font-size: 12px; font-weight: bold; color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .p-dojo { font-size: 9px; color: #9ca3af; }

    .line-r { position: absolute; right: -22px; width: 22px; border-bottom: 2px solid #6b7280; top: 50%; z-index: 1; }
    .conn-v { position: absolute; right: -22px; width: 2px; background: #6b7280; top: 50%; z-index: 1; transform: translateY(-50%); }
    .live-dot { display: inline-block; width: 6px; height: 6px; background: #ef4444; border-radius: 50%; animation: pulse 1s infinite; margin-right: 4px;}
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    
    .champion-box { background: radial-gradient(#FDB931, #d9a024); color: black !important; text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; }
    
    /* BOTONES */
    div.stButton > button { width: 100%; border: 1px solid #374151; background: #1f2937; color: white; font-size: 12px; }
    div.stButton > button:hover { border-color: #FDB931; color: #FDB931; }
    
    /* VOTOS */
    .vote-container { background: #111; padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #333; }
    .vote-bar-bg { width: 100%; height: 6px; background: #333; border-radius: 3px; margin-top: 5px; display: flex; }
    .vote-bar-red { height: 100%; background: #ef4444; }
    .vote-bar-white { height: 100%; background: #fff; }
</style>
""", unsafe_allow_html=True)

# --- 3. CONEXIÓN Y DATOS ---
CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]
STATUS_OPTS = ["Inscripciones Abiertas", "Inscripciones Cerradas", "Torneo Activo"]

# RATE LIMITER
if 'limiter' not in st.session_state: 
    class RateLimiter:
        def __init__(self): self.reqs = {}
        def check(self, user):
            now = time.time()
            if user in self.reqs and now - self.reqs[user] < 2: return False
            self.reqs[user] = now; return True
    st.session_state.limiter = RateLimiter()

if 'voted_matches' not in st.session_state: st.session_state.voted_matches = set()
if 'cart' not in st.session_state: st.session_state.cart = []

@st.cache_resource
def get_connection(): return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    conn = get_connection()
    try:
        # Matches
        try:
            df_m = conn.read(spreadsheet=SHEET_URL, worksheet="Matches", ttl=10)
            if df_m.empty or "P1_Foto" not in df_m.columns: raise Exception
        except:
            df_m = pd.DataFrame(columns=["Category", "Match_ID", "P1_Name", "P1_Dojo", "P1_Foto", "P1_Votes", "P2_Name", "P2_Dojo", "P2_Foto", "P2_Votes", "Winner", "Live"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Matches", data=df_m)
            
        # Inscripciones
        try:
            df_i = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones", ttl=10)
            if 'Nombre_Completo' in df_i.columns: df_i = df_i.rename(columns={'Nombre_Completo': 'Nombre'})
        except:
            df_i = pd.DataFrame(columns=["ID", "Nombre", "Dojo", "Categoria", "Foto_Base64", "Estado"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df_i)

        # Config
        try:
            df_c = conn.read(spreadsheet=SHEET_URL, worksheet="Config", ttl=10)
            status = df_c.iloc[0]['Status']
        except:
            status = "Inscripciones Abiertas"
            conn.update(spreadsheet=SHEET_URL, worksheet="Config", data=pd.DataFrame([{"Status": status}]))

        return df_m, df_i, status
    except: return pd.DataFrame(), pd.DataFrame(), "Inscripciones Abiertas"

def save_reg(data):
    conn = get_connection()
    try:
        current = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones")
        final = pd.concat([current, pd.DataFrame(data)], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=final)
        load_data.clear()
        return True
    except: return False

def save_matches(df):
    get_connection().update(spreadsheet=SHEET_URL, worksheet="Matches", data=df)
    load_data.clear()

def save_status(s):
    get_connection().update(spreadsheet=SHEET_URL, worksheet="Config", data=pd.DataFrame([{"Status": s}]))
    load_data.clear()

df_matches, df_insc, tournament_status = load_data()

# --- SORTEO INTELIGENTE ---
def generate_bracket_for_category(category):
    # 1. Obtener inscritos
    if df_insc.empty: return False, "No hay base de datos de inscritos."
    
    # Filtro seguro
    players = df_insc[df_insc['Categoria'] == category].to_dict('records')
    
    if len(players) < 2: return False, f"Se necesitan mínimo 2 inscritos en {category}."
    
    # 2. Mezclar aleatoriamente
    random.shuffle(players)
    
    # 3. Preparar DataFrame limpio para esta categoría
    global df_matches
    # Eliminamos matches viejos de esta categoria para reescribirlos
    df_matches = df_matches[df_matches['Category'] != category]
    
    new_matches = []
    
    # 4. Asignar a Cuartos de Final (Q1-Q4)
    # Rellenamos hasta 8 espacios con None si faltan jugadores
    while len(players) < 8:
        players.append(None)
        
    match_ids = ['Q1', 'Q2', 'Q3', 'Q4']
    
    for i, mid in enumerate(match_ids):
        # Tomar pares: 0y1, 2y3, 4y5, 6y7
        idx_p1 = i * 2
        idx_p2 = i * 2 + 1
        
        p1 = players[idx_p1]
        p2 = players[idx_p2]
        
        # Crear fila del Match
        new_matches.append({
            "Category": category, 
            "Match_ID": mid,
            "P1_Name": p1.get('Nombre', '') if p1 else "", 
            "P1_Dojo": p1.get('Dojo', '') if p1 else "", 
            "P1_Foto": p1.get('Foto_Base64', '') if p1 else "", 
            "P1_Votes": 0,
            "P2_Name": p2.get('Nombre', '') if p2 else "", 
            "P2_Dojo": p2.get('Dojo', '') if p2 else "", 
            "P2_Foto": p2.get('Foto_Base64', '') if p2 else "",
            "P2_Votes": 0, 
            "Winner": None, # Ganador vacío al inicio
            "Live": False
        })
        
    # 5. Crear espacios vacíos para Semis y Final (se llenarán solos al ganar)
    for m in ['S1', 'S2', 'F1']:
        new_matches.append({
            "Category": category, "Match_ID": m, 
            "P1_Name": "", "P1_Dojo": "", "P1_Foto": "", "P1_Votes": 0, 
            "P2_Name": "", "P2_Dojo": "", "P2_Foto": "", "P2_Votes": 0, 
            "Winner": None, "Live": False
        })
        
    # 6. Guardar todo
    df_final = pd.concat([df_matches, pd.DataFrame(new_matches)], ignore_index=True)
    save_matches(df_final)
    return True, f"¡Sorteo realizado! {len([p for p in players if p])} luchadores asignados."

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.header("🔧 Panel de Control")
    if not st.session_state.get('is_admin'):
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Ingresar") and hashlib.sha256(pwd.encode()).hexdigest() == ADMIN_HASH:
            st.session_state.is_admin = True; st.rerun()
    else:
        st.success("Admin Activo")
        new_status = st.selectbox("Fase Torneo", STATUS_OPTS, index=STATUS_OPTS.index(tournament_status) if tournament_status in STATUS_OPTS else 0)
        if new_status != tournament_status: save_status(new_status); st.rerun()
        if st.button("Cerrar Sesión"): st.session_state.is_admin = False; st.rerun()

# --- 5. NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = "HOME"
if 'cat' not in st.session_state: st.session_state.cat = None
if 'page' not in st.session_state: st.session_state.page = 0

def go(view, cat=None):
    st.session_state.view = view; st.session_state.cat = cat; st.rerun()

# HEADER
st.markdown(f"""
<div class="header-container">
    <div><h2 style="margin:0;font-size:22px;">WKB CHILE</h2><small style="color:#FDB931;">OFFICIAL HUB | {tournament_status}</small></div>
    <div style="font-size:12px;background:#333;padding:5px 10px;border-radius:4px;">{tournament_status}</div>
</div>""", unsafe_allow_html=True)

# --- VISTAS ---

# HOME
if st.session_state.view == "HOME":
    if tournament_status == "Inscripciones Abiertas":
        if st.button("📝 IR A INSCRIPCIONES", type="primary"): go("REGISTER")
    
    st.markdown("### 📂 CATEGORÍAS")
    start = st.session_state.page * 6
    cols = st.columns(2)
    for i, c in enumerate(ALL_CATS[start:start+6]):
        label = c.replace("KUMITE - ","").replace("KATA - ","🥋 ")
        if cols[i%2].button(label, key=c, use_container_width=True): go("BRACKET", c)
    
    c1, c2 = st.columns(2)
    if c1.button("⬅") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    if c2.button("➡") and start+6 < len(ALL_CATS): st.session_state.page += 1; st.rerun()

# REGISTRO
elif st.session_state.view == "REGISTER":
    if st.button("⬅ VOLVER"): go("HOME")
    st.markdown("### 📝 INSCRIPCIÓN")
    
    if tournament_status != "Inscripciones Abiertas": st.error("Inscripciones Cerradas")
    else:
        with st.form("reg"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombre Completo")
            dojo = c2.text_input("Dojo")
            cat = st.selectbox("Categoría", ALL_CATS)
            foto = st.file_uploader("Foto (jpg/png)", type=['jpg','png'])
            if st.form_submit_button("AGREGAR"):
                if nom and dojo and foto:
                    img = Image.open(foto); img.thumbnail((150,150)); buf=io.BytesIO(); img.save(buf,"JPEG"); b64=base64.b64encode(buf.getvalue()).decode()
                    st.session_state.cart.append({"ID":hashlib.md5(nom.encode()).hexdigest()[:8], "Nombre":nom, "Dojo":dojo, "Categoria":cat, "Foto_Base64":b64, "Tipo":"Indiv", "Codigo_Pago":"", "Fecha":str(datetime.datetime.now())})
                    st.success("Agregado al carrito")
                else: st.error("Datos incompletos")
        
        if st.session_state.cart:
            st.markdown("#### 🛒 Carrito")
            st.dataframe(pd.DataFrame(st.session_state.cart)[["Nombre","Categoria"]])
            code = st.text_input("Código Pago (WKB2026)")
            if st.button("CONFIRMAR") and code == PAYMENT_CODE_TEST:
                for p in st.session_state.cart: p["Codigo_Pago"] = code
                save_reg(st.session_state.cart); st.session_state.cart = []; st.balloons(); st.success("Inscrito!"); time.sleep(2); go("HOME")

# BRACKET
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    render_header()
    if st.button("⬅ INICIO"): go("HOME")
    st.markdown(f"### {cat}")
    
    matches_cat = df_matches[df_matches['Category'] == cat]
    bracket_active = not matches_cat.empty

    # ADMIN
    if st.session_state.get('is_admin'):
        with st.sidebar:
            st.markdown("---")
            # BOTÓN CRÍTICO: GENERAR LLAVES
            if st.button("🎲 GENERAR SORTEO", type="primary"):
                s, m = generate_bracket_for_category(cat)
                if s: st.success(m); time.sleep(1); st.rerun()
                else: st.error(m)
            
            # Edición Manual
            if bracket_active:
                st.markdown("---")
                mid = st.selectbox("Editar", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
                r = matches_cat[matches_cat['Match_ID']==mid].iloc[0]
                with st.form("ed"):
                    win = st.selectbox("Ganador", ["", r['P1_Name'], r['P2_Name']])
                    live = st.checkbox("Live", r['Live'])
                    if st.form_submit_button("Guardar"):
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==mid)].index[0]
                        df_matches.at[idx,'Winner']=win; df_matches.at[idx,'Live']=live
                        # Lógica de Avance
                        if win:
                            dest, slot = ('S1','P1') if mid=='Q1' else ('S1','P2') if mid=='Q2' else ('S2','P1') if mid=='Q3' else ('S2','P2') if mid=='Q4' else ('F1','P1') if mid=='S1' else ('F1','P2') if mid=='S2' else (None,None)
                            if dest:
                                tidx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==dest)].index
                                if not tidx.empty:
                                    src_p = 'P1' if win==r['P1_Name'] else 'P2'
                                    df_matches.at[tidx[0],f'{slot}_Name'] = win
                                    df_matches.at[tidx[0],f'{slot}_Dojo'] = r[f'{src_p}_Dojo']
                                    df_matches.at[tidx[0],f'{slot}_Foto'] = r[f'{src_p}_Foto']
                        save_matches(df_matches); st.rerun()

    # VISUALIZACIÓN
    if tournament_status != "Torneo Activo" and not bracket_active:
        # LISTA
        st.info("📋 Inscritos (Llaves pendientes)")
        insc = df_insc[df_insc['Categoria'] == cat]
        if insc.empty: st.warning("Sin inscritos")
        else:
            for _, p in insc.iterrows():
                nombre = p.get('Nombre', p.get('Nombre_Completo', 'Participante'))
                img = f"data:image/jpeg;base64,{p.get('Foto_Base64','')}" if p.get('Foto_Base64') else "https://via.placeholder.com/50"
                st.markdown(f"""<div class="list-card"><img src="{img}" class="list-avatar"><div><div style="font-weight:bold;">{nombre}</div><div style="color:#aaa;font-size:12px;">🥋 {p.get('Dojo','')}</div></div></div>""", unsafe_allow_html=True)
    elif bracket_active:
        # BRACKET
        cat_df = matches_cat.set_index('Match_ID')
        def get_v(m,c): return cat_df.at[m,c] if m in cat_df.index else ""
        def card(mid):
            p1, p2 = get_v(mid,'P1_Name'), get_v(mid,'P2_Name')
            img1, img2 = get_v(mid,'P1_Foto'), get_v(mid,'P2_Foto')
            src1 = f"data:image/jpeg;base64,{img1}" if img1 else ""
            src2 = f"data:image/jpeg;base64,{img2}" if img2 else ""
            live = '<span class="live-dot"></span>' if get_v(mid,'Live') else ''
            return f"""<div class="player-box border-red">{f'<img src="{src1}" class="img-mini">' if src1 else ''}<div class="p-data"><div class="p-name">{live} {p1 if p1 else "..."}</div><div class="p-dojo">{get_v(mid,'P1_Dojo')}</div></div></div><div class="player-box border-white">{f'<img src="{src2}" class="img-mini">' if src2 else ''}<div class="p-data"><div class="p-name">{p2 if p2 else "..."}</div><div class="p-dojo">{get_v(mid,'P2_Dojo')}</div></div><div class="line-r"></div></div>"""

        st.html(f"""<div class="bracket-wrapper"><div class="bracket-container"><div class="round"><div style="text-align:center;font-size:10px">CUARTOS</div>{card('Q1')}<div style="height:20px"></div>{card('Q2')}<div style="height:20px"></div>{card('Q3')}<div style="height:20px"></div>{card('Q4')}</div><div class="round"><div style="text-align:center;font-size:10px">SEMIS</div><div style="height:50px"></div>{card('S1')}<div style="height:100px"></div>{card('S2')}</div><div class="round"><div style="text-align:center;font-size:10px">FINAL</div><div style="height:120px"></div>{card('F1')}</div><div class="round"><div style="text-align:center;font-size:10px">CAMPEÓN</div><div style="height:120px"></div><div class="champion-box">{get_v('F1','Winner') if get_v('F1','Winner') else "?"} 🏆</div></div></div></div>""")
        
        # Votación (Solo si Activo)
        if tournament_status == "Torneo Activo":
            cols = st.columns(4)
            for i, m in enumerate(['Q1','Q2','Q3','Q4','S1','S2','F1']):
                p1, p2 = get_v(m,'P1_Name'), get_v(m,'P2_Name')
                if p1 and p2 and not get_v(m,'Winner'):
                    v1, v2 = int(get_v(m,'P1_Votes')), int(get_v(m,'P2_Votes'))
                    tot = v1+v2 if v1+v2 > 0 else 1
                    with cols[i%4]:
                        st.markdown(f"**{m}**")
                        # Barra Progreso
                        st.markdown(f"""<div class="vote-container"><div style="display:flex;justify-content:space-between;font-size:10px"><span>🔴 {int(v1/tot*100)}%</span><span>⚪ {int(v2/tot*100)}%</span></div><div class="vote-bar-bg"><div class="vote-bar-red" style="width:{v1/tot*100}%"></div><div class="vote-bar-white" style="width:{v2/tot*100}%"></div></div></div>""", unsafe_allow_html=True)
                        
                        ca, cb = st.columns(2)
                        def vote(match, col):
                            if not st.session_state.limiter.check("user"): st.toast("⏳ Espera..."); return
                            idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==match)].index[0]
                            df_matches.at[idx, col] = int(df_matches.at[idx, col]) + 1
                            save_matches(df_matches); st.toast("Voto OK")
                        
                        if ca.button(f"🔴 {p1[:8]}..", key=f"r{m}"): vote(m, 'P1_Votes')
                        if cb.button(f"⚪ {p2[:8]}..", key=f"w{m}"): vote(m, 'P2_Votes')

    if not st.session_state.get('is_admin'): st.html("<script>setTimeout(function(){window.location.reload();}, 30000);</script>")
