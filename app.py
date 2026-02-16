import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import random
import time
from datetime import datetime, timedelta
import re

# === CONFIGURACIÓN DE PÁGINA ===
st.set_page_config(
    page_title="WKB WORLD CUP 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === CONSTANTES ===
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
PRECIO = 15000
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
CODIGO_VIP = "WKB2026"

CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# === FUNCIONES DE UTILIDAD ===
def generar_id(nombre, email):
    """Genera ID único"""
    texto = f"{nombre}{email}{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

def validar_email(email):
    """Valida formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def formatear_peso(valor):
    """Formatea moneda"""
    return f"${valor:,.0f}".replace(",", ".")

def tiempo_restante():
    """Calcula tiempo para el torneo"""
    delta = FECHA_TORNEO - datetime.now()
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return dias, horas, minutos, segundos

# === FUNCIONES DE GOOGLE SHEETS ===
@st.cache_data(ttl=5)
def leer_inscripciones():
    """Lee todas las inscripciones"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Inscripciones", ttl=0)
        if df.empty:
            return pd.DataFrame(columns=[
                "ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", 
                "Dojo", "Pais", "Categoria", "Estado", "Metodo"
            ])
        return df
    except Exception as e:
        return pd.DataFrame(columns=[
            "ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", 
            "Dojo", "Pais", "Categoria", "Estado", "Metodo"
        ])

def guardar_inscripcion(datos):
    """Guarda una nueva inscripción"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_existente = leer_inscripciones()
        
        nueva_fila = pd.DataFrame([{
            "ID": datos['id'],
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nombre": datos['nombre'].upper(),
            "Email": datos['email'].lower(),
            "Telefono": datos['telefono'],
            "Edad": datos['edad'],
            "Dojo": datos['dojo'].upper(),
            "Pais": datos['pais'],
            "Categoria": datos['categoria'],
            "Estado": "CONFIRMADO",
            "Metodo": datos['metodo']
        }])
        
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {str(e)}")
        return False

@st.cache_data(ttl=5)
def leer_brackets():
    """Lee los brackets existentes"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Brackets", ttl=0)
        if df.empty:
            return pd.DataFrame(columns=[
                "Fecha", "Categoria", "Competidor1", "Dojo1", 
                "Competidor2", "Dojo2", "Tatami", "Estado", "Ganador"
            ])
        return df
    except:
        return pd.DataFrame(columns=[
            "Fecha", "Categoria", "Competidor1", "Dojo1", 
            "Competidor2", "Dojo2", "Tatami", "Estado", "Ganador"
        ])

def guardar_brackets(df):
    """Guarda los brackets"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except:
        return False

def generar_brackets_auto():
    """Genera brackets automáticamente"""
    df = leer_inscripciones()
    
    if df.empty:
        return False, "No hay inscripciones"
    
    # Filtrar confirmados
    df_conf = df[df['Estado'] == 'CONFIRMADO'].copy()
    
    if len(df_conf) < 2:
        return False, "Se necesitan al menos 2 competidores"
    
    # Verificar si ya hay brackets de hoy
    brackets_exist = leer_brackets()
    if not brackets_exist.empty:
        hoy = datetime.now().strftime("%Y-%m-%d")
        if 'Fecha' in brackets_exist.columns:
            brackets_hoy = brackets_exist[brackets_exist['Fecha'].str.contains(hoy)]
            if len(brackets_hoy) > 0:
                return False, "Brackets ya generados hoy"
    
    # Generar nuevos brackets
    todos_brackets = []
    
    for categoria in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == categoria]
        
        if len(df_cat) >= 2:
            participantes = df_cat.to_dict('records')
            random.shuffle(participantes)
            
            for i in range(0, len(participantes)-1, 2):
                if i+1 < len(participantes):
                    bracket = {
                        "Fecha": datetime.now().strftime("%Y-%m-%d"),
                        "Categoria": categoria,
                        "Competidor1": participantes[i]['Nombre'],
                        "Dojo1": participantes[i].get('Dojo', ''),
                        "Competidor2": participantes[i+1]['Nombre'],
                        "Dojo2": participantes[i+1].get('Dojo', ''),
                        "Tatami": f"Tatami {(i % 3) + 1}",
                        "Estado": "Pendiente",
                        "Ganador": ""
                    }
                    todos_brackets.append(bracket)
            
            # Número impar - bye
            if len(participantes) % 2 == 1:
                ultimo = participantes[-1]
                bracket = {
                    "Fecha": datetime.now().strftime("%Y-%m-%d"),
                    "Categoria": categoria,
                    "Competidor1": ultimo['Nombre'],
                    "Dojo1": ultimo.get('Dojo', ''),
                    "Competidor2": "DESCANSA (BYE)",
                    "Dojo2": "-",
                    "Tatami": "Descansa",
                    "Estado": "Bye",
                    "Ganador": ultimo['Nombre']
                }
                todos_brackets.append(bracket)
    
    if todos_brackets:
        df_nuevos = pd.DataFrame(todos_brackets)
        if guardar_brackets(df_nuevos):
            return True, f"✅ {len(todos_brackets)} brackets generados"
    
    return False, "No se generaron brackets"

# === CSS PROFESIONAL ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #2a0a0a 0%, #0a0c10 100%);
        font-family: 'Rajdhani', sans-serif;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Orbitron', sans-serif !important;
        color: white !important;
        text-shadow: 0 0 10px rgba(255, 43, 43, 0.5);
        letter-spacing: 1px;
    }
    
    /* LOGO */
    .logo-container {
        text-align: center;
        padding: 20px 0 10px 0;
        position: relative;
    }
    
    .logo-container img {
        width: min(350px, 80%);
        filter: drop-shadow(0 0 30px rgba(255, 43, 43, 0.4));
        transition: all 0.3s ease;
    }
    
    .logo-container img:hover {
        transform: scale(1.02);
        filter: drop-shadow(0 0 40px rgba(255, 43, 43, 0.6));
    }
    
    .logo-container h1 {
        font-size: clamp(1.8rem, 5vw, 3rem);
        margin: 10px 0 5px 0;
        background: linear-gradient(45deg, #fff, #ff2b2b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* COUNTDOWN */
    .countdown-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin: 30px 0;
    }
    
    .countdown-item {
        background: linear-gradient(145deg, #1e2028, #14161e);
        border: 1px solid #333;
        border-radius: 15px;
        padding: 15px 10px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }
    
    .countdown-number {
        font-family: 'Orbitron', monospace;
        font-size: clamp(1.5rem, 4vw, 2.5rem);
        font-weight: 900;
        color: #ff2b2b;
        line-height: 1;
    }
    
    .countdown-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* CARDS */
    .glass-card {
        background: rgba(20, 22, 30, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 4px solid #ff2b2b;
        border-radius: 16px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    /* FORM */
    .form-container {
        background: rgba(0, 0, 0, 0.3);
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #333;
    }
    
    .form-title {
        color: #ff2b2b;
        font-size: 1.3rem;
        margin-bottom: 20px;
        border-bottom: 2px solid #ff2b2b;
        padding-bottom: 10px;
    }
    
    /* BRACKETS */
    .brackets-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    .bracket-card {
        background: linear-gradient(145deg, #1e2028, #14161e);
        border: 1px solid #ff2b2b;
        border-radius: 12px;
        padding: 18px;
        transition: all 0.3s;
    }
    
    .bracket-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(255, 43, 43, 0.2);
    }
    
    .bracket-header {
        color: #ff2b2b;
        font-family: 'Orbitron', sans-serif;
        font-size: 1rem;
        border-bottom: 1px solid #333;
        padding-bottom: 8px;
        margin-bottom: 15px;
    }
    
    .bracket-fighter {
        display: flex;
        justify-content: space-between;
        padding: 10px;
        margin: 5px 0;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 6px;
        border-left: 3px solid #ff2b2b;
    }
    
    .bracket-vs {
        text-align: center;
        color: #ff2b2b;
        font-weight: bold;
        margin: 5px 0;
        font-size: 0.9rem;
    }
    
    .bracket-tatami {
        display: inline-block;
        background: #ff2b2b;
        color: white;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-top: 12px;
    }
    
    .bracket-bye {
        background: rgba(255, 215, 0, 0.1);
        border: 1px solid gold;
    }
    
    /* METRICS */
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', monospace !important;
        font-size: 2.2rem !important;
        color: #ff2b2b !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Rajdhani', sans-serif !important;
        font-size: 0.9rem !important;
        color: #aaa !important;
    }
    
    /* BUTTONS */
    .stButton > button {
        background: linear-gradient(90deg, #8b0000, #ff2b2b);
        color: white !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        letter-spacing: 1px !important;
        transition: all 0.3s !important;
    }
    
    .stButton > button:hover {
        box-shadow: 0 0 20px rgba(255, 43, 43, 0.6);
        transform: scale(1.02);
    }
    
    /* INPUTS */
    .stTextInput > div > div, .stNumberInput > div > div, .stSelectbox > div > div {
        background-color: #1e2028 !important;
        border: 1px solid #444 !important;
        border-radius: 6px !important;
        color: white !important;
    }
    
    .stTextInput > label, .stNumberInput > label, .stSelectbox > label {
        color: #aaa !important;
        font-size: 0.9rem !important;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(20, 22, 30, 0.8);
        padding: 10px;
        border-radius: 12px;
        gap: 30px;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Orbitron', sans-serif !important;
        color: white !important;
    }
    
    /* FOOTER */
    .footer {
        text-align: center;
        color: #666;
        padding: 30px 0 10px 0;
        border-top: 1px solid #333;
        margin-top: 50px;
    }
    
    /* RESPONSIVE */
    @media (max-width: 768px) {
        .countdown-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .brackets-grid {
            grid-template-columns: 1fr;
        }
        .glass-card {
            padding: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"""
    <div class="logo-container">
        <img src="{LOGO_URL}" alt="WKB Logo">
        <h1>WORLD CUP 2026</h1>
        <p style="color: #888; letter-spacing: 3px;">SANTIAGO · CHILE · ABRIL 2026</p>
    </div>
    """, unsafe_allow_html=True)

# === COUNTDOWN ===
dias, horas, minutos, segundos = tiempo_restante()
st.markdown(f"""
<div class="countdown-grid">
    <div class="countdown-item"><div class="countdown-number">{dias}</div><div class="countdown-label">DÍAS</div></div>
    <div class="countdown-item"><div class="countdown-number">{horas}</div><div class="countdown-label">HORAS</div></div>
    <div class="countdown-item"><div class="countdown-number">{minutos}</div><div class="countdown-label">MINUTOS</div></div>
    <div class="countdown-item"><div class="countdown-number">{segundos}</div><div class="countdown-label">SEGUNDOS</div></div>
</div>
""", unsafe_allow_html=True)

# === TABS PRINCIPALES ===
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "📝 INSCRIPCIÓN", "🏆 BRACKETS", "⚙️ ADMIN"])

# ========== TAB 1: DASHBOARD ==========
with tab1:
    st.markdown("## 📊 PANEL DE CONTROL")
    
    df = leer_inscripciones()
    
    if not df.empty:
        df_conf = df[df['Estado'] == 'CONFIRMADO']
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("TOTAL INSCRITOS", len(df_conf))
        with col2:
            st.metric("CATEGORÍAS", df_conf['Categoria'].nunique())
        with col3:
            st.metric("DOJOS", df_conf['Dojo'].nunique())
        with col4:
            st.metric("CUPOS DISPONIBLES", 500 - len(df_conf))
        
        # Gráfico de categorías
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📈 DISTRIBUCIÓN POR CATEGORÍA")
        
        counts = df_conf['Categoria'].value_counts().sort_values()
        fig = px.bar(
            x=counts.values,
            y=counts.index,
            orientation='h',
            color=counts.values,
            color_continuous_scale=['#440000', '#ff2b2b'],
            labels={'x': 'Inscritos', 'y': ''}
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Rajdhani'),
            height=450,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Últimas inscripciones
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ⏱️ ÚLTIMAS INSCRIPCIONES")
        
        ultimas = df_conf.sort_values('Fecha', ascending=False).head(5)
        for _, row in ultimas.iterrows():
            st.markdown(f"""
            <div style="background: rgba(0,0,0,0.2); padding: 10px; margin: 5px 0; border-radius: 8px;">
                <span style="color: #ff2b2b;">{row['Nombre']}</span> - {row['Categoria']} 
                <span style="float: right; color: #888;">{row['Dojo']}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📌 No hay inscripciones todavía")

# ========== TAB 2: INSCRIPCIÓN ==========
with tab2:
    st.markdown("## 📝 FORMULARIO DE INSCRIPCIÓN")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="form-title">DATOS DEL COMPETIDOR</div>', unsafe_allow_html=True)
    
    with st.form("form_inscripcion"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre Completo *", placeholder="Ej: Juan Pérez González")
            email = st.text_input("Email *", placeholder="ejemplo@correo.com")
            telefono = st.text_input("Teléfono / WhatsApp *", placeholder="+56 9 1234 5678")
        
        with col2:
            edad = st.number_input("Edad *", min_value=18, max_value=99, value=25)
            dojo = st.text_input("Dojo / Escuela *", placeholder="Nombre de tu dojo")
            pais = st.selectbox("País", ["Chile", "Argentina", "Perú", "Brasil", "Uruguay", "Paraguay", "Bolivia", "Ecuador", "Colombia", "Otro"])
        
        categoria = st.selectbox("Categoría *", CATEGORIAS)
        
        st.markdown("### 💰 PAGO")
        st.markdown(f"**Valor inscripción:** {formatear_peso(PRECIO)} CLP")
        
        metodo_pago = st.radio(
            "Método de pago",
            ["MercadoPago (Tarjeta/Transferencia)", "Código VIP"],
            horizontal=True
        )
        
        if metodo_pago == "Código VIP":
            codigo_vip = st.text_input("Ingresa tu código VIP", type="password")
        
        terminos = st.checkbox("Acepto los términos y condiciones del torneo")
        
        submitted = st.form_submit_button("COMPLETAR INSCRIPCIÓN", use_container_width=True)
        
        if submitted:
            # Validaciones
            errores = []
            if not nombre or len(nombre.split()) < 2:
                errores.append("❌ Ingresa nombre y apellido completo")
            if not email or not validar_email(email):
                errores.append("❌ Email inválido")
            if not telefono or len(telefono.replace(" ", "")) < 8:
                errores.append("❌ Teléfono inválido (mínimo 8 dígitos)")
            if not dojo:
                errores.append("❌ Ingresa el nombre de tu dojo")
            if not terminos:
                errores.append("❌ Debes aceptar los términos")
            
            if metodo_pago == "Código VIP" and codigo_vip != CODIGO_VIP:
                errores.append("❌ Código VIP inválido")
            
            if not errores:
                datos = {
                    'id': generar_id(nombre, email),
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono,
                    'edad': edad,
                    'dojo': dojo,
                    'pais': pais,
                    'categoria': categoria,
                    'metodo': 'VIP' if metodo_pago == "Código VIP" else 'Pendiente'
                }
                
                if guardar_inscripcion(datos):
                    st.balloons()
                    st.success("✅ ¡Inscripción exitosa!")
                    st.info(f"Tu ID de registro: {datos['id']}")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar. Intenta nuevamente.")
            else:
                for error in errores:
                    st.error(error)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 3: BRACKETS ==========
with tab3:
    st.markdown("## 🏆 BRACKETS DEL TORNEO")
    
    # Generar brackets automáticamente
    with st.spinner("Actualizando brackets..."):
        resultado, mensaje = generar_brackets_auto()
        if resultado:
            st.success(mensaje)
    
    # Mostrar brackets
    df_brackets = leer_brackets()
    
    if not df_brackets.empty:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            categorias_brackets = ["TODAS"] + list(df_brackets['Categoria'].unique())
            filtro_cat = st.selectbox("Filtrar por categoría", categorias_brackets)
        with col2:
            tatamis = ["TODOS"] + list(df_brackets['Tatami'].unique())
            filtro_tatami = st.selectbox("Filtrar por tatami", tatamis)
        
        # Aplicar filtros
        df_filtrado = df_brackets.copy()
        if filtro_cat != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['Categoria'] == filtro_cat]
        if filtro_tatami != "TODOS":
            df_filtrado = df_filtrado[df_filtrado['Tatami'] == filtro_tatami]
        
        # Mostrar brackets
        if not df_filtrado.empty:
            st.markdown(f'<div class="brackets-grid">', unsafe_allow_html=True)
            
            for _, row in df_filtrado.iterrows():
                bye_class = "bracket-bye" if "DESCANSA" in row['Competidor2'] else ""
                
                ganador1 = "🏆 " if row['Ganador'] == row['Competidor1'] else ""
                ganador2 = "🏆 " if row['Ganador'] == row['Competidor2'] else ""
                
                st.markdown(f"""
                <div class="bracket-card {bye_class}">
                    <div class="bracket-header">{row['Categoria']}</div>
                    <div class="bracket-fighter">{ganador1}{row['Competidor1']} <span style="color:#888;">{row['Dojo1']}</span></div>
                    <div class="bracket-vs">VS</div>
                    <div class="bracket-fighter">{ganador2}{row['Competidor2']} <span style="color:#888;">{row['Dojo2']}</span></div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:15px;">
                        <span class="bracket-tatami">{row['Tatami']}</span>
                        <span style="color:#888;">{row['Estado']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Estadísticas de brackets
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Combates", len(df_filtrado))
            with col2:
                st.metric("Categorías", df_filtrado['Categoria'].nunique())
            with col3:
                byes = len(df_filtrado[df_filtrado['Competidor2'] == "DESCANSA (BYE)"])
                st.metric("Byes", byes)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No hay brackets para los filtros seleccionados")
    else:
        st.info("📌 No hay brackets generados todavía")
        
        if st.button("🔄 GENERAR BRACKETS AHORA", use_container_width=True):
            with st.spinner("Generando brackets..."):
                resultado, mensaje = generar_brackets_auto()
                if resultado:
                    st.success(mensaje)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning(mensaje)

# ========== TAB 4: ADMIN ==========
with tab4:
    st.markdown("## ⚙️ PANEL DE ADMINISTRACIÓN")
    
    password = st.text_input("Contraseña de administrador", type="password")
    
    # Contraseña desde secrets o por defecto
    admin_pass = st.secrets["general"].get("admin_password", "admin123")
    
    if password == admin_pass:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        admin_tabs = st.tabs(["📋 INSCRIPCIONES", "🏆 BRACKETS", "📊 ESTADÍSTICAS"])
        
        with admin_tabs[0]:
            df_admin = leer_inscripciones()
            if not df_admin.empty:
                st.dataframe(
                    df_admin,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width="small"),
                        "Fecha": st.column_config.DatetimeColumn("Fecha", width="medium"),
                        "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                        "Email": st.column_config.TextColumn("Email", width="medium"),
                        "Telefono": st.column_config.TextColumn("Teléfono", width="small"),
                        "Categoria": st.column_config.TextColumn("Categoría", width="medium")
                    }
                )
                
                # Exportar
                col1, col2 = st.columns(2)
                with col1:
                    csv = df_admin.to_csv(index=False)
                    st.download_button(
                        "📥 DESCARGAR CSV",
                        csv,
                        f"inscripciones_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
            else:
                st.info("No hay inscripciones")
        
        with admin_tabs[1]:
            df_brackets_admin = leer_brackets()
            if not df_brackets_admin.empty:
                st.dataframe(df_brackets_admin, use_container_width=True, hide_index=True)
                
                # Actualizar ganadores
                st.markdown("### Actualizar resultados")
                with st.form("form_resultados"):
                    bracket_idx = st.selectbox(
                        "Seleccionar combate",
                        range(len(df_brackets_admin)),
                        format_func=lambda x: f"{df_brackets_admin.iloc[x]['Competidor1']} vs {df_brackets_admin.iloc[x]['Competidor2']}"
                    )
                    
                    ganador = st.radio(
                        "Ganador",
                        [df_brackets_admin.iloc[bracket_idx]['Competidor1'], df_brackets_admin.iloc[bracket_idx]['Competidor2']]
                    )
                    
                    if st.form_submit_button("ACTUALIZAR"):
                        df_brackets_admin.at[bracket_idx, 'Ganador'] = ganador
                        df_brackets_admin.at[bracket_idx, 'Estado'] = "Finalizado"
                        if guardar_brackets(df_brackets_admin):
                            st.success("✅ Resultado actualizado")
                            st.rerun()
                
                # Botón para regenerar
                if st.button("🔄 REGENERAR TODOS LOS BRACKETS", use_container_width=True):
                    if st.checkbox("Confirmar regeneración"):
                        df_vacio = pd.DataFrame(columns=df_brackets_admin.columns)
                        guardar_brackets(df_vacio)
                        resultado, mensaje = generar_brackets_auto()
                        if resultado:
                            st.success(mensaje)
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("No hay brackets")
        
        with admin_tabs[2]:
            df_stats = leer_inscripciones()
            if not df_stats.empty:
                df_conf = df_stats[df_stats['Estado'] == 'CONFIRMADO']
                
                # Estadísticas generales
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total ingresos", formatear_peso(len(df_conf) * PRECIO))
                with col2:
                    st.metric("Pago pendiente", len(df_stats[df_stats['Metodo'] == 'Pendiente']))
                with col3:
                    st.metric("Pago VIP", len(df_stats[df_stats['Metodo'] == 'VIP']))
                
                # Gráfico de países
                if 'Pais' in df_conf.columns:
                    paises = df_conf['Pais'].value_counts()
                    fig_paises = px.pie(
                        values=paises.values,
                        names=paises.index,
                        title="Distribución por País",
                        color_discrete_sequence=px.colors.sequential.Reds
                    )
                    fig_paises.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white')
                    )
                    st.plotly_chart(fig_paises, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    elif password:
        st.error("❌ Contraseña incorrecta")

# === FOOTER ===
st.markdown("""
<div class="footer">
    <p>© 2024 World Kyokushin Budokai Chile · Todos los derechos reservados</p>
    <p style="font-size: 0.8rem; color: #444;">Versión 4.0 · Sistema Integrado de Inscripciones y Brackets</p>
</div>
""", unsafe_allow_html=True)
