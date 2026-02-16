import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import plotly.express as px
import plotly.graph_objects as go
import uuid
import re
import time
from datetime import datetime
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB World Cup 2026 | Futuristic Championship",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTES ---
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
PRECIO = 15000
CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# --- FUNCIONES DE DATOS Y LÓGICA ---
def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        return conn.read(worksheet="Inscripciones", ttl=0)
    except:
        return pd.DataFrame(columns=["ID", "Nombre", "Categoria", "Dojo", "Estado", "Fecha"])

def guardar_inscripcion(datos, metodo_pago="MercadoPago"):
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
            "Metodo": metodo_pago
        }])
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False

def crear_link_mp(datos):
    try:
        sdk = mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
        base_url = st.secrets["general"]["public_url"]
        preference = {
            "items": [{"title": f"WKB 2026 - {datos['categoria']}", "quantity": 1, "currency_id": "CLP", "unit_price": PRECIO}],
            "payer": {"email": datos['email']},
            "back_urls": {
                "success": f"{base_url}?status=approved",
                "failure": f"{base_url}?status=failure"
            },
            "auto_return": "approved",
            "external_reference": datos['id']
        }
        res = sdk.preference().create(preference)
        return res["response"]["init_point"]
    except:
        return None

# --- ESTILOS CSS PROFESIONALES FUTURISTAS ---
def apply_futuristic_styles():
    st.markdown("""
        <style>
        /* Importar fuentes tecnológicas */
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700;800&display=swap');

        /* Variables globales */
        :root {
            --primary: #00f3ff;
            --primary-dark: #0066ff;
            --secondary: #ff00e5;
            --accent: #ffff00;
            --dark: #0a0a0f;
            --darker: #050508;
            --light: #ffffff;
            --gray: #1a1a2e;
            --neon-glow: 0 0 10px rgba(0, 243, 255, 0.5);
            --cyber-glow: 0 0 20px rgba(255, 0, 229, 0.3);
        }

        /* Reset y estilos base */
        .stApp {
            background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
            color: var(--light);
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        p, div, span, label {
            font-family: 'Space Grotesk', sans-serif;
            color: rgba(255, 255, 255, 0.9);
        }

        /* Animaciones globales */
        @keyframes neonPulse {
            0% { opacity: 1; text-shadow: 0 0 10px var(--primary); }
            50% { opacity: 0.8; text-shadow: 0 0 20px var(--primary), 0 0 30px var(--secondary); }
            100% { opacity: 1; text-shadow: 0 0 10px var(--primary); }
        }

        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }

        @keyframes gridMove {
            0% { background-position: 0 0; }
            100% { background-position: 50px 50px; }
        }

        /* Fondo con grid futurista */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 243, 255, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
            animation: gridMove 20s linear infinite;
            z-index: 0;
        }

        /* Header con efecto cyber */
        .logo-container {
            text-align: center;
            margin-bottom: 30px;
            position: relative;
            z-index: 1;
            animation: float 6s ease-in-out infinite;
        }

        .logo-img {
            max-width: 180px;
            filter: drop-shadow(0 0 20px rgba(0, 243, 255, 0.5));
        }

        /* Cuenta Regresiva Cyberpunk */
        .countdown-box {
            background: rgba(10, 10, 15, 0.8);
            backdrop-filter: blur(10px);
            border: 2px solid;
            border-image: linear-gradient(45deg, var(--primary), var(--secondary)) 1;
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
            z-index: 1;
            box-shadow: 0 0 30px rgba(0, 243, 255, 0.2);
        }

        .countdown-box::before {
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, 
                transparent, 
                rgba(0, 243, 255, 0.1), 
                transparent);
            animation: neonPulse 3s infinite;
            z-index: -1;
        }

        .countdown-time {
            font-size: 4rem;
            font-weight: 800;
            font-family: 'Syne', sans-serif;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: neonPulse 2s infinite;
            letter-spacing: 5px;
        }

        .countdown-label {
            font-size: 1rem;
            color: var(--light);
            letter-spacing: 4px;
            text-transform: uppercase;
            font-weight: 300;
        }

        /* Tarjetas de Métricas Cyber */
        div[data-testid="stMetric"] {
            background: rgba(26, 26, 46, 0.7);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(0, 243, 255, 0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 0 30px rgba(0, 243, 255, 0.3);
            border-color: var(--primary);
        }

        div[data-testid="stMetric"]::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 243, 255, 0.2), transparent);
            transition: 0.5s;
        }

        div[data-testid="stMetric"]:hover::before {
            left: 100%;
        }

        /* Botones Cyber */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--dark);
            border: none;
            border-radius: 50px;
            padding: 12px 30px;
            font-weight: 700;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }

        .stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 30px rgba(0, 243, 255, 0.5);
            border-color: var(--light);
        }

        .stButton > button::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transition: 0.5s;
        }

        .stButton > button:hover::before {
            left: 100%;
        }

        /* Inputs Cyber */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            background: rgba(26, 26, 46, 0.7) !important;
            border: 1px solid rgba(0, 243, 255, 0.3) !important;
            border-radius: 10px !important;
            color: var(--light) !important;
            font-family: 'Space Grotesk', sans-serif !important;
            transition: all 0.3s ease !important;
        }

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.3) !important;
        }

        /* Sidebar Cyber */
        section[data-testid="stSidebar"] {
            background: rgba(5, 5, 8, 0.9);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(0, 243, 255, 0.3);
        }

        section[data-testid="stSidebar"] .stRadio > div {
            gap: 10px;
        }

        section[data-testid="stSidebar"] .stRadio > div > label {
            background: rgba(26, 26, 46, 0.5);
            padding: 12px 20px;
            border-radius: 10px;
            border: 1px solid transparent;
            transition: all 0.3s ease;
            font-weight: 500;
        }

        section[data-testid="stSidebar"] .stRadio > div > label:hover {
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
            transform: translateX(5px);
        }

        section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
            background: linear-gradient(135deg, rgba(0, 243, 255, 0.2), rgba(255, 0, 229, 0.2));
            border-color: var(--primary);
        }

        /* Tablas Cyber */
        .stDataFrame {
            background: rgba(26, 26, 46, 0.7) !important;
            border-radius: 15px !important;
            overflow: hidden !important;
            border: 1px solid rgba(0, 243, 255, 0.3) !important;
        }

        .stDataFrame th {
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            color: var(--dark) !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            font-size: 0.9rem !important;
        }

        .stDataFrame td {
            color: var(--light) !important;
            border-bottom: 1px solid rgba(0, 243, 255, 0.1) !important;
        }

        /* Panel Admin Cyber */
        .admin-panel {
            background: rgba(26, 26, 46, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(0, 243, 255, 0.3);
            margin-top: 20px;
        }

        /* Premios Cyber */
        .premios-box {
            background: rgba(26, 26, 46, 0.7);
            backdrop-filter: blur(10px);
            padding: 25px;
            border-radius: 20px;
            border: 1px solid rgba(255, 0, 229, 0.3);
            box-shadow: 0 0 30px rgba(255, 0, 229, 0.2);
        }

        .premios-box h4 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            text-align: center;
        }

        .premios-box ul {
            list-style: none;
            padding: 0;
        }

        .premios-box li {
            padding: 10px;
            margin-bottom: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border-left: 3px solid;
            transition: all 0.3s ease;
        }

        .premios-box li:nth-child(1) { border-left-color: #ffd700; }
        .premios-box li:nth-child(2) { border-left-color: #c0c0c0; }
        .premios-box li:nth-child(3) { border-left-color: #cd7f32; }

        .premios-box li:hover {
            transform: translateX(5px);
            background: rgba(255, 255, 255, 0.1);
        }

        /* Mensajes de éxito/error */
        .stAlert {
            background: rgba(26, 26, 46, 0.9) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid var(--primary) !important;
            border-radius: 15px !important;
            color: var(--light) !important;
        }

        .stSuccess {
            background: rgba(0, 255, 0, 0.1) !important;
            border-color: #00ff00 !important;
        }

        .stError {
            background: rgba(255, 0, 0, 0.1) !important;
            border-color: #ff0000 !important;
        }

        /* Scrollbar Cyber */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: var(--darker);
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 5px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, var(--secondary), var(--primary));
        }

        /* Efecto de partículas flotantes */
        .particle {
            position: fixed;
            width: 2px;
            height: 2px;
            background: var(--primary);
            border-radius: 50%;
            pointer-events: none;
            opacity: 0.5;
            animation: float 6s infinite;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .countdown-time {
                font-size: 2.5rem;
            }
            
            h1 {
                font-size: 1.8rem;
            }
        }
        </style>
        
        <!-- Partículas flotantes -->
        <div class="particle" style="top: 10%; left: 20%;"></div>
        <div class="particle" style="top: 30%; right: 15%;"></div>
        <div class="particle" style="bottom: 20%; left: 30%;"></div>
        <div class="particle" style="bottom: 40%; right: 40%;"></div>
        <div class="particle" style="top: 70%; left: 60%;"></div>
        
        <script>
        // Script para crear partículas dinámicas
        function createParticle() {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animation = 'float ' + (3 + Math.random() * 4) + 's infinite';
            particle.style.opacity = Math.random() * 0.5;
            document.body.appendChild(particle);
            
            setTimeout(() => {
                particle.remove();
            }, 6000);
        }
        
        // Crear partículas cada 500ms
        setInterval(createParticle, 500);
        </script>
    """, unsafe_allow_html=True)

# --- COMPONENTES VISUALES MEJORADOS ---
def mostrar_header():
    st.markdown(f"""
        <div class='logo-container'>
            <img src='{LOGO_URL}' class='logo-img'>
            <h1>⚡ WKB CHILE WORLD CUP 2026 ⚡</h1>
            <p style="text-align: center; font-size: 1.2rem; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                FUTURISTIC CHAMPIONSHIP
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Lógica de Cuenta Regresiva mejorada
    ahora = datetime.now()
    restante = FECHA_TORNEO - ahora
    dias = restante.days
    horas, resto = divmod(restante.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    
    st.markdown(f"""
        <div class='countdown-box'>
            <div class='countdown-label'>⚡ CUENTA REGRESIVA ⚡</div>
            <div class='countdown-time'>{dias:03d} : {horas:02d} : {minutos:02d} : {segundos:02d}</div>
            <div class='countdown-label'>DÍAS : HORAS : MIN : SEG</div>
            <div class='countdown-label' style="margin-top: 10px;">24 ABRIL 2026 - ARENA SANTIAGO</div>
        </div>
    """, unsafe_allow_html=True)

def dashboard_avanzado(df):
    st.markdown("### 📊 ANALYTICS DEL TORNEO")
    
    if df.empty:
        st.info("⚡ Esperando primeros registros para generar gráficos...")
        return

    # Filtro de datos confirmados
    df = df[df['Estado'] == 'CONFIRMADO'] if 'Estado' in df.columns else df

    # KPIs mejorados
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric(
            label="TOTAL INSCRITOS", 
            value=f"{len(df)}", 
            delta="⚡",
            delta_color="off"
        )
    
    with c2:
        dojos_count = df['Dojo'].nunique() if 'Dojo' in df.columns else 0
        st.metric(
            label="DOJOS ACTIVOS", 
            value=f"{dojos_count}", 
            delta="🏢",
            delta_color="off"
        )
    
    with c3:
        cats_count = df['Categoria'].nunique() if 'Categoria' in df.columns else 0
        st.metric(
            label="CATEGORÍAS", 
            value=f"{cats_count}/10", 
            delta="🎯",
            delta_color="off"
        )
    
    with c4:
        cupos_restantes = max(0, 500 - len(df))
        st.metric(
            label="CUPOS DISPONIBLES", 
            value=f"{cupos_restantes}", 
            delta="🎟️",
            delta_color="off"
        )

    # Gráfico 1: Inscritos por Categoría (Barras Horizontales Interactivas)
    if 'Categoria' in df.columns:
        conteo_cat = df['Categoria'].value_counts().reset_index()
        conteo_cat.columns = ['Categoría', 'Inscritos']
        
        fig_bar = px.bar(
            conteo_cat, 
            x='Inscritos', 
            y='Categoría', 
            orientation='h',
            title="⚡ COMPETITIVIDAD POR CATEGORÍA",
            text='Inscritos',
            color='Inscritos',
            color_continuous_scale=[[0, '#00f3ff'], [0.5, '#ff00e5'], [1, '#ffff00']]
        )
        
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_family="Space Grotesk",
            font_color="white",
            title_font_family="Syne",
            title_font_color="#00f3ff",
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        
        fig_bar.update_traces(
            textfont_color='white',
            textposition='outside',
            marker_line_color='white',
            marker_line_width=1,
            opacity=0.8
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

    # Sección Premios Mejorada
    st.markdown("### 🏆 DISPUTA POR EL PODIO")
    
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        # Gráfico Sunburst mejorado
        if 'Dojo' in df.columns and 'Categoria' in df.columns:
            fig_sun = px.sunburst(
                df, 
                path=['Categoria', 'Dojo'], 
                title="⚡ DISTRIBUCIÓN DE FUERZA (CATEGORÍA > DOJO)",
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            
            fig_sun.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_family="Space Grotesk",
                font_color="white",
                title_font_family="Syne",
                title_font_color="#ff00e5"
            )
            
            st.plotly_chart(fig_sun, use_container_width=True)

    with col_g2:
        st.markdown("""
        <div class='premios-box'>
            <h4>🏆 PREMIOS EN JUEGO</h4>
            <ul>
                <li>🥇 <b>1er Lugar:</b> Copa Gran Campeón + Medalla Oro + Certificado + Pase a Internacional</li>
                <li>🥈 <b>2do Lugar:</b> Copa Finalista + Medalla Plata + Certificado</li>
                <li>🥉 <b>3er Lugar:</b> Medalla Bronce + Certificado + Kit Deportivo</li>
            </ul>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <p style="text-align: center; font-size: 0.9rem;">
                <b>MEDALLAS EN JUEGO:</b> 30 (3 por categoría)<br>
                <b>⚡ VALOR TOTAL: $2.500.000 CLP ⚡</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Gráfico de torta para distribución por género (si hay datos)
        if 'Categoria' in df.columns:
            femenino = df[df['Categoria'].str.contains('Femenino', case=False)].shape[0]
            masculino = df[~df['Categoria'].str.contains('Femenino', case=False)].shape[0]
            
            if femenino + masculino > 0:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Masculino', 'Femenino'],
                    values=[masculino, femenino],
                    marker_colors=['#00f3ff', '#ff00e5'],
                    textinfo='label+percent',
                    textfont_color='white',
                    hole=0.3
                )])
                
                fig_pie.update_layout(
                    title="⚡ DISTRIBUCIÓN POR GÉNERO",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_family="Space Grotesk",
                    font_color="white",
                    title_font_family="Syne",
                    title_font_color="#00f3ff",
                    showlegend=False,
                    height=250,
                    margin=dict(t=50, b=0, l=0, r=0)
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)

def formulario_inscripcion():
    st.markdown("### 📝 FICHA DE COMPETIDOR")
    st.markdown("<p style='margin-bottom: 30px;'>Completa tus datos para acceder al sistema de pago seguro</p>", unsafe_allow_html=True)
    
    with st.form("form_registro"):
        c1, c2 = st.columns(2)
        
        with c1:
            nombre = st.text_input("👤 NOMBRE COMPLETO *", placeholder="Ej: Juan Pérez González")
            email = st.text_input("📧 EMAIL *", placeholder="ejemplo@correo.com")
            telefono = st.text_input("📱 TELÉFONO", placeholder="+56 9 1234 5678")
        
        with c2:
            edad = st.number_input("🎂 EDAD", min_value=18, max_value=99, step=1)
            dojo = st.text_input("🥋 DOJO / ESCUELA *", placeholder="Ej: Kyokushin Chile")
            categoria = st.selectbox("🏆 CATEGORÍA *", CATEGORIAS)
        
        st.markdown("<p style='font-size: 0.8rem; color: rgba(255,255,255,0.5);'>* Campos obligatorios</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("⚡ IR AL PAGO SEGURO ⚡", use_container_width=True)
        
        if submitted:
            if nombre and email and dojo:
                if '@' not in email or '.' not in email:
                    st.error("❌ Email inválido")
                else:
                    st.session_state.temp_data = {
                        "id": str(uuid.uuid4())[:8].upper(),
                        "nombre": nombre, 
                        "email": email, 
                        "telefono": telefono,
                        "edad": edad, 
                        "dojo": dojo, 
                        "categoria": categoria
                    }
                    st.session_state.step = 2
                    st.rerun()
            else:
                st.warning("⚠️ Completa todos los campos obligatorios")

def pasarela_pago():
    data = st.session_state.temp_data
    st.success("✅ DATOS VALIDADOS CORRECTAMENTE")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("""
        <div style="background: rgba(26, 26, 46, 0.7); backdrop-filter: blur(10px); padding: 25px; border-radius: 15px; border: 1px solid rgba(0, 243, 255, 0.3);">
            <h4 style="margin-bottom: 20px;">📋 RESUMEN DE INSCRIPCIÓN</h4>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <table style="width: 100%; color: white;">
            <tr>
                <td style="padding: 8px 0;"><b>Atleta:</b></td>
                <td style="padding: 8px 0;">{data['nombre']}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0;"><b>Categoría:</b></td>
                <td style="padding: 8px 0;">{data['categoria']}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0;"><b>Dojo:</b></td>
                <td style="padding: 8px 0;">{data['dojo']}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0;"><b>Email:</b></td>
                <td style="padding: 8px 0;">{data['email']}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0;"><b>Teléfono:</b></td>
                <td style="padding: 8px 0;">{data['telefono'] or 'No especificado'}</td>
            </tr>
            <tr>
                <td style="padding: 15px 0 0 0;"><b>TOTAL A PAGAR:</b></td>
                <td style="padding: 15px 0 0 0; color: #00f3ff; font-size: 1.3rem;"><b>${PRECIO:,.0f} CLP</b></td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("✏️ EDITAR DATOS", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
            
    with c2:
        st.markdown("""
        <div style="background: rgba(26, 26, 46, 0.7); backdrop-filter: blur(10px); padding: 25px; border-radius: 15px; border: 1px solid rgba(255, 0, 229, 0.3);">
            <h4 style="margin-bottom: 20px;">💳 MÉTODO DE PAGO</h4>
        """, unsafe_allow_html=True)
        
        link = crear_link_mp(data)
        if link:
            st.markdown("""
            <p style="text-align: center; margin-bottom: 20px;">
                <span style="background: rgba(0, 243, 255, 0.1); padding: 5px 15px; border-radius: 50px; font-size: 0.9rem;">
                    ⚡ PAGO SEGURO CON MERCADO PAGO ⚡
                </span>
            </p>
            """, unsafe_allow_html=True)
            
            st.link_button("🔒 PAGAR AHORA CON MERCADO PAGO", link, use_container_width=True)
            
            st.markdown("""
            <div style="margin-top: 20px;">
                <p style="font-size: 0.8rem; color: rgba(255,255,255,0.5);">
                    ✅ Pago 100% seguro<br>
                    ✅ Aceptamos todas las tarjetas<br>
                    ✅ Transferencia bancaria disponible<br>
                    ✅ Confirmación inmediata
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("❌ Error conectando con el sistema de pagos. Intenta nuevamente.")
        
        st.markdown("</div>", unsafe_allow_html=True)

def panel_admin():
    st.title("🔐 PANEL ADMINISTRATIVO")
    
    # Crear pestañas para mejor organización
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📋 INSCRIPCIONES", "⚙️ CONFIGURACIÓN"])
    
    with tab1:
        st.markdown("### 📈 ESTADÍSTICAS EN VIVO")
        
        pwd = st.text_input("🔑 CONTRASEÑA DE ADMINISTRADOR", type="password")
        
        if pwd == st.secrets["general"].get("admin_password", "admin"):
            df = get_data()
            
            if not df.empty:
                # Métricas rápidas
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Inscritos", len(df))
                col2.metric("Pagos Confirmados", len(df[df['Estado'] == 'CONFIRMADO']) if 'Estado' in df.columns else len(df))
                col3.metric("Ingresos Totales", f"${len(df) * PRECIO:,.0f}")
                col4.metric("Tasa de Conversión", f"{(len(df)/500)*100:.1f}%")
                
                # Gráfico de línea temporal (si hay fechas)
                if 'Fecha' in df.columns:
                    df['Fecha'] = pd.to_datetime(df['Fecha'])
                    df_daily = df.groupby(df['Fecha'].dt.date).size().reset_index(name='count')
                    
                    fig_line = px.line(
                        df_daily, 
                        x='Fecha', 
                        y='count',
                        title="📈 INSCRIPCIONES POR DÍA",
                        markers=True
                    )
                    
                    fig_line.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_family="Space Grotesk",
                        font_color="white",
                        title_font_family="Syne",
                        title_font_color="#00f3ff"
                    )
                    
                    st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No hay datos disponibles")
        else:
            st.warning("⚠️ Ingresa la contraseña de administrador")
    
    with tab2:
        st.markdown("### 📋 LISTA DE INSCRITOS")
        
        pwd = st.text_input("🔑 CONTRASEÑA PARA VER INSCRIPCIONES", type="password", key="pwd_tab2")
        
        if pwd == st.secrets["general"].get("admin_password", "admin"):
            df = get_data()
            
            if not df.empty:
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    categoria_filter = st.multiselect("Filtrar por Categoría", options=df['Categoria'].unique() if 'Categoria' in df.columns else [])
                with col2:
                    estado_filter = st.multiselect("Filtrar por Estado", options=df['Estado'].unique() if 'Estado' in df.columns else [])
                
                # Aplicar filtros
                df_filtered = df.copy()
                if categoria_filter and 'Categoria' in df.columns:
                    df_filtered = df_filtered[df_filtered['Categoria'].isin(categoria_filter)]
                if estado_filter and 'Estado' in df.columns:
                    df_filtered = df_filtered[df_filtered['Estado'].isin(estado_filter)]
                
                # Mostrar tabla
                st.dataframe(
                    df_filtered,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": "CÓDIGO",
                        "Fecha": "FECHA",
                        "Nombre": "NOMBRE",
                        "Email": "EMAIL",
                        "Dojo": "DOJO",
                        "Categoria": "CATEGORÍA",
                        "Estado": "ESTADO",
                        "Metodo": "MÉTODO DE PAGO"
                    }
                )
                
                # Botones de exportación
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 DESCARGAR CSV",
                        df_filtered.to_csv(index=False).encode('utf-8'),
                        "inscritos_wkb_2026.csv",
                        "text/csv",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        "📥 DESCARGAR EXCEL",
                        df_filtered.to_excel(index=False).encode('utf-8'),
                        "inscritos_wkb_2026.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with col3:
                    if st.button("🔄 ACTUALIZAR", use_container_width=True):
                        st.rerun()
            else:
                st.info("No hay inscripciones registradas")
    
    with tab3:
        st.markdown("### ⚙️ CONFIGURACIÓN DEL TORNEO")
        
        pwd = st.text_input("🔑 CONTRASEÑA DE ADMINISTRADOR", type="password", key="pwd_tab3")
        
        if pwd == st.secrets["general"].get("admin_password", "admin"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🎯 PARÁMETROS GENERALES")
                nuevo_precio = st.number_input("Precio de inscripción (CLP)", value=PRECIO, step=1000)
                nuevo_cupo = st.number_input("Cupo máximo", value=500, step=10)
                
                st.markdown("#### 📅 FECHA DEL TORNEO")
                nueva_fecha = st.date_input("Fecha", value=FECHA_TORNEO.date())
                nueva_hora = st.time_input("Hora", value=FECHA_TORNEO.time())
            
            with col2:
                st.markdown("#### 🏷️ CATEGORÍAS")
                st.markdown("**Categorías actuales:**")
                for i, cat in enumerate(CATEGORIAS, 1):
                    st.markdown(f"{i}. {cat}")
                
                if st.button("💾 GUARDAR CAMBIOS", use_container_width=True):
                    st.success("✅ Configuración actualizada (simulado)")
        else:
            st.warning("⚠️ Ingresa la contraseña de administrador")

# --- CONTROLADOR PRINCIPAL ---
def main():
    # Aplicar estilos futuristas
    apply_futuristic_styles()
    
    # Inicializar session state
    if 'step' not in st.session_state:
        st.session_state.step = 1
    
    # Menú Lateral Mejorado
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h3 style="font-size: 1.2rem;">⚡ WKB 2026 ⚡</h3>
        </div>
        """, unsafe_allow_html=True)
        
        menu = st.radio(
            "NAVEGACIÓN",
            ["🏠 INICIO & STATS", "📝 INSCRIBIRSE", "🔐 ADMIN"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Información adicional en sidebar
        st.markdown("""
        <div style="font-size: 0.8rem;">
            <p><b>📅 FECHA:</b> 24 Abril 2026</p>
            <p><b>📍 LUGAR:</b> Arena Santiago</p>
            <p><b>⏰ HORA:</b> 09:00 hrs</p>
            <p><b>🎟️ CUPOS:</b> 500</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Redes sociales
        st.markdown("""
        <div style="text-align: center;">
            <p style="font-size: 0.7rem;">SÍGUENOS</p>
            <p style="font-size: 1.2rem;">📱</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Manejo de retorno de MP
    if "status" in st.query_params and st.query_params["status"] == "approved":
        if 'temp_data' in st.session_state:
            if guardar_inscripcion(st.session_state.temp_data):
                st.balloons()
                st.success("""
                ### 🎉 ¡INSCRIPCIÓN EXITOSA!
                
                ✅ Tu pago ha sido confirmado
                ✅ Te esperamos en el tatami
                ✅ Recibirás un email con los detalles
                
                **¡NOS VEMOS EN EL CAMPEONATO!** ⚡
                """)
                st.session_state.temp_data = {}
                st.query_params.clear()
                time.sleep(3)
                st.rerun()
    
    # Renderizar según menú
    if menu == "🏠 INICIO & STATS":
        mostrar_header()
        df = get_data()
        dashboard_avanzado(df)
        
    elif menu == "📝 INSCRIBIRSE":
        mostrar_header()
        
        if st.session_state.step == 1:
            formulario_inscripcion()
        else:
            pasarela_pago()
            
    elif menu == "🔐 ADMIN":
        panel_admin()

if __name__ == "__main__":
    main()
