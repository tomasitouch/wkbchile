import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import hashlib
import datetime
import base64
from PIL import Image
import io
import random

# --- 1. CONFIGURACIÓN GLOBAL ---
st.set_page_config(
    page_title="WKB Tournament Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="expanded" # Sidebar siempre visible
)

# Meta tags para móviles (PWA & Scroll)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#0e1117">
""", unsafe_allow_html=True)

# CONSTANTES
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
ADMIN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9" # admin123
PAYMENT_CODE = "WKB2026"

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]
STATUS_OPTS = ["Inscripciones Abiertas", "Inscripciones Cerradas", "Torneo Activo"]

# --- 2. ESTILOS CSS PROFESIONALES ---
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
    
    /* TARJETAS LISTA */
    .list-card {
        background: #1f2937; padding: 10px; border-radius: 8px; border: 1px solid #374151;
        display: flex; align-items: center; gap: 15px; margin-bottom: 8px; transition: 0.2s;
    }
    .list-card:hover { border-color: #FDB931; transform: translateX(5px); }
    .list-avatar { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 2px solid #FDB931; }

    /* BRACKET HORIZONTAL */
    .bracket-wrapper { width: 100%; overflow-x: auto; padding-bottom: 20px; -webkit-overflow-scrolling: touch; }
    .bracket-container { display: flex; min-width: 900px; padding: 10px; }
    .round { min-width: 220px; margin: 0 10px; display: flex; flex-direction: column; justify-content: space-around; }

    /* BOX JUGADOR BRACKET */
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

    /* CONECTORES & LIVE */
    .line-r { position: absolute; right: -22px; width: 22px; border-bottom: 2px solid #6b7280; top: 50%; z-index: 1; }
    .conn-v { position: absolute; right: -22px; width: 2px; background: #6b7280; top: 50%; z-index: 1; transform: translateY(-50%); }
    .live-dot { display: inline-block; width: 6px; height: 6px; background: #ef4444; border-radius: 50%; animation: pulse 1s infinite; margin-right: 4px;}
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    
    .champion-box { background: radial-gradient(#FDB931, #d9a024); color: black !important; text-align: center; padding: 15px; border-radius: 8px; font-weight: bold; }
    
    div.stButton > button { width: 100%; border: 1px solid #374151; background: #1f2937; color: white; }
    div.stButton > button:hover { border-color: #FDB931; color: #FDB931; }
</style>
""", unsafe_allow_html=True)

# --- 3. CONEXIÓN Y DATOS ---
@st.cache_resource
def get_connection(): return st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    conn = get_connection()
    try:
        # 1. Matches
        try:
            df_m = conn.read(spreadsheet=SHEET_URL, worksheet="Matches", ttl=10)
            if df_m.empty or "P1_Foto" not in df_m.columns: raise Exception
        except:
            df_m = pd.DataFrame(columns=["Category", "Match_ID", "P1_Name", "P1_Dojo", "P1_Foto", "P1_Votes", "P2_Name", "P2_Dojo", "P2_Foto", "P2_Votes", "Winner", "Live"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Matches", data=df_m)
            
        # 2. Inscripciones
        try:
            df_i = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones", ttl=10)
            if 'Nombre_Completo' in df_i.columns: df_i = df_i.rename(columns={'Nombre_Completo': 'Nombre'})
        except:
            df_i = pd.DataFrame(columns=["ID", "Nombre", "Dojo", "Categoria", "Foto_Base64", "Estado"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df_i)

        # 3. Config
        try:
            df_c = conn.read(spreadsheet=SHEET_URL, worksheet="Config", ttl=10)
            status = df_c.iloc[0]['Status']
        except:
            status = "Inscripciones Abiertas"
            conn.update(spreadsheet=SHEET_URL, worksheet="Config", data=pd.DataFrame([{"Status": status}]))

        return df_m, df_i, status
    except: return pd.DataFrame(), pd.DataFrame(), "Error"

# FUNCIONES DE GUARDADO
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

# ESTADO INICIAL
if 'cart' not in st.session_state: st.session_state.cart = []
if 'view' not in st.session_state: st.session_state.view = "HOME"
if 'cat' not in st.session_state: st.session_state.cat = None
if 'page' not in st.session_state: st.session_state.page = 0
if 'votes' not in st.session_state: st.session_state.votes = set()

df_matches, df_insc, tournament_status = load_data()

# --- 4. BARRA LATERAL (ADMIN GLOBAL) ---
with st.sidebar:
    st.header("🔧 Panel de Control")
    
    # Login Admin
    if not st.session_state.get('is_admin'):
        pwd = st.text_input("Contraseña Admin", type="password")
        if st.button("Ingresar"):
            if hashlib.sha256(pwd.encode()).hexdigest() == ADMIN_HASH:
                st.session_state.is_admin = True
                st.rerun()
            else: st.error("Contraseña incorrecta")
    
    # Menú Admin (Solo si logueado)
    if st.session_state.get('is_admin'):
        st.success("✅ Modo Administrador Activo")
        
        st.markdown("---")
        st.subheader("⚙️ Estado del Torneo")
        new_status = st.selectbox("Fase Actual:", STATUS_OPTS, index=STATUS_OPTS.index(tournament_status) if tournament_status in STATUS_OPTS else 0)
        
        if new_status != tournament_status:
            if st.button("💾 Actualizar Estado"):
                save_status(new_status)
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.is_admin = False
            st.rerun()

# --- 5. NAVEGACIÓN ---
def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

# HEADER VISUAL
st.markdown(f"""
<div class="header-container">
    <div><h2 style="margin:0;font-size:22px;">WKB CHILE</h2><small style="color:#FDB931;">OFFICIAL HUB</small></div>
    <div style="font-size:12px;background:#333;padding:5px 10px;border-radius:4px;">{tournament_status}</div>
</div>
""", unsafe_allow_html=True)

# --- 6. VISTAS ---

# === VISTA HOME ===
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
    if c1.button("⬅ Anterior") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    if c2.button("Siguiente ➡") and start+6 < len(ALL_CATS): st.session_state.page += 1; st.rerun()

# === VISTA REGISTRO ===
elif st.session_state.view == "REGISTER":
    if st.button("⬅ VOLVER"): go("HOME")
    st.markdown("### 📝 INSCRIPCIÓN")
    
    if tournament_status != "Inscripciones Abiertas":
        st.warning("Las inscripciones están cerradas.")
    else:
        with st.form("reg"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nombre Completo")
            dojo = c2.text_input("Dojo")
            cat = st.selectbox("Categoría", ALL_CATS)
            foto = st.file_uploader("Foto Carnet (Max 2MB)", type=['jpg','png'])
            if st.form_submit_button("AÑADIR"):
                if nom and dojo and foto:
                    img = Image.open(foto); img.thumbnail((150,150)); buf=io.BytesIO(); img.save(buf,"JPEG"); b64=base64.b64encode(buf.getvalue()).decode()
                    st.session_state.cart.append({"ID":hashlib.md5(nom.encode()).hexdigest()[:8], "Nombre":nom, "Dojo":dojo, "Categoria":cat, "Foto_Base64":b64, "Estado":"OK"})
                    st.success("Añadido al carrito")
                else: st.error("Datos incompletos")
        
        if st.session_state.cart:
            st.markdown("#### 🛒 Carrito")
            st.dataframe(pd.DataFrame(st.session_state.cart)[["Nombre","Categoria"]])
            code = st.text_input("Código Pago (Prueba: WKB2026)")
            if st.button("CONFIRMAR TODO") and code == PAYMENT_CODE:
                save_reg(st.session_state.cart)
                st.session_state.cart = []
                st.balloons(); st.success("Inscrito!"); time.sleep(2); go("HOME")

# === VISTA BRACKET/LISTA ===
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    c1,c2=st.columns([1,4])
    with c1: 
        if st.button("⬅"): go("HOME")
    with c2: st.markdown(f"### {cat}")

    # Filtrar datos de esta categoría
    cat_insc = df_insc[df_insc['Categoria'] == cat]
    cat_match = df_matches[df_matches['Category'] == cat]
    has_bracket = not cat_match.empty

    # --- ADMIN ACTIONS EN BRACKET ---
    if st.session_state.get('is_admin'):
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Gestión: {cat}**")
            
            # Generador de Llaves
            if st.button("🎲 GENERAR SORTEO", type="primary"):
                players = cat_insc.to_dict('records')
                if len(players) < 2: st.error("Mínimo 2 inscritos")
                else:
                    random.shuffle(players)
                    # Limpiar viejo
                    df_matches = df_matches[df_matches['Category']!=cat]
                    new_m = []
                    # Cuartos
                    for i, mid in enumerate(['Q1','Q2','Q3','Q4']):
                        p1 = players[i*2] if i*2 < len(players) else None
                        p2 = players[i*2+1] if i*2+1 < len(players) else None
                        new_m.append({
                            "Category":cat, "Match_ID":mid, 
                            "P1_Name": p1['Nombre'] if p1 else "", "P1_Dojo": p1['Dojo'] if p1 else "", "P1_Foto": p1['Foto_Base64'] if p1 else "", "P1_Votes":0,
                            "P2_Name": p2['Nombre'] if p2 else "", "P2_Dojo": p2['Dojo'] if p2 else "", "P2_Foto": p2['Foto_Base64'] if p2 else "", "P2_Votes":0,
                            "Winner":None, "Live":False
                        })
                    # Semis/Final
                    for m in ['S1','S2','F1']:
                        new_m.append({"Category":cat, "Match_ID":m, "P1_Name":"","P1_Dojo":"","P1_Foto":"","P1_Votes":0, "P2_Name":"","P2_Dojo":"","P2_Foto":"","P2_Votes":0, "Winner":None, "Live":False})
                    
                    final_df = pd.concat([df_matches, pd.DataFrame(new_m)], ignore_index=True)
                    save_matches(final_df)
                    st.success("Llave Generada!"); st.rerun()

            # Editor de Resultados
            if has_bracket:
                st.markdown("✏️ **Editar Match**")
                mid = st.selectbox("Seleccionar", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
                r = cat_match[cat_match['Match_ID']==mid].iloc[0]
                with st.form("match_edit"):
                    w = st.selectbox("Ganador", ["", r['P1_Name'], r['P2_Name']])
                    live = st.checkbox("En Vivo", r['Live'])
                    if st.form_submit_button("Guardar"):
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==mid)].index[0]
                        df_matches.at[idx,'Winner'] = w
                        df_matches.at[idx,'Live'] = live
                        
                        # Avance Automático
                        if w:
                            dest, slot = "", ""
                            if 'Q' in mid:
                                dest = 'S1' if mid in ['Q1','Q2'] else 'S2'
                                slot = 'P1' if mid in ['Q1','Q3'] else 'P2'
                            elif 'S' in mid:
                                dest = 'F1'
                                slot = 'P1' if mid == 'S1' else 'P2'
                            
                            if dest:
                                tidx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==dest)].index
                                if not tidx.empty:
                                    src = 'P1' if w == r['P1_Name'] else 'P2'
                                    df_matches.at[tidx[0], f'{slot}_Name'] = w
                                    df_matches.at[tidx[0], f'{slot}_Dojo'] = r[f'{src}_Dojo']
                                    df_matches.at[tidx[0], f'{slot}_Foto'] = r[f'{src}_Foto']
                        
                        save_matches(df_matches); st.rerun()

    # --- LÓGICA DE VISUALIZACIÓN ---
    
    # CASO 1: MODO LISTA (Inscripciones abiertas/cerradas o sin llave generada)
    if tournament_status != "Torneo Activo" or not has_bracket:
        st.info(f"📋 Lista de Participantes | Estado: {tournament_status}")
        if cat_insc.empty: st.warning("Sin inscritos.")
        else:
            for _, p in cat_insc.iterrows():
                # Fallback seguro para la foto
                img = f"data:image/jpeg;base64,{p['Foto_Base64']}" if p.get('Foto_Base64') else "https://via.placeholder.com/50"
                st.markdown(f"""
                <div class="list-card">
                    <img src="{img}" class="list-avatar">
                    <div>
                        <div style="font-weight:bold;">{p['Nombre']}</div>
                        <div style="font-size:12px;color:#aaa;">🥋 {p['Dojo']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # CASO 2: MODO BRACKET (Solo si Torneo Activo Y Llave existe)
    else:
        df_idx = cat_match.set_index('Match_ID')
        def get_v(m,c): return df_idx.at[m,c] if m in df_idx.index else ""
        
        def card(mid):
            p1, p2 = get_v(mid,'P1_Name'), get_v(mid,'P2_Name')
            i1 = f"data:image/jpeg;base64,{get_v(mid,'P1_Foto')}" if get_v(mid,'P1_Foto') else ""
            i2 = f"data:image/jpeg;base64,{get_v(mid,'P2_Foto')}" if get_v(mid,'P2_Foto') else ""
            live = '<span class="live-dot"></span>' if get_v(mid,'Live') else ''
            
            return f"""
            <div class="player-box border-red">
                {f'<img src="{i1}" class="img-mini">' if i1 else ''}
                <div class="p-data"><div class="p-name">{live} {p1 if p1 else "..."}</div><div class="p-dojo">{get_v(mid,'P1_Dojo')}</div></div>
            </div>
            <div class="player-box border-white">
                {f'<img src="{i2}" class="img-mini">' if i2 else ''}
                <div class="p-data"><div class="p-name">{p2 if p2 else "..."}</div><div class="p-dojo">{get_v(mid,'P2_Dojo')}</div></div>
                <div class="line-r"></div>
            </div>
            """

        # HTML Bracket
        st.html(f"""
        <div class="bracket-wrapper"><div class="bracket-container">
            <div class="round"><div style="text-align:center;font-size:10px">CUARTOS</div>{card('Q1')}<div style="height:20px"></div>{card('Q2')}<div style="height:20px"></div>{card('Q3')}<div style="height:20px"></div>{card('Q4')}</div>
            <div class="round"><div style="text-align:center;font-size:10px">SEMIS</div><div style="height:50px"></div>{card('S1')}<div style="height:100px"></div>{card('S2')}</div>
            <div class="round"><div style="text-align:center;font-size:10px">FINAL</div><div style="height:120px"></div>{card('F1')}</div>
            <div class="round"><div style="text-align:center;font-size:10px">CAMPEÓN</div><div style="height:120px"></div><div class="champion-box">{get_v('F1','Winner') if get_v('F1','Winner') else "?"} 🏆</div></div>
        </div></div>
        """)

        # Botones Votación
        st.markdown("---")
        st.caption("🗳️ Votación en Vivo")
        cols = st.columns(4)
        for i, m in enumerate(['Q1','Q2','Q3','Q4','S1','S2','F1']):
            p1, p2 = get_v(m,'P1_Name'), get_v(m,'P2_Name')
            if p1 and p2 and not get_v(m,'Winner'):
                with cols[i%4]:
                    st.markdown(f"**Match {m}**")
                    ca, cb = st.columns(2)
                    if ca.button("🔴", key=f"r{m}"):
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==m)].index[0]
                        df_matches.at[idx,'P1_Votes'] = int(df_matches.at[idx,'P1_Votes']) + 1
                        save_matches(df_matches); st.toast("Voto enviado")
                    if cb.button("⚪", key=f"w{m}"):
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==m)].index[0]
                        df_matches.at[idx,'P2_Votes'] = int(df_matches.at[idx,'P2_Votes']) + 1
                        save_matches(df_matches); st.toast("Voto enviado")

    if not st.session_state.get('is_admin'):
        st.html("<script>setTimeout(function(){window.location.reload();}, 30000);</script>")
