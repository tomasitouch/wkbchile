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

# Meta tags para responsive y PWA
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#0e1117">
""", unsafe_allow_html=True)

# CONFIGURACIÓN
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9" # admin123
PAYMENT_CODE_TEST = "WKB2026" 

# ESTADOS DEL TORNEO
STATUS_OPTIONS = ["Inscripciones Abiertas", "Inscripciones Cerradas", "Torneo Activo"]

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
        transition: transform 0.2s;
    }
    .list-card:hover { transform: translateX(5px); border-color: #FDB931; }
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
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

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
@st.cache_data(ttl=10)
def load_all_data():
    conn = get_connection()
    try:
        # 1. Matches
        try:
            df_matches = conn.read(spreadsheet=SHEET_URL, worksheet="Matches", ttl=10)
            if df_matches.empty or "P1_Foto" not in df_matches.columns: raise Exception("Empty")
        except:
            df_matches = pd.DataFrame(columns=["Category", "Match_ID", "P1_Name", "P1_Dojo", "P1_Foto", "P1_Votes", "P2_Name", "P2_Dojo", "P2_Foto", "P2_Votes", "Winner", "Live"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Matches", data=df_matches)

        # 2. Inscripciones
        try:
            df_insc = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones", ttl=10)
        except:
            df_insc = pd.DataFrame(columns=["ID", "Nombre", "Edad", "Peso", "Estatura", "Grado", "Dojo", "Org", "Contacto", "Categoria", "Tipo", "Codigo_Pago", "Foto_Base64", "Fecha"])
            conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df_insc)

        # 3. Config (Estado Torneo)
        try:
            df_config = conn.read(spreadsheet=SHEET_URL, worksheet="Config", ttl=10)
            status = df_config.iloc[0]['Status'] if not df_config.empty else "Inscripciones Abiertas"
        except:
            df_config = pd.DataFrame([{"Status": "Inscripciones Abiertas"}])
            conn.update(spreadsheet=SHEET_URL, worksheet="Config", data=df_config)
            status = "Inscripciones Abiertas"

        return df_matches, df_insc, status
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), "Error"

# Helpers de Guardado
def save_registration(participants):
    conn = get_connection()
    try:
        existing = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones")
        new_df = pd.DataFrame(participants)
        final = pd.concat([existing, new_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=final)
        load_all_data.clear()
        return True
    except: return False

def save_matches(df):
    conn = get_connection()
    conn.update(spreadsheet=SHEET_URL, worksheet="Matches", data=df)
    load_all_data.clear()

def save_status(new_status):
    conn = get_connection()
    df = pd.DataFrame([{"Status": new_status}])
    conn.update(spreadsheet=SHEET_URL, worksheet="Config", data=df)
    load_all_data.clear()

# Cargar todo al inicio
df_matches, df_inscriptions, tournament_status = load_all_data()

# --- LÓGICA DE SORTEO (GENERADOR DE LLAVES) ---
def generate_bracket_for_category(category):
    # 1. Obtener inscritos
    players = df_inscriptions[df_inscriptions['Categoria'] == category].to_dict('records')
    
    if len(players) < 2:
        return False, "Necesitas al menos 2 inscritos."
    
    # 2. Mezclar
    random.shuffle(players)
    
    # 3. Limpiar matches previos de esta categoría
    global df_matches
    # Filtramos para quitar los viejos y luego añadir nuevos (esto es una simplificación)
    # En producción idealmente se hace un update más selectivo
    df_matches = df_matches[df_matches['Category'] != category]
    
    new_matches = []
    
    # 4. Asignar Cuartos (Q1-Q4)
    match_ids = ['Q1', 'Q2', 'Q3', 'Q4']
    for i, mid in enumerate(match_ids):
        idx_p1 = i * 2
        idx_p2 = i * 2 + 1
        
        p1 = players[idx_p1] if idx_p1 < len(players) else None
        p2 = players[idx_p2] if idx_p2 < len(players) else None
        
        new_matches.append({
            "Category": category, "Match_ID": mid,
            "P1_Name": p1['Nombre'] if p1 else "", "P1_Dojo": p1['Dojo'] if p1 else "", "P1_Foto": p1['Foto_Base64'] if p1 else "",
            "P1_Votes": 0,
            "P2_Name": p2['Nombre'] if p2 else "", "P2_Dojo": p2['Dojo'] if p2 else "", "P2_Foto": p2['Foto_Base64'] if p2 else "",
            "P2_Votes": 0, "Winner": None, "Live": False
        })
        
    # Semis y Final vacías
    for m in ['S1', 'S2', 'F1']:
        new_matches.append({
            "Category": category, "Match_ID": m,
            "P1_Name": "", "P1_Dojo": "", "P1_Foto": "", "P1_Votes": 0,
            "P2_Name": "", "P2_Dojo": "", "P2_Foto": "", "P2_Votes": 0, "Winner": None, "Live": False
        })
        
    # 5. Guardar
    df_new = pd.DataFrame(new_matches)
    df_final = pd.concat([df_matches, df_new], ignore_index=True)
    save_matches(df_final)
    return True, "Sorteo realizado."

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
                <small style="color:#FDB931;">OFFICIAL HUB | {tournament_status.upper()}</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. VISTA: INSCRIPCIÓN ---
if st.session_state.view == "REGISTER":
    render_header()
    if st.button("⬅ VOLVER"): go("HOME")
    
    if tournament_status != "Inscripciones Abiertas":
        st.error("🚫 LAS INSCRIPCIONES ESTÁN CERRADAS")
    else:
        st.markdown("### 📝 INSCRIPCIÓN OFICIAL")
        tipo = st.radio("Tipo:", ["Individual", "Colectiva (1 Pago)"], horizontal=True)
        
        with st.form("reg"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre Completo")
            edad = c2.number_input("Edad", 4, 99)
            c3, c4 = st.columns(2)
            dojo = c3.text_input("Dojo")
            cat_sel = c4.selectbox("Categoría", ALL_CATS)
            
            # Foto
            foto = st.file_uploader("Foto Frontal (Max 2MB)", type=['jpg','png'])
            
            # Legales
            st.markdown("---")
            consent = st.checkbox("Acepto Consentimiento Informado")
            legal = st.checkbox("Acepto Descargo de Responsabilidad")
            
            if st.form_submit_button("AGREGAR AL CARRITO"):
                if nombre and dojo and foto and consent and legal:
                    # Procesar imagen
                    img = Image.open(foto)
                    img.thumbnail((150, 150))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=70)
                    img_str = base64.b64encode(buf.getvalue()).decode()
                    
                    st.session_state.cart.append({
                        "ID": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
                        "Nombre": nombre, "Edad": edad, "Dojo": dojo, "Categoria": cat_sel,
                        "Foto_Base64": img_str, "Tipo": tipo, "Codigo_Pago": "",
                        "Fecha": str(datetime.datetime.now()),
                        "Org": "", "Contacto": "", "Peso": 0, "Estatura": 0, "Grado": "" # Simplificado para demo
                    })
                    st.success("Agregado al carrito")
                else: st.error("Faltan datos")

        if st.session_state.cart:
            st.markdown("### 🛒 CARRITO")
            st.dataframe(pd.DataFrame(st.session_state.cart)[["Nombre","Categoria"]])
            code = st.text_input("Código Pago (Prueba: WKB2026)")
            if st.button("CONFIRMAR INSCRIPCIÓN") and code == PAYMENT_CODE_TEST:
                for p in st.session_state.cart: p["Codigo_Pago"] = code
                save_registration(st.session_state.cart)
                st.session_state.cart = []
                st.balloons(); st.success("Inscrito!"); time.sleep(2); go("HOME")

# --- 6. VISTA HOME ---
elif st.session_state.view == "HOME":
    render_header()
    
    if tournament_status == "Inscripciones Abiertas":
        if st.button("📝 IR A INSCRIPCIONES", type="primary", use_container_width=True): go("REGISTER")
    
    st.markdown("---")
    st.markdown("### 📂 CATEGORÍAS")
    
    start = st.session_state.page * 6
    cols = st.columns(2)
    for i, c in enumerate(ALL_CATS[start:start+6]):
        label = c.replace("KUMITE - ","").replace("KATA - ","🥋 ")
        if cols[i%2].button(label, key=c, use_container_width=True): go("BRACKET", c)
    
    c1,c2 = st.columns(2)
    if c1.button("⬅ Prev") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    if c2.button("Next ➡") and start+6 < len(ALL_CATS): st.session_state.page += 1; st.rerun()

# --- 7. VISTA CATEGORÍA (LISTA O BRACKET) ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    render_header()
    if st.button("⬅ INICIO"): go("HOME")
    st.markdown(f"### {cat}")

    # Verificar si hay llaves
    matches_cat = df_matches[df_matches['Category'] == cat]
    bracket_exists = not matches_cat.empty

    # --- ADMIN ---
    with st.sidebar:
        st.header("Admin Panel")
        if not st.session_state.get('is_admin'):
            if st.button("Login") and check_admin(st.text_input("Pwd",type="password")):
                st.session_state.is_admin = True; st.rerun()
        else:
            st.success("Admin OK")
            
            # CONTROL GLOBAL
            st.markdown("#### ⚙️ Config Torneo")
            new_status = st.selectbox("Estado", STATUS_OPTIONS, index=STATUS_OPTIONS.index(tournament_status))
            if new_status != tournament_status:
                save_status(new_status); st.rerun()
            
            # GENERADOR
            st.markdown("#### 🎲 Sorteo")
            if st.button("GENERAR LLAVE", type="primary"):
                s, m = generate_bracket_for_category(cat)
                if s: st.success(m); time.sleep(1); st.rerun()
                else: st.error(m)
            
            # EDITOR
            if bracket_exists:
                st.markdown("#### ✏️ Resultados")
                mid = st.selectbox("Match", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
                row = matches_cat[matches_cat['Match_ID'] == mid].iloc[0]
                with st.form("ed"):
                    win = st.selectbox("Ganador", ["", row['P1_Name'], row['P2_Name']])
                    live = st.checkbox("Live", row['Live'])
                    if st.form_submit_button("Guardar"):
                        idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==mid)].index[0]
                        df_matches.at[idx, 'Winner'] = win
                        df_matches.at[idx, 'Live'] = live
                        
                        # Lógica simple de avance (Q->S->F)
                        if win:
                            # Detectar destino
                            dest, slot = "", ""
                            if 'Q' in mid:
                                dest = 'S1' if mid in ['Q1','Q2'] else 'S2'
                                slot = 'P1' if mid in ['Q1','Q3'] else 'P2'
                            elif 'S' in mid:
                                dest = 'F1'
                                slot = 'P1' if mid == 'S1' else 'P2'
                            
                            if dest:
                                t_idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==dest)].index
                                if not t_idx.empty:
                                    df_matches.at[t_idx[0], f'{slot}_Name'] = win
                                    df_matches.at[t_idx[0], f'{slot}_Foto'] = row['P1_Foto'] if win == row['P1_Name'] else row['P2_Foto']
                                    df_matches.at[t_idx[0], f'{slot}_Dojo'] = row['P1_Dojo'] if win == row['P1_Name'] else row['P2_Dojo']
                        
                        save_matches(df_matches); st.rerun()

    # --- LOGICA VISUAL ---
    
    # 1. Si el torneo NO está activo O no hay llaves generadas -> MOSTRAR LISTA
    if tournament_status != "Torneo Activo" and not bracket_exists:
        st.info("📋 Lista de Participantes Inscritos")
        inscritos = df_inscriptions[df_inscriptions['Categoria'] == cat]
        
        if inscritos.empty: st.warning("No hay inscritos.")
        else:
            for _, p in inscritos.iterrows():
                img = f"data:image/jpeg;base64,{p['Foto_Base64']}" if p['Foto_Base64'] else "https://via.placeholder.com/50"
                st.markdown(f"""
                <div class="list-card">
                    <img src="{img}" class="list-avatar">
                    <div>
                        <div style="font-weight:bold;">{p['Nombre']}</div>
                        <div style="color:#aaa;font-size:12px;">🥋 {p['Dojo']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 2. Si el torneo ESTÁ ACTIVO O ya hay llaves -> MOSTRAR BRACKET
    else:
        if not bracket_exists:
            st.warning("Torneo activo pero sin llaves generadas para esta categoría.")
        else:
            cat_df = matches_cat.set_index('Match_ID')
            def get_v(m,c): return cat_df.at[m,c] if m in cat_df.index else ""

            def card(mid):
                p1, p2 = get_v(mid,'P1_Name'), get_v(mid,'P2_Name')
                img1 = f"data:image/jpeg;base64,{get_v(mid,'P1_Foto')}" if get_v(mid,'P1_Foto') else ""
                img2 = f"data:image/jpeg;base64,{get_v(mid,'P2_Foto')}" if get_v(mid,'P2_Foto') else ""
                live = '<span class="live-indicator"></span>' if get_v(mid,'Live') else ''
                
                return f"""
                <div class="player-box border-red">
                    {f'<img src="{img1}" class="player-img-small">' if img1 else ''}
                    <div class="p-info"><div class="p-name">{live} {p1 if p1 else "..."}</div><div class="p-dojo">{get_v(mid,'P1_Dojo')}</div></div>
                </div>
                <div class="player-box border-white">
                    {f'<img src="{img2}" class="player-img-small">' if img2 else ''}
                    <div class="p-info"><div class="p-name">{p2 if p2 else "..."}</div><div class="p-dojo">{get_v(mid,'P2_Dojo')}</div></div>
                    <div class="line-r"></div>
                </div>
                """

            st.html(f"""
            <div class="bracket-wrapper"><div class="bracket-container">
                <div class="round"><div style="text-align:center;font-size:10px">CUARTOS</div>{card('Q1')}<div style="height:20px"></div>{card('Q2')}<div style="height:20px"></div>{card('Q3')}<div style="height:20px"></div>{card('Q4')}</div>
                <div class="round"><div style="text-align:center;font-size:10px">SEMIS</div><div style="height:50px"></div>{card('S1')}<div style="height:100px"></div>{card('S2')}</div>
                <div class="round"><div style="text-align:center;font-size:10px">FINAL</div><div style="height:120px"></div>{card('F1')}</div>
                <div class="round"><div style="text-align:center;font-size:10px">CAMPEÓN</div><div style="height:120px"></div><div class="champion-box">{get_v('F1','Winner') if get_v('F1','Winner') else "?"} 🏆</div></div>
            </div></div>
            """)

            # Botones de Votación (Nativos)
            if tournament_status == "Torneo Activo":
                st.write("---")
                st.caption("🗳️ Votación en Vivo")
                cols = st.columns(4)
                for i, m in enumerate(['Q1','Q2','Q3','Q4','S1','S2','F1']):
                    p1, p2 = get_v(m,'P1_Name'), get_v(m,'P2_Name')
                    if p1 and p2 and not get_v(m,'Winner'):
                        with cols[i%4]:
                            st.markdown(f"**{m}**")
                            c_a, c_b = st.columns(2)
                            if c_a.button("🔴", key=f"r{m}"):
                                idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==m)].index[0]
                                df_matches.at[idx,'P1_Votes'] = int(df_matches.at[idx,'P1_Votes'])+1
                                save_matches(df_matches); st.toast("Voto Rojo")
                            if c_b.button("⚪", key=f"w{m}"):
                                idx = df_matches[(df_matches['Category']==cat)&(df_matches['Match_ID']==m)].index[0]
                                df_matches.at[idx,'P2_Votes'] = int(df_matches.at[idx,'P2_Votes'])+1
                                save_matches(df_matches); st.toast("Voto Blanco")

    # Auto-refresco público
    if not st.session_state.get('is_admin'):
        st.html("<script>setTimeout(function(){window.location.reload();}, 30000);</script>")
