import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import plotly.express as px
import uuid
import time
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB ALL AMERICAN 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES & CONFIGURACIÓN ---
# EL CODIGO DE INVITADO SE DEFINE AQUÍ (No necesitas tocar secrets)
CODIGO_VIP = "WKB2026" 

LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
PRECIO = 15000

CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# --- CSS RESPONSIVO & FUTURISTA ---
st.markdown("""
    <style>
    /* 1. FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');

    /* 2. FONDO GLOBAL */
    .stApp {
        background-color: #0e1117;
        background-image: radial-gradient(circle at 50% 0%, #2a0a0a 0%, #0e1117 60%);
        background-attachment: fixed;
    }
    
    /* 3. TIPOGRAFÍA */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase;
        color: #fff;
        text-shadow: 0 0 15px rgba(255, 43, 43, 0.6);
    }
    
    p, label, .stMarkdown, .stSelectbox, .stTextInput, .stNumberInput {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.1rem;
    }

    /* 4. TARJETAS DE VIDRIO (GLASSMORPHISM) */
    .glass-card {
        background: rgba(26, 28, 36, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #ff2b2b;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.3s ease;
    }

    /* 5. LOGO RESPONSIVO */
    .logo-container {
        text-align: center;
        padding: 20px 0;
    }
    .logo-container img {
        width: 300px; /* Tamaño PC */
        max-width: 80%; /* Adaptable a móvil */
        filter: drop-shadow(0 0 20px rgba(255,255,255,0.15));
        transition: transform 0.3s;
    }
    .logo-container img:hover {
        transform: scale(1.03);
    }
    
    .main-title {
        font-size: 3.5em; 
        letter-spacing: 5px; 
        margin-top: 10px;
        text-align: center;
    }

    /* 6. CUENTA REGRESIVA RESPONSIVA */
    .countdown-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap; /* Permite que baje de línea en móvil */
        gap: 15px;
        margin: 30px 0;
        font-family: 'Orbitron', sans-serif;
    }
    .time-unit {
        background: linear-gradient(145deg, #1a1c24, #0f1014);
        border: 1px solid #333;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        min-width: 80px;
        flex: 1 1 80px; /* Flexible */
    }
    .time-val {
        font-size: 2rem;
        font-weight: 900;
        color: #ff2b2b;
    }
    .time-label {
        font-size: 0.7rem;
        color: #888;
        letter-spacing: 1px;
    }

    /* 7. BOTONES NEON */
    .stButton>button {
        background: linear-gradient(90deg, #800000 0%, #ff2b2b 100%);
        color: white !important;
        font-family: 'Orbitron', sans-serif !important;
        border: none;
        border-radius: 6px;
        height: 50px;
        width: 100%;
        font-weight: bold;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(255, 43, 43, 0.6);
        transform: scale(1.01);
    }
    
    /* 8. INPUTS FORZADOS A DARK */
    .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {
        background-color: #12141a !important;
        border: 1px solid #444 !important;
        color: white !important;
    }
    
    /* 9. MEDIA QUERIES (AJUSTES PARA MOVIL) */
    @media only screen and (max-width: 600px) {
        .logo-container img { width: 200px; }
        .main-title { font-size: 2em; letter-spacing: 2px; }
        .glass-card { padding: 15px; }
        .time-unit { min-width: 60px; }
        .time-val { font-size: 1.5rem; }
    }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND ---

def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        return conn.read(worksheet="Inscripciones", ttl=0)
    except:
        return pd.DataFrame(columns=["ID", "Nombre", "Categoria", "Dojo", "Estado", "Fecha", "Metodo"])

def guardar_inscripcion(datos, metodo):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_existente = get_data()
        
        # Check duplicados
        if not df_existente.empty and datos['id'] in df_existente['ID'].values:
             return True

        nueva_fila = pd.DataFrame([{
            "ID": datos['id'],
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Nombre": datos['nombre'],
            "Email": datos['email'],
            "Dojo": datos['dojo'],
            "Categoria": datos['categoria'],
            "Telefono": datos['telefono'],
            "Edad": datos['edad'],
            "Estado": "CONFIRMADO",
            "Metodo": metodo
        }])
        
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error Database: {e}")
        return False

def mp_link(datos):
    try:
        sdk = mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
        base_url = st.secrets["general"]["public_url"]
        pref = {
            "items": [{"title": f"WKB 2026: {datos['categoria']}", "quantity": 1, "currency_id": "CLP", "unit_price": PRECIO}],
            "payer": {"email": datos['email']},
            "back_urls": {"success": f"{base_url}?status=approved", "failure": f"{base_url}?status=failure"},
            "auto_return": "approved",
            "external_reference": datos['id']
        }
        return sdk.preference().create(pref)["response"]["init_point"]
    except: return None

# --- UI COMPONENTS ---

def render_header():
    # Logo y Título Responsive
    st.markdown(f"""
        <div class="logo-container">
            <img src='{LOGO_URL}'> 
            <div class='main-title'>WKB CHILE <span style='color:#ff2b2b'>2026</span></div>
            <p style='color: #888; letter-spacing: 2px;'>ALL AMERICAN TOURNAMENT REGISTRATION</p>
        </div>
    """, unsafe_allow_html=True)

    # Lógica Countdown
    delta = FECHA_TORNEO - datetime.now()
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, _ = divmod(resto, 60)
    
    st.markdown(f"""
        <div class='countdown-container'>
            <div class='time-unit'><div class='time-val'>{dias}</div><div class='time-label'>DÍAS</div></div>
            <div class='time-unit'><div class='time-val'>{horas}</div><div class='time-label'>HRS</div></div>
            <div class='time-unit'><div class='time-val'>{minutos}</div><div class='time-label'>MIN</div></div>
        </div>
    """, unsafe_allow_html=True)

def render_stats(df):
    st.markdown("## 📡 LIVE ANALYTICS")
    
    if df.empty:
        st.info("System Initialization... Waiting for fighters.")
        return

    df_conf = df[df['Estado'] == 'Confirmado'] if 'Estado' in df.columns else df
    
    # KPIs en Grid
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Fighters", len(df_conf))
        st.metric("Categorías Activas", df_conf['Categoria'].nunique() if not df_conf.empty else 0)
    with col2:
        st.metric("Dojos", df_conf['Dojo'].nunique() if not df_conf.empty else 0)
        st.metric("Cupos Disponibles", 500 - len(df_conf))

    # Gráfico 1: Barras
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 📊 CATEGORY DENSITY")
    if not df_conf.empty and 'Categoria' in df_conf.columns:
        counts = df_conf['Categoria'].value_counts().reset_index()
        counts.columns = ['Cat', 'Count']
        
        fig = px.bar(counts, x='Count', y='Cat', orientation='h', text='Count',
                     color='Count', color_continuous_scale=['#440000', '#ff2b2b'])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family="Rajdhani"),
            xaxis=dict(showgrid=False, color='#666'), yaxis=dict(showgrid=False, color='#fff'),
            margin=dict(l=0, r=0, t=30, b=0), height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Gráfico 2: Premios
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 🏆 PRIZE TIERS")
    st.markdown("""
        <div style='display:flex; justify-content:space-between; border-bottom:1px solid #333; padding:10px;'>
            <span style='color:#FFD700; font-weight:bold; font-size:1.2em'>🥇 1ST PLACE</span>
            <span>GOLD MEDAL + CUP</span>
        </div>
        <div style='display:flex; justify-content:space-between; border-bottom:1px solid #333; padding:10px;'>
            <span style='color:#C0C0C0; font-weight:bold; font-size:1.2em'>🥈 2ND PLACE</span>
            <span>SILVER MEDAL + CUP</span>
        </div>
        <div style='display:flex; justify-content:space-between; padding:10px;'>
            <span style='color:#CD7F32; font-weight:bold; font-size:1.2em'>🥉 3RD PLACE</span>
            <span>BRONZE MEDAL</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_form():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 📝 FIGHTER REGISTRATION")
    
    with st.form("main_form"):
        # En móvil se apilarán automáticamente
        nombre = st.text_input("FULL NAME / NOMBRE")
        email = st.text_input("EMAIL ADDRESS")
        telefono = st.text_input("MOBILE / WHATSAPP")
        
        col_a, col_b = st.columns(2)
        with col_a: edad = st.number_input("AGE / EDAD", 18, 99)
        with col_b: dojo = st.text_input("DOJO / TEAM")
        
        categoria = st.selectbox("CATEGORY / CATEGORÍA", CATEGORIAS)
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("INITIATE PAYMENT SEQUENCE ►", use_container_width=True)
        
        if submitted:
            if nombre and email and dojo and telefono:
                st.session_state.tmp = {
                    "id": str(uuid.uuid4())[:8].upper(),
                    "nombre": nombre, "email": email, "telefono": telefono,
                    "edad": edad, "dojo": dojo, "categoria": categoria
                }
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("MISSING REQUIRED DATA FIELDS")
    st.markdown("</div>", unsafe_allow_html=True)

def render_payment():
    data = st.session_state.tmp
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    
    # Resumen
    st.markdown("### 🔐 CONFIRM DATA")
    st.markdown(f"""
    <div style='background:rgba(0,0,0,0.3); padding:15px; border-radius:8px; margin-bottom:20px;'>
        <b style='color:#ff2b2b'>{data['nombre']}</b><br>
        <small>{data['categoria']} | {data['dojo']}</small><br>
        <h2 style='margin:10px 0; color:#fff'>${PRECIO:,.0f} CLP</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("◄ EDIT DATA"):
        st.session_state.step = 1
        st.rerun()
    
    st.markdown("---")
    
    # 1. Pago MP
    link = mp_link(data)
    if link:
        st.link_button("💳 PAY WITH MERCADOPAGO", link, use_container_width=True, type="primary")
    else:
        st.error("Payment Gateway Error")

    # 2. Código Invitado
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("🎟️ HAVE AN INVITATION CODE?"):
        vip_code = st.text_input("Enter VIP Code", type="password")
        if st.button("APPLY CODE"):
            if vip_code == CODIGO_VIP:
                with st.spinner("Authorizing VIP Access..."):
                    if guardar_inscripcion(data, metodo="Cortesía/VIP"):
                        st.balloons()
                        st.success("VIP ACCESS GRANTED.")
                        del st.session_state.tmp
                        st.session_state.step = 1
                        time.sleep(2)
                        st.rerun()
            else:
                st.error("INVALID CODE")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- APP PRINCIPAL ---
def main():
    render_header()
    
    # Navegación
    tabs = st.tabs(["🏠 DASHBOARD", "📝 REGISTER", "⚙️ SYSTEM"])
    
    # Callback MP
    if "status" in st.query_params and st.query_params["status"] == "approved":
        if 'tmp' in st.session_state:
            if guardar_inscripcion(st.session_state.tmp, metodo="MercadoPago"):
                st.balloons()
                st.success("PAYMENT APPROVED. FIGHTER REGISTERED.")
                del st.session_state.tmp
                st.query_params.clear()
                time.sleep(2)
                st.rerun()

    # Tab 1: Stats
    with tabs[0]:
        df = get_data()
        render_stats(df)
    
    # Tab 2: Registro
    with tabs[1]:
        if 'step' not in st.session_state: st.session_state.step = 1
        if st.session_state.step == 1: render_form()
        else: render_payment()

    # Tab 3: Admin
    with tabs[2]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### ADMIN MAINFRAME")
        pwd = st.text_input("ENTER ROOT PASSWORD", type="password")
        if pwd == st.secrets["general"].get("admin_password", "admin"):
            df = get_data()
            st.dataframe(df, use_container_width=True)
            st.download_button("DOWNLOAD DATABASE", df.to_csv(index=False), "wkb_db.csv", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()


