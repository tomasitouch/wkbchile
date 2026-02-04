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
import urllib.parse

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Official Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

# Meta tags para responsive y PWA
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0e1117">
""", unsafe_allow_html=True)

# LINK GOOGLE SHEET
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

# --- 2. SEGURIDAD ---
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9" # Hash de "admin123"

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 3. ESTILOS CSS PRO (RESPONSIVE + HORIZONTAL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    @keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    
    .stApp { background-color: #0e1117; color: white; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, div, button { font-family: 'Roboto Condensed', sans-serif !important; text-transform: uppercase; }
    
    /* HEADER */
    .header-container { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 20px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;
    }
    .sponsor-logo { height: 35px; opacity: 0.7; filter: grayscale(100%); transition: 0.3s; }
    
    /* BOTONES NATIVOS STREAMLIT */
    div.stButton > button {
        width: 100%; background: #1f2937; color: #e5e7eb; border: 1px solid #374151;
        padding: 12px; border-radius: 6px; transition: 0.2s;
    }
    div.stButton > button:hover { border-color: #ef4444; color: #ef4444; transform: translateX(3px); }

    /* --- BRACKET HORIZONTAL --- */
    .bracket-wrapper {
        width: 100%;
        overflow-x: auto; 
        overflow-y: hidden;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 20px;
        margin-bottom: 20px;
    }
    
    .bracket-container { 
        display: flex; 
        justify-content: flex-start;
        min-width: 900px; /* Fuerza el ancho para scroll horizontal */
        padding: 10px;
    }
    
    .round { 
        min-width: 240px; 
        margin: 0 10px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-around; 
    }

    /* TARJETAS DE JUGADOR (VISUALES) */
    .player-box { 
        background: #1f2937; padding: 12px; margin: 8px 0; border-radius: 6px; 
        position: relative; z-index: 2; box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        border: 1px solid #374151; min-height: 70px; display: flex; flex-direction: column; justify-content: center;
    }
    .border-red { border-left: 5px solid #ef4444; background: linear-gradient(90deg, rgba(239,68,68,0.1) 0%, rgba(31,41,55,1) 100%); }
    .border-white { border-left: 5px solid #ffffff; background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(31,41,55,1) 100%); }
    
    .p-name { font-size: 14px; font-weight: bold; color: white; margin-bottom: 4px; }
    .p-details { font-size: 11px; color: #9ca3af; display: flex; justify-content: space-between; }
    .p-vote-bar { height: 4px; background: #374151; margin-top: 6px; border-radius: 2px; overflow: hidden; }
    .p-vote-fill { height: 100%; transition: width 0.5s ease; }
    
    /* CAMPEÓN */
    .champion-box { 
        background: radial-gradient(circle, #FDB931 0%, #d9a024 100%); 
        color: black !important; text-align: center; padding: 20px; 
        border-radius: 8px; font-weight: bold; font-size: 18px;
        box-shadow: 0 0 25px rgba(253, 185, 49, 0.4); animation: fadeIn 1.5s;
    }

    /* CONECTORES */
    .line-r { position: absolute; right: -22px; width: 22px; border-bottom: 2px solid #6b7280; top: 50%; z-index: 1; }
    .conn-v { position: absolute; right: -22px; width: 2px; background: #6b7280; top: 50%; z-index: 1; transform: translateY(-50%); }
    .live-indicator { display: inline-block; width: 8px; height: 8px; background-color: #ef4444; border-radius: 50%; margin-right: 6px; animation: pulse 1s infinite; }

    /* MEDIA QUERIES */
    @media (max-width: 768px) {
        .header-container { justify-content: center; text-align: center; }
        .bracket-wrapper { margin: 0 -1rem; width: calc(100% + 2rem); padding: 0 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# --- 4. GESTIÓN DE DATOS ---

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

# Rate Limiter (Anti-Spam)
class RateLimiter:
    def __init__(self): self.requests = {}
    def allow(self, uid):
        now = time.time()
        if uid in self.requests and now - self.requests[uid] < 5: return False
        self.requests[uid] = now
        return True

if 'limiter' not in st.session_state: st.session_state.limiter = RateLimiter()
if 'cart' not in st.session_state: st.session_state.cart = [] 
if 'voted_matches' not in st.session_state: st.session_state.voted_matches = set()

@st.cache_resource
def get_connection(): return st.connection("gsheets", type=GSheetsConnection)

# Cargar Datos Torneo
@st.cache_data(ttl=15)
def load_data():
    conn = get_connection()
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Hoja1", ttl=15)
        if df.empty or "Live" not in df.columns:
            data = []
            for cat in ALL_CATS:
                for m in ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']:
                    data.append({"Category": cat, "Match_ID": m, "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": None, "Live": False})
            df = pd.DataFrame(data)
            conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
        return df
    except: return pd.DataFrame()

# Guardar Inscripción
def save_registration(participants):
    conn = get_connection()
    try:
        try:
            existing = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones", ttl=0)
        except:
            existing = pd.DataFrame(columns=["ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", "Dojo", "Organizacion", "Telefono", "Email", "Categoria", "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64", "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID"])
        
        new_df = pd.DataFrame(participants)
        final_df = pd.concat([existing, new_df], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=final_df)
        return True
    except Exception as e:
        st.error(f"Error guardando: {e}")
        return False

def save_bracket(df):
    conn = get_connection()
    conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
    load_data.clear()

main_df = load_data()

# --- 5. NAVEGACIÓN ---
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
        <div class="header-title">
            <img src="{logo_org}" height="50" style="filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));">
            <div>
                <h2 style="margin:0; font-size: 20px; letter-spacing: 1px;">WKB CHILE</h2>
                <small style="color:#FDB931; font-weight:bold;">OFFICIAL HUB</small>
            </div>
        </div>
        <div style="font-size:10px; color:#888;">LIVE SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. VISTA: INSCRIPCIÓN ---
if st.session_state.view == "REGISTER":
    render_header()
    if st.button("⬅ VOLVER"): go("HOME")
    
    st.markdown("### 📝 INSCRIPCIÓN OFICIAL")
    
    with st.form("reg_form", clear_on_submit=True):
        st.caption("Datos del Competidor")
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        edad = c2.number_input("Edad", 4, 99)
        
        c3, c4, c5 = st.columns(3)
        peso = c3.number_input("Peso (kg)", 20.0, 150.0, step=0.5)
        estatura = c4.number_input("Estatura (cm)", 100, 220)
        grado = c5.selectbox("Grado", ["10º Kyu (Blanco)", "9º Kyu", "8º Kyu", "Cinturón Negro"])
        
        c6, c7 = st.columns(2)
        dojo = c6.text_input("Dojo")
        org = c7.text_input("Organización")
        contact = st.text_input("Teléfono (+569...)")
        
        cat_sel = st.selectbox("Categoría", ALL_CATS)
        foto = st.file_uploader("Foto Frontal (Carnet)", type=['jpg','png'])
        
        st.markdown("---")
        consent = st.checkbox("Acepto Consentimiento Informado")
        legal = st.checkbox("Acepto Descargo de Responsabilidad")
        
        added = st.form_submit_button("AGREGAR AL CARRITO")
        
        if added:
            if not (nombre and dojo and contact and consent and legal and foto):
                st.error("Faltan datos obligatorios o foto.")
            else:
                img_str = ""
                try:
                    bytes_data = foto.getvalue()
                    img_str = base64.b64encode(bytes_data).decode()
                except: pass
                
                pid = hashlib.md5((nombre + str(time.time())).encode()).hexdigest()[:8]
                
                participant = {
                    "ID": pid, "Nombre_Completo": nombre, "Edad": edad, "Peso": peso, 
                    "Estatura": estatura, "Grado": grado, "Dojo": dojo, "Organizacion": org, 
                    "Telefono": contact, "Email": "", "Categoria": cat_sel,
                    "Tipo_Inscripcion": "Pendiente", "Codigo_Pago": "", 
                    "Fecha_Inscripcion": str(datetime.datetime.now()),
                    "Foto_Base64": img_str[:50] + "..." if len(img_str)>50 else "",
                    "Full_Foto": img_str,
                    "Consentimiento": consent, "Descargo": legal, "Estado_Pago": "Pendiente", "Grupo_ID": ""
                }
                st.session_state.cart.append(participant)
                st.success("Participante agregado al carrito.")

    if st.session_state.cart:
        st.markdown("### 🛒 CARRITO DE INSCRIPCIÓN")
        df_cart = pd.DataFrame(st.session_state.cart)
        st.dataframe(df_cart[["Nombre_Completo", "Categoria", "Dojo"]], use_container_width=True)
        
        total = len(st.session_state.cart) * 15000
        st.markdown(f"**TOTAL A PAGAR:** :green[${total:,} CLP]")
        
        code = st.text_input("Ingresa Código de Pago (Transferencia)", placeholder="Ej: WKB2026")
        
        c_pay, c_clear = st.columns([2,1])
        if c_pay.button("CONFIRMAR INSCRIPCIÓN", type="primary"):
            if code == "WKB2026": # Código de prueba
                tipo = "Individual" if len(st.session_state.cart) == 1 else "Colectivo"
                group_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:6] if len(st.session_state.cart) > 1 else ""
                
                final_list = []
                for p in st.session_state.cart:
                    p["Tipo_Inscripcion"] = tipo
                    p["Codigo_Pago"] = code
                    p["Grupo_ID"] = group_id
                    p["Foto_Base64"] = p.pop("Full_Foto")
                    final_list.append(p)
                
                if save_registration(final_list):
                    st.balloons()
                    st.success("¡INSCRIPCIÓN COMPLETADA! Nos vemos en el tatami.")
                    st.session_state.cart = []
                    time.sleep(3)
                    go("HOME")
            else:
                st.error("Código de pago inválido.")
        
        if c_clear.button("Borrar Todo"):
            st.session_state.cart = []
            st.rerun()

# --- 7. VISTA HOME ---
elif st.session_state.view == "HOME":
    render_header()
    
    if st.button("📝 INSCRIPCIÓN (Individual / Equipo)", type="primary", use_container_width=True):
        go("REGISTER")
        
    st.markdown("---")
    st.markdown("### 🏆 SEGUIMIENTO DE LLAVES")
    
    CATS_PAGE = 6
    start = st.session_state.page * CATS_PAGE
    end = start + CATS_PAGE
    
    cols = st.columns(2)
    for i, c in enumerate(ALL_CATS[start:end]):
        label = c.replace("KUMITE - ", "").replace("KATA - ", "🥋 ")
        if cols[i%2].button(label, key=c, use_container_width=True): go("BRACKET", c)
    
    c1, c2, c3 = st.columns([1,2,1])
    if st.session_state.page > 0: 
        if c1.button("⬅ Prev"): st.session_state.page -= 1; st.rerun()
    if end < len(ALL_CATS): 
        if c3.button("Next ➡"): st.session_state.page += 1; st.rerun()

# --- 8. VISTA BRACKET HORIZONTAL (RESPONSIVE) ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    cat_df = main_df[main_df['Category'] == cat].set_index('Match_ID')
    
    def get_row(mid): 
        try: return cat_df.loc[mid]
        except: return pd.Series()
    def get_val(row, col): return row[col] if col in row and pd.notna(row[col]) else "..."

    def generate_share_link():
        import urllib.parse
        base_url = "https://tu-app.streamlit.app/"
        params = {"category": urllib.parse.quote(cat)}
        return f"{base_url}?{params}"

    render_header()
    
    c1, c2, c3 = st.columns([1,3,1])
    with c1:
        if st.button("⬅ INICIO"): go("HOME")
    with c2:
        st.markdown(f"<h3 style='text-align:center; color:#FDB931;'>{cat}</h3>", unsafe_allow_html=True)
    with c3:
        link = generate_share_link()
        st.markdown(f"<div style='text-align:right; font-size:10px;'><a href='{link}' style='color:#FDB931;'>🔗 Link</a></div>", unsafe_allow_html=True)
    
    # Admin
    with st.sidebar:
        if not st.session_state.get('is_admin'):
            if st.button("Admin") and check_admin(st.text_input("Pwd",type="password")):
                st.session_state.is_admin = True; st.rerun()
        else:
            st.success("Admin Mode")
            mid = st.selectbox("Edit Match", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
            with st.form("edit"):
                row = get_row(mid)
                n1 = st.text_input("Red", get_val(row,'P1_Name'))
                d1 = st.text_input("Dojo1", get_val(row,'P1_Dojo'))
                n2 = st.text_input("White", get_val(row,'P2_Name'))
                d2 = st.text_input("Dojo2", get_val(row,'P2_Dojo'))
                live = st.checkbox("Live", get_val(row,'Live'))
                win = st.selectbox("Winner", ["", n1, n2])
                if st.form_submit_button("Save"):
                    idx = main_df[(main_df['Category']==cat)&(main_df['Match_ID']==mid)].index
                    if not idx.empty:
                        main_df.at[idx[0],'P1_Name']=n1; main_df.at[idx[0],'P1_Dojo']=d1
                        main_df.at[idx[0],'P2_Name']=n2; main_df.at[idx[0],'P2_Dojo']=d2
                        main_df.at[idx[0],'Live']=live; main_df.at[idx[0],'Winner']=win
                        save_bracket(main_df); st.rerun()

    # GENERADOR VISUAL (HTML Puro - Sin Onclick)
    def card(mid):
        row = get_row(mid)
        p1, p2 = get_val(row,'P1_Name'), get_val(row,'P2_Name')
        d1, d2 = get_val(row,'P1_Dojo'), get_val(row,'P2_Dojo')
        v1 = int(row['P1_Votes']) if pd.notna(row['P1_Votes']) else 0
        v2 = int(row['P2_Votes']) if pd.notna(row['P2_Votes']) else 0
        tot = v1 + v2
        pct = (v1/tot*100) if tot > 0 else 50
        
        live = '<span class="live-indicator"></span>' if row.get('Live') else ''
        
        return f"""
        <div class="player-box border-red">
            <div class="p-name">{live} {p1 if p1 else "..."}</div>
            <div class="p-details"><span>{d1}</span><span>{int(pct)}%</span></div>
            <div class="p-vote-bar"><div style="width:{pct}%;height:100%;background:#ef4444"></div></div>
        </div>
        <div class="player-box border-white">
            <div class="p-name">{p2 if p2 else "..."}</div>
            <div class="p-details"><span>{d2}</span></div>
            <div class="line-r"></div>
        </div>
        """

    html = f"""
    <div class="bracket-wrapper">
        <div class="bracket-container">
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">CUARTOS</div>
                {card('Q1')}<div style="height:20px"></div>
                {card('Q2')}<div style="height:20px"></div>
                {card('Q3')}<div style="height:20px"></div>
                {card('Q4')}
            </div>
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">SEMIS</div>
                <div style="height:50px"></div>
                {card('S1')}
                <div style="height:100px"></div>
                {card('S2')}
            </div>
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">FINAL</div>
                <div style="height:120px"></div>
                {card('F1')}
            </div>
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">CAMPEÓN</div>
                <div style="height:120px"></div>
                <div class="champion-box">{get_val(get_row('F1'),'Winner')} 🏆</div>
            </div>
        </div>
    </div>
    <div style="text-align:center;color:#666;font-size:10px;margin-bottom:20px">Desliza horizontalmente para ver todo el cuadro ➡</div>
    """
    st.html(html)

    # --- BOTONES DE VOTACIÓN (NATIVOS) ---
    st.markdown("##### 📊 VOTACIÓN DEL PÚBLICO")
    
    def vote(mid, col):
        if not st.session_state.limiter.allow("user"): st.toast("⏳ Espera..."); return
        vote_key = f"{cat}_{mid}"
        if vote_key in st.session_state.voted_matches: st.toast("Ya votaste"); return
        
        idx = main_df[(main_df['Category']==cat)&(main_df['Match_ID']==mid)].index
        if not idx.empty:
            main_df.at[idx[0], col] = int(main_df.at[idx[0], col]) + 1
            save_bracket(main_df)
            st.session_state.voted_matches.add(vote_key)
            st.toast("Voto enviado!")

    cols = st.columns(4)
    for i, m in enumerate(['Q1','Q2','Q3','Q4']):
        row = get_row(m)
        p1, p2 = get_val(row,'P1_Name'), get_val(row,'P2_Name')
        if p1 and p2 and not get_val(row,'Winner'):
            with cols[i]:
                st.caption(f"Match {m}")
                c_a, c_b = st.columns(2)
                if c_a.button("🔴", key=f"r{m}"): vote(m, 'P1_Votes')
                if c_b.button("⚪", key=f"w{m}"): vote(m, 'P2_Votes')
    
    if not st.session_state.get('is_admin'):
        st.html("<script>setTimeout(function(){window.location.reload();}, 30000);</script>")
