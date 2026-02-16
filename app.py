import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import plotly.express as px
import plotly.graph_objects as go
import uuid
import time
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB WORLD CUP 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS FUTURISTA & ESTÉTICA DARK ---
st.markdown("""
    <style>
    /* Importar fuentes futuristas */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');

    /* Estilos Globales */
    .stApp {
        background-color: #0e1117;
        background-image: radial-gradient(circle at 50% 0%, #2a0a0a 0%, #0e1117 60%);
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #fff;
        text-shadow: 0 0 10px rgba(255, 43, 43, 0.5);
    }
    
    p, label, .stMarkdown {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 1.1rem;
    }

    /* Tarjetas estilo HUD (Glassmorphism) */
    .glass-card {
        background: rgba(26, 28, 36, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 3px solid #ff2b2b; /* Acento Rojo */
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(255, 43, 43, 0.2);
        border-color: #ff2b2b;
    }

    /* Cuenta Regresiva Digital */
    .countdown-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 30px 0;
        font-family: 'Orbitron', sans-serif;
    }
    .time-unit {
        background: linear-gradient(145deg, #1a1c24, #0f1014);
        border: 1px solid #333;
        padding: 15px 25px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        min-width: 100px;
    }
    .time-val {
        font-size: 2.5rem;
        font-weight: 900;
        color: #ff2b2b;
        text-shadow: 0 0 10px #ff2b2b;
    }
    .time-label {
        font-size: 0.8rem;
        color: #888;
        letter-spacing: 1px;
    }

    /* Botones Neon */
    .stButton>button {
        background: linear-gradient(90deg, #990000 0%, #ff2b2b 100%);
        color: white;
        font-family: 'Orbitron', sans-serif;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
        clip-path: polygon(10% 0, 100% 0, 100% 80%, 90% 100%, 0 100%, 0 20%);
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px #ff2b2b;
        transform: scale(1.02);
    }
    
    /* Input Fields Dark */
    .stTextInput>div>div, .stNumberInput>div>div, .stSelectbox>div>div {
        background-color: #161920;
        border: 1px solid #333;
        color: white;
        border-radius: 4px;
    }

    /* Métricas */
    div[data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif;
        color: #ff2b2b;
        text-shadow: 0 0 5px rgba(255, 43, 43, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
PRECIO = 5000
CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# --- LÓGICA BACKEND ---

def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        return conn.read(worksheet="Inscripciones", ttl=0)
    except:
        return pd.DataFrame(columns=["ID", "Nombre", "Categoria", "Dojo", "Estado", "Fecha"])

def guardar_inscripcion(datos):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_existente = get_data()
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
            "Metodo": "MercadoPago"
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
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown(f"""
            <div style='text-align: center; padding: 20px;'>
                <img src='{LOGO_URL}' width='120' style='filter: drop-shadow(0 0 10px rgba(255,255,255,0.3));'>
                <h1 style='margin-top: 10px; font-size: 3em;'>WKB CHILE <span style='color:#ff2b2b'>2026</span></h1>
                <p style='color: #888;'>WORLD CUP TOURNAMENT REGISTRATION SYSTEM</p>
            </div>
        """, unsafe_allow_html=True)

    # Countdown Logic
    delta = FECHA_TORNEO - datetime.now()
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, _ = divmod(resto, 60)
    
    st.markdown(f"""
        <div class='countdown-container'>
            <div class='time-unit'><div class='time-val'>{dias}</div><div class='time-label'>DÍAS</div></div>
            <div class='time-unit'><div class='time-val'>{horas}</div><div class='time-label'>HORAS</div></div>
            <div class='time-unit'><div class='time-val'>{minutos}</div><div class='time-label'>MIN</div></div>
        </div>
    """, unsafe_allow_html=True)

def render_stats(df):
    st.markdown("## 📡 LIVE TOURNAMENT ANALYTICS")
    
    if df.empty:
        st.info("Inicializando sistemas... Esperando data.")
        return

    df_conf = df[df['Estado'] == 'Confirmado'] if 'Estado' in df.columns else df
    
    # Métricas HUD
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Fighters Ready", len(df_conf), delta=f"+{len(df_conf)} this week")
    with c2: st.metric("Dojos", df_conf['Dojo'].nunique() if not df_conf.empty else 0)
    with c3: st.metric("Categories", df_conf['Categoria'].nunique() if not df_conf.empty else 0)
    with c4: st.metric("Slots Left", 500 - len(df_conf), delta_color="inverse")

    # Gráficos Plotly Dark Theme
    c_chart1, c_chart2 = st.columns([2, 1])
    
    with c_chart1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### 📊 CATEGORY DENSITY")
        
        counts = df_conf['Categoria'].value_counts().reset_index()
        counts.columns = ['Cat', 'Count']
        
        fig = px.bar(counts, x='Count', y='Cat', orientation='h', text='Count',
                     color='Count', color_continuous_scale=['#440000', '#ff2b2b'])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family="Rajdhani"),
            xaxis=dict(showgrid=False, color='#666'),
            yaxis=dict(showgrid=False, color='#fff'),
            margin=dict(l=0, r=0, t=0, b=0),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_chart2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### 🏆 PRIZE POOL")
        st.markdown("""
        <div style='font-family: "Orbitron"; font-size: 0.9em;'>
            <div style='margin-bottom:15px; border-bottom:1px solid #333; padding-bottom:10px;'>
                <span style='color:#FFD700; font-size:1.5em;'>1ST</span> 
                <span style='float:right; color:#ddd;'>GOLD + CUP</span>
            </div>
            <div style='margin-bottom:15px; border-bottom:1px solid #333; padding-bottom:10px;'>
                <span style='color:#C0C0C0; font-size:1.5em;'>2ND</span> 
                <span style='float:right; color:#ddd;'>SILVER</span>
            </div>
            <div>
                <span style='color:#CD7F32; font-size:1.5em;'>3RD</span> 
                <span style='float:right; color:#ddd;'>BRONZE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def render_form():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### 📝 FIGHTER REGISTRATION MODULE")
    
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("FULL NAME / NOMBRE")
            email = st.text_input("EMAIL ADDRESS")
            telefono = st.text_input("MOBILE / WHATSAPP")
        with col2:
            edad = st.number_input("AGE / EDAD", 18, 99)
            dojo = st.text_input("DOJO / TEAM")
            categoria = st.selectbox("CATEGORY / CATEGORÍA", CATEGORIAS)
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("INITIATE PAYMENT SEQUENCE ►", use_container_width=True)
        
        if submitted:
            if nombre and email and dojo:
                st.session_state.tmp = {
                    "id": str(uuid.uuid4())[:8].upper(),
                    "nombre": nombre, "email": email, "telefono": telefono,
                    "edad": edad, "dojo": dojo, "categoria": categoria
                }
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("MISSING DATA FIELDS")
    st.markdown("</div>", unsafe_allow_html=True)

def render_payment():
    data = st.session_state.tmp
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    
    with col1:
        st.markdown("### 🔐 SECURE CHECKOUT")
        st.markdown(f"""
        <div style='font-family: "Rajdhani"; font-size: 1.2em; line-height: 1.6;'>
            <span style='color:#888'>ID:</span> <span style='color:#fff'>{data['id']}</span><br>
            <span style='color:#888'>FIGHTER:</span> <span style='color:#ff2b2b'>{data['nombre']}</span><br>
            <span style='color:#888'>CATEGORY:</span> {data['categoria']}<br>
            <hr style='border-color: #333'>
            <span style='font-size: 1.5em; color:#fff'>TOTAL: ${PRECIO:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("◄ EDIT DATA"):
            st.session_state.step = 1
            st.rerun()

    with col2:
        st.markdown("### PAYMENT GATEWAY")
        link = mp_link(data)
        if link:
            st.link_button("💳 ACCESS MERCADOPAGO TERMINAL", link, use_container_width=True)
        else:
            st.error("CONNECTION ERROR")
    st.markdown("</div>", unsafe_allow_html=True)

# --- MAIN ---
def main():
    render_header()
    
    # Menu Tabs Futuristas
    tabs = st.tabs(["🏠 DASHBOARD", "📝 REGISTER", "⚙️ SYSTEM"])
    
    # Manejo de Retorno MP
    if "status" in st.query_params and st.query_params["status"] == "approved":
        if 'tmp' in st.session_state:
            if guardar_inscripcion(st.session_state.tmp):
                st.balloons()
                st.success("REGISTRATION CONFIRMED. WELCOME TO THE ARENA.")
                del st.session_state.tmp
                st.query_params.clear()

    with tabs[0]:
        df = get_data()
        render_stats(df)
    
    with tabs[1]:
        if 'step' not in st.session_state: st.session_state.step = 1
        if st.session_state.step == 1: render_form()
        else: render_payment()

    with tabs[2]:
        pwd = st.text_input("ADMIN ACCESS KEY", type="password")
        if pwd == st.secrets["general"].get("admin_password", "admin"):
            df = get_data()
            st.dataframe(df, use_container_width=True)
            st.download_button("DOWNLOAD DATABASE", df.to_csv(), "wkb_db.csv")

if __name__ == "__main__":
    main()
