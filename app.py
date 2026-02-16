import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import random
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB WORLD CUP 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES ---
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
PRECIO = 15000
CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# --- FUNCIONES DE GOOGLE SHEETS ---
@st.cache_data(ttl=10)
def get_data():
    """Obtiene datos de inscripciones"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Inscripciones", ttl=0)
        if df.empty:
            return pd.DataFrame(columns=["ID", "Nombre", "Categoria", "Dojo", "Estado"])
        return df
    except:
        return pd.DataFrame(columns=["ID", "Nombre", "Categoria", "Dojo", "Estado"])

def save_data(df):
    """Guarda datos en sheets"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Inscripciones", data=df)
        return True
    except:
        return False

def get_brackets():
    """Obtiene brackets existentes"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(worksheet="Brackets", ttl=0)
    except:
        return pd.DataFrame()

def save_brackets(df):
    """Guarda brackets en sheets"""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except:
        return False

# --- FUNCIÓN AUTOMÁTICA DE BRACKETS ---
def generar_brackets_auto():
    """Genera brackets automáticamente - SIN NECESIDAD DE CONFIGURACIÓN"""
    
    # Obtener datos
    df = get_data()
    
    # Verificar si hay suficientes datos
    if df.empty:
        return False, "No hay inscripciones"
    
    # Filtrar solo confirmados
    if 'Estado' in df.columns:
        df_conf = df[df['Estado'] == 'CONFIRMADO'].copy()
    else:
        df_conf = df.copy()
    
    if len(df_conf) < 2:
        return False, "Se necesitan al menos 2 competidores"
    
    # Verificar si ya hay brackets de hoy
    try:
        brackets_existentes = get_brackets()
        if not brackets_existentes.empty:
            hoy = datetime.now().strftime("%Y-%m-%d")
            if 'Fecha' in brackets_existentes.columns:
                brackets_hoy = brackets_existentes[brackets_existentes['Fecha'].str.contains(hoy)]
                if not brackets_hoy.empty:
                    return False, "Brackets ya generados hoy"
    except:
        pass
    
    # Generar brackets
    todos_brackets = []
    
    for categoria in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == categoria]
        
        if len(df_cat) >= 2:
            # Mezclar participantes
            participantes = df_cat.to_dict('records')
            random.shuffle(participantes)
            
            # Crear parejas
            for i in range(0, len(participantes)-1, 2):
                if i+1 < len(participantes):
                    bracket = {
                        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Categoria": categoria,
                        "Competidor1": participantes[i]['Nombre'],
                        "Dojo1": participantes[i].get('Dojo', ''),
                        "Competidor2": participantes[i+1]['Nombre'],
                        "Dojo2": participantes[i+1].get('Dojo', ''),
                        "Tatami": f"Tatami {(i % 3) + 1}",
                        "Estado": "Pendiente",
                        "Resultado": ""
                    }
                    todos_brackets.append(bracket)
            
            # Si hay número impar, el último descansa
            if len(participantes) % 2 == 1:
                ultimo = participantes[-1]
                bracket = {
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Categoria": categoria,
                    "Competidor1": ultimo['Nombre'],
                    "Dojo1": ultimo.get('Dojo', ''),
                    "Competidor2": "DESCANSA",
                    "Dojo2": "BYE",
                    "Tatami": "Descansa",
                    "Estado": "Bye",
                    "Resultado": "Avanza directo"
                }
                todos_brackets.append(bracket)
    
    # Guardar brackets
    if todos_brackets:
        df_brackets = pd.DataFrame(todos_brackets)
        if save_brackets(df_brackets):
            return True, f"✅ {len(todos_brackets)} brackets generados"
        else:
            return False, "Error al guardar"
    
    return False, "No se generaron brackets"

# --- CSS MEJORADO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    /* Fondo */
    .stApp {
        background: linear-gradient(135deg, #0a0c10 0%, #1a1c24 100%);
    }
    
    /* Títulos */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: white;
        text-shadow: 0 0 10px #ff2b2b;
    }
    
    /* Logo */
    .logo-container {
        text-align: center;
        padding: 20px;
    }
    .logo-container img {
        width: min(300px, 80%);
        filter: drop-shadow(0 0 20px #ff2b2b);
    }
    
    /* Tarjetas */
    .glass-card {
        background: rgba(20, 22, 30, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid #333;
        border-left: 4px solid #ff2b2b;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
    }
    
    /* Brackets */
    .bracket-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    .bracket-card {
        background: linear-gradient(145deg, #1e2028, #14161e);
        border: 1px solid #ff2b2b;
        border-radius: 10px;
        padding: 15px;
    }
    
    .bracket-title {
        color: #ff2b2b;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.1rem;
        margin-bottom: 10px;
        border-bottom: 1px solid #333;
        padding-bottom: 5px;
    }
    
    .competitor {
        display: flex;
        justify-content: space-between;
        padding: 8px;
        margin: 5px 0;
        background: rgba(0,0,0,0.3);
        border-radius: 5px;
    }
    
    .vs {
        text-align: center;
        color: #ff2b2b;
        font-weight: bold;
        margin: 5px 0;
    }
    
    .tatami {
        display: inline-block;
        background: #ff2b2b;
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-top: 10px;
    }
    
    .bye {
        background: rgba(255,215,0,0.1);
        border: 1px solid gold;
    }
    
    /* Botones */
    .stButton>button {
        background: linear-gradient(90deg, #8b0000, #ff2b2b);
        color: white;
        font-family: 'Orbitron', sans-serif;
        border: none;
        width: 100%;
    }
    
    /* Métricas */
    [data-testid="stMetricValue"] {
        color: #ff2b2b !important;
        font-family: 'Orbitron', monospace !important;
    }
    
    @media (max-width: 768px) {
        .bracket-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.markdown(f"""
    <div class="logo-container">
        <img src="{LOGO_URL}">
        <h1 style="font-size: clamp(1.8rem, 5vw, 3rem;">WKB WORLD CUP 2026</h1>
        <p style="color: #666;">SANTIAGO · CHILE</p>
    </div>
    """, unsafe_allow_html=True)

# --- TABS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "🏆 BRACKETS", "⚙️ ADMIN"])

# ========== TAB 1: DASHBOARD ==========
with tab1:
    st.markdown("## 📈 ESTADÍSTICAS EN VIVO")
    
    df = get_data()
    
    if not df.empty and 'Estado' in df.columns:
        df_conf = df[df['Estado'] == 'CONFIRMADO']
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Inscritos", len(df_conf))
        with col2:
            st.metric("Categorías", df_conf['Categoria'].nunique())
        with col3:
            st.metric("Dojos", df_conf['Dojo'].nunique())
        with col4:
            st.metric("Cupos", 500 - len(df_conf))
        
        # Gráfico
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Distribución por Categoría")
        
        counts = df_conf['Categoria'].value_counts()
        fig = px.bar(
            x=counts.values,
            y=counts.index,
            orientation='h',
            color=counts.values,
            color_continuous_scale=['#440000', '#ff2b2b']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No hay inscripciones aún")

# ========== TAB 2: BRACKETS (AUTOMÁTICO) ==========
with tab2:
    st.markdown("## 🏆 BRACKETS DEL TORNEO")
    
    # AUTO-GENERACIÓN CADA VEZ QUE SE CARGA LA PÁGINA
    with st.spinner("Actualizando brackets..."):
        resultado, mensaje = generar_brackets_auto()
        if resultado:
            st.success(mensaje)
        elif mensaje != "Brackets ya generados hoy":
            st.info(mensaje)
    
    # Mostrar brackets
    df_brackets = get_brackets()
    
    if not df_brackets.empty:
        # Selector de categoría
        categorias = df_brackets['Categoria'].unique()
        cat_seleccionada = st.selectbox("Filtrar por categoría", ["TODAS"] + list(categorias))
        
        if cat_seleccionada != "TODAS":
            df_brackets = df_brackets[df_brackets['Categoria'] == cat_seleccionada]
        
        # Mostrar en grid
        st.markdown('<div class="bracket-grid">', unsafe_allow_html=True)
        
        for idx, row in df_brackets.iterrows():
            bye_class = "bye" if row['Competidor2'] == "DESCANSA" else ""
            
            st.markdown(f"""
            <div class="bracket-card {bye_class}">
                <div class="bracket-title">{row['Categoria']}</div>
                <div class="competitor">
                    <span>⚔️ {row['Competidor1']}</span>
                    <small>{row['Dojo1']}</small>
                </div>
                <div class="vs">VS</div>
                <div class="competitor">
                    <span>⚔️ {row['Competidor2']}</span>
                    <small>{row['Dojo2']}</small>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                    <span class="tatami">{row['Tatami']}</span>
                    <span style="color: #888;">{row['Estado']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botón para regenerar (opcional)
        if st.button("🔄 REGENERAR BRACKETS", use_container_width=True):
            with st.spinner("Generando nuevos brackets..."):
                # Limpiar brackets anteriores
                save_brackets(pd.DataFrame())
                # Generar nuevos
                resultado, mensaje = generar_brackets_auto()
                if resultado:
                    st.success(mensaje)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(mensaje)
    else:
        st.info("No hay brackets generados aún")

# ========== TAB 3: ADMIN SIMPLE ==========
with tab3:
    st.markdown("## ⚙️ PANEL ADMIN")
    
    password = st.text_input("Contraseña", type="password")
    
    # Contraseña por defecto (cámbiala en secrets)
    admin_pass = st.secrets["general"].get("admin_password", "admin123")
    
    if password == admin_pass:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        # Ver datos
        df = get_data()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Exportar
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 DESCARGAR INSCRIPCIONES",
                csv,
                "inscripciones.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("No hay datos")
        
        # Ver brackets
        df_b = get_brackets()
        if not df_b.empty:
            with st.expander("Ver brackets"):
                st.dataframe(df_b, use_container_width=True, hide_index=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    elif password:
        st.error("Contraseña incorrecta")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>© 2024 WKB Chile - Sistema Automático de Brackets</p>
    <p style="font-size: 0.8rem;">Los brackets se generan automáticamente cada vez que hay nuevos inscritos</p>
</div>
""", unsafe_allow_html=True)
