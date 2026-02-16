import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import hashlib
import random
import math
import time
from datetime import datetime
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

PAISES = ["Chile", "Argentina", "Perú", "Brasil", "Uruguay", "Paraguay", 
          "Bolivia", "Ecuador", "Colombia", "Venezuela", "Otro"]

# === FUNCIONES DE UTILIDAD ===
def generar_id(nombre, email):
    texto = f"{nombre}{email}{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def formatear_peso(valor):
    return f"${valor:,.0f}".replace(",", ".")

def tiempo_restante():
    delta = FECHA_TORNEO - datetime.now()
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return dias, horas, minutos, segundos

def verificar_admin(password):
    if password:
        hash_input = hashlib.sha256(password.encode()).hexdigest()
        return hash_input == st.secrets["general"]["admin_token_hash"]
    return False

# === FUNCIONES DE GOOGLE SHEETS ===
@st.cache_data(ttl=5)
def leer_inscripciones():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Inscripciones", ttl=0)
        if df.empty:
            return pd.DataFrame(columns=[
                "ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", 
                "Dojo", "Pais", "Categoria", "Estado", "Metodo"
            ])
        # Asegurar que los nombres sean string
        if 'Nombre' in df.columns:
            df['Nombre'] = df['Nombre'].astype(str)
        if 'Dojo' in df.columns:
            df['Dojo'] = df['Dojo'].astype(str)
        return df
    except Exception as e:
        return pd.DataFrame(columns=[
            "ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", 
            "Dojo", "Pais", "Categoria", "Estado", "Metodo"
        ])

def guardar_inscripcion(datos):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_existente = leer_inscripciones()
        
        nueva_fila = pd.DataFrame([{
            "ID": datos['id'],
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nombre": str(datos['nombre']).upper(),
            "Email": str(datos['email']).lower(),
            "Telefono": str(datos['telefono']),
            "Edad": datos['edad'],
            "Dojo": str(datos['dojo']).upper(),
            "Pais": str(datos['pais']),
            "Categoria": str(datos['categoria']),
            "Estado": "CONFIRMADO",
            "Metodo": str(datos['metodo'])
        }])
        
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error al guardar: {str(e)}")
        return False

@st.cache_data(ttl=5)
def leer_brackets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Brackets", ttl=0)
        if df.empty:
            return pd.DataFrame(columns=[
                "Categoria", "Ronda", "Partido_ID", "Competidor1", "Dojo1",
                "Competidor2", "Dojo2", "Ganador"
            ])
        # Asegurar tipos de datos
        for col in ['Competidor1', 'Competidor2', 'Ganador', 'Dojo1', 'Dojo2']:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)
        return df
    except:
        return pd.DataFrame(columns=[
            "Categoria", "Ronda", "Partido_ID", "Competidor1", "Dojo1",
            "Competidor2", "Dojo2", "Ganador"
        ])

def guardar_brackets(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except Exception as e:
        st.error(f"Error guardando brackets: {str(e)}")
        return False

def generar_brackets_dinamicos():
    """Genera brackets con rondas exactas según cantidad de luchadores"""
    df = leer_inscripciones()
    
    if df.empty:
        return False, "No hay inscripciones"
    
    # Filtrar confirmados
    df_conf = df[df['Estado'] == 'CONFIRMADO'].copy()
    
    if len(df_conf) < 2:
        return False, "Se necesitan al menos 2 competidores"
    
    todos_partidos = []
    
    for categoria in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == categoria]
        num_competidores = len(df_cat)
        
        if num_competidores >= 2:
            participantes = df_cat.to_dict('records')
            random.shuffle(participantes)
            
            # Calcular número exacto de rondas necesarias
            num_rondas = math.ceil(math.log2(num_competidores))
            capacidad_total = 2 ** num_rondas
            
            # Crear lista de competidores con byes
            competidores_lista = []
            for p in participantes:
                competidores_lista.append({
                    'nombre': str(p.get('Nombre', '')),
                    'dojo': str(p.get('Dojo', ''))
                })
            
            # Añadir byes necesarios
            byes_necesarios = capacidad_total - num_competidores
            for _ in range(byes_necesarios):
                competidores_lista.append(None)
            
            # Mezclar para distribución aleatoria
            random.shuffle(competidores_lista)
            
            # Generar primera ronda
            partido_id = 1
            for i in range(0, len(competidores_lista), 2):
                if i + 1 < len(competidores_lista):
                    c1 = competidores_lista[i]
                    c2 = competidores_lista[i + 1]
                    
                    if c1 is None and c2 is not None:
                        # BYE para c2
                        partido = {
                            "Categoria": categoria,
                            "Ronda": 1,
                            "Partido_ID": partido_id,
                            "Competidor1": "BYE",
                            "Dojo1": "-",
                            "Competidor2": c2['nombre'],
                            "Dojo2": c2['dojo'],
                            "Ganador": c2['nombre']
                        }
                    elif c2 is None and c1 is not None:
                        # BYE para c1
                        partido = {
                            "Categoria": categoria,
                            "Ronda": 1,
                            "Partido_ID": partido_id,
                            "Competidor1": c1['nombre'],
                            "Dojo1": c1['dojo'],
                            "Competidor2": "BYE",
                            "Dojo2": "-",
                            "Ganador": c1['nombre']
                        }
                    elif c1 is not None and c2 is not None:
                        # Partido normal
                        partido = {
                            "Categoria": categoria,
                            "Ronda": 1,
                            "Partido_ID": partido_id,
                            "Competidor1": c1['nombre'],
                            "Dojo1": c1['dojo'],
                            "Competidor2": c2['nombre'],
                            "Dojo2": c2['dojo'],
                            "Ganador": ""
                        }
                    else:
                        continue
                    
                    todos_partidos.append(partido)
                    partido_id += 1
            
            # Generar rondas superiores
            partidos_por_ronda = capacidad_total // 2
            for ronda in range(2, num_rondas + 1):
                partidos_por_ronda = partidos_por_ronda // 2
                for j in range(partidos_por_ronda):
                    partido = {
                        "Categoria": categoria,
                        "Ronda": ronda,
                        "Partido_ID": partido_id,
                        "Competidor1": "",
                        "Dojo1": "",
                        "Competidor2": "",
                        "Dojo2": "",
                        "Ganador": ""
                    }
                    todos_partidos.append(partido)
                    partido_id += 1
    
    if todos_partidos:
        df_brackets = pd.DataFrame(todos_partidos)
        if guardar_brackets(df_brackets):
            return True, f"✅ {len(todos_partidos)} brackets generados"
    
    return False, "No se generaron brackets"

# === CSS PROFESIONAL ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #2a0a0a 0%, #0a0c10 100%);
        font-family: 'Rajdhani', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: white !important;
        text-shadow: 0 0 10px rgba(255, 43, 43, 0.5);
    }
    
    /* LOGO */
    .logo-container {
        text-align: center;
        padding: 20px 0;
    }
    .logo-container img {
        width: min(350px, 80%);
        filter: drop-shadow(0 0 30px rgba(255, 43, 43, 0.4));
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
        padding: 15px;
        text-align: center;
    }
    .countdown-number {
        font-family: 'Orbitron', monospace;
        font-size: clamp(1.5rem, 4vw, 2.5rem);
        color: #ff2b2b;
        font-weight: 900;
    }
    
    /* BRACKETS HORIZONTALES */
    .bracket-container {
        overflow-x: auto;
        padding: 20px 0;
        margin: 20px 0;
        background: rgba(0,0,0,0.2);
        border-radius: 12px;
    }
    
    .bracket-row {
        display: flex;
        flex-direction: row;
        gap: 30px;
        min-width: min-content;
        padding: 20px;
    }
    
    .round-column {
        display: flex;
        flex-direction: column;
        gap: 30px;
        min-width: 280px;
    }
    
    .round-title {
        font-family: 'Orbitron', sans-serif;
        color: #ff2b2b;
        text-align: center;
        padding: 10px;
        border-bottom: 2px solid #ff2b2b;
        margin-bottom: 20px;
    }
    
    .match-card {
        background: linear-gradient(145deg, #1e2028, #14161e);
        border: 1px solid #ff2b2b;
        border-radius: 8px;
        padding: 15px;
        position: relative;
        min-width: 250px;
    }
    
    .match-card::after {
        content: '';
        position: absolute;
        right: -30px;
        top: 50%;
        width: 30px;
        height: 2px;
        background: #ff2b2b;
        display: none;
    }
    
    .round-column:not(:last-child) .match-card::after {
        display: block;
    }
    
    .match-card.bye-match {
        border-color: gold;
        background: rgba(255,215,0,0.1);
    }
    
    .competitor-slot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        margin: 5px 0;
        background: rgba(0,0,0,0.3);
        border-radius: 6px;
        border-left: 3px solid #ff2b2b;
    }
    
    .competitor-slot.winner {
        border-left-color: gold;
        background: rgba(255,215,0,0.1);
    }
    
    .competitor-slot.bye {
        border-left-color: gold;
        background: rgba(255,215,0,0.05);
    }
    
    .competitor-name {
        font-weight: 600;
        color: white;
    }
    
    .competitor-dojo {
        font-size: 0.75rem;
        color: #888;
    }
    
    .vs-divider {
        text-align: center;
        color: #ff2b2b;
        font-weight: bold;
        margin: 5px 0;
        font-size: 0.8rem;
    }
    
    .match-info {
        display: flex;
        justify-content: space-between;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #333;
        font-size: 0.75rem;
    }
    
    .match-id {
        color: #666;
    }
    
    .winner-badge {
        background: gold;
        color: black;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
    }
    
    .bye-badge {
        background: gold;
        color: black;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
    }
    
    /* GLASS CARD */
    .glass-card {
        background: rgba(20, 22, 30, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-left: 4px solid #ff2b2b;
        border-radius: 16px;
        padding: 25px;
        margin: 20px 0;
    }
    
    /* BOTONES */
    .stButton > button {
        background: linear-gradient(90deg, #8b0000, #ff2b2b);
        color: white !important;
        font-family: 'Orbitron', sans-serif !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        width: 100%;
    }
    
    /* METRICS */
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', monospace !important;
        color: #ff2b2b !important;
        font-size: 2rem !important;
    }
    
    @media (max-width: 768px) {
        .round-column {
            min-width: 220px;
        }
        .match-card {
            min-width: 200px;
            padding: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# === HEADER Y COUNTDOWN ===
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.markdown(f"""
    <div class="logo-container">
        <img src="{LOGO_URL}">
        <h1>WORLD CUP 2026</h1>
        <p style="color:#888;">SANTIAGO · CHILE · ABRIL 2026</p>
    </div>
    """, unsafe_allow_html=True)

dias, horas, minutos, segundos = tiempo_restante()
st.markdown(f"""
<div class="countdown-grid">
    <div class="countdown-item"><div class="countdown-number">{dias}</div><div>DÍAS</div></div>
    <div class="countdown-item"><div class="countdown-number">{horas}</div><div>HORAS</div></div>
    <div class="countdown-item"><div class="countdown-number">{minutos}</div><div>MINUTOS</div></div>
    <div class="countdown-item"><div class="countdown-number">{segundos}</div><div>SEGUNDOS</div></div>
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
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("TOTAL INSCRITOS", len(df_conf))
        with col2:
            st.metric("CATEGORÍAS", df_conf['Categoria'].nunique())
        with col3:
            st.metric("DOJOS", df_conf['Dojo'].nunique())
        with col4:
            st.metric("CUPOS", 500 - len(df_conf))
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        counts = df_conf['Categoria'].value_counts().sort_values()
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
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("📌 No hay inscripciones")

# ========== TAB 2: INSCRIPCIÓN ==========
with tab2:
    st.markdown("## 📝 FORMULARIO DE INSCRIPCIÓN")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    with st.form("form_inscripcion"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre Completo *")
            email = st.text_input("Email *")
            telefono = st.text_input("Teléfono *")
        with col2:
            edad = st.number_input("Edad *", 18, 99, 25)
            dojo = st.text_input("Dojo *")
            pais = st.selectbox("País", PAISES)
        
        categoria = st.selectbox("Categoría *", CATEGORIAS)
        st.markdown(f"**Valor:** {formatear_peso(PRECIO)} CLP")
        
        metodo_pago = st.radio("Método de pago", ["Código VIP", "Pagar después"])
        if metodo_pago == "Código VIP":
            codigo_vip = st.text_input("Código VIP", type="password")
        
        terminos = st.checkbox("Acepto términos y condiciones")
        
        if st.form_submit_button("INSCRIBIRSE", use_container_width=True):
            errores = []
            if not nombre or len(nombre.split()) < 2:
                errores.append("Nombre completo requerido")
            if not email or not validar_email(email):
                errores.append("Email inválido")
            if not telefono or len(telefono) < 8:
                errores.append("Teléfono inválido")
            if not dojo:
                errores.append("Dojo requerido")
            if not terminos:
                errores.append("Debes aceptar términos")
            if metodo_pago == "Código VIP" and codigo_vip != CODIGO_VIP:
                errores.append("Código VIP inválido")
            
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
                    st.success("✅ Inscripción exitosa!")
                    st.rerun()
            else:
                for e in errores:
                    st.error(e)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 3: BRACKETS ==========
with tab3:
    st.markdown("## 🏆 BRACKETS DEL TORNEO")
    
    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("🔄 GENERAR BRACKETS", use_container_width=True):
            with st.spinner("Generando brackets..."):
                resultado, mensaje = generar_brackets_dinamicos()
                if resultado:
                    st.success(mensaje)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning(mensaje)
    
    df_brackets = leer_brackets()
    
    if not df_brackets.empty:
        # Mostrar resumen
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📊 RESUMEN")
        
        categorias_unicas = df_brackets['Categoria'].unique()
        for cat in categorias_unicas:
            df_cat = df_brackets[df_brackets['Categoria'] == cat]
            rondas = df_cat['Ronda'].max()
            partidos = len(df_cat)
            st.markdown(f"**{cat}**: {rondas} rondas · {partidos} partidos")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Selector de categoría
        categorias = df_brackets['Categoria'].unique()
        cat_sel = st.selectbox("Seleccionar categoría", categorias)
        
        # Filtrar por categoría
        df_cat = df_brackets[df_brackets['Categoria'] == cat_sel]
        
        if not df_cat.empty:
            max_ronda = df_cat['Ronda'].max()
            
            # Contenedor con scroll horizontal
            st.markdown('<div class="bracket-container">', unsafe_allow_html=True)
            st.markdown('<div class="bracket-row">', unsafe_allow_html=True)
            
            # Crear columna para cada ronda
            for ronda in range(1, max_ronda + 1):
                df_ronda = df_cat[df_cat['Ronda'] == ronda].reset_index(drop=True)
                
                # Determinar nombre de la ronda
                if ronda == max_ronda:
                    nombre_ronda = "🏆 FINAL"
                elif ronda == max_ronda - 1:
                    nombre_ronda = "🥈 SEMIFINAL"
                elif ronda == max_ronda - 2:
                    nombre_ronda = "🥉 CUARTOS"
                else:
                    nombre_ronda = f"RONDA {ronda}"
                
                st.markdown(f'<div class="round-column">', unsafe_allow_html=True)
                st.markdown(f'<div class="round-title">{nombre_ronda}</div>', unsafe_allow_html=True)
                
                for _, partido in df_ronda.iterrows():
                    bye_class = "bye-match" if partido['Competidor1'] == "BYE" or partido['Competidor2'] == "BYE" else ""
                    
                    winner1 = "winner" if partido['Ganador'] == partido['Competidor1'] else ""
                    winner2 = "winner" if partido['Ganador'] == partido['Competidor2'] else ""
                    
                    st.markdown(f"""
                    <div class="match-card {bye_class}">
                        <div class="competitor-slot {winner1}">
                            <span class="competitor-name">{partido['Competidor1'] or '---'}</span>
                            <span class="competitor-dojo">{partido['Dojo1']}</span>
                        </div>
                        <div class="vs-divider">⚔️ VS ⚔️</div>
                        <div class="competitor-slot {winner2}">
                            <span class="competitor-name">{partido['Competidor2'] or '---'}</span>
                            <span class="competitor-dojo">{partido['Dojo2']}</span>
                        </div>
                        <div class="match-info">
                            <span class="match-id">#{partido['Partido_ID']}</span>
                            {f'<span class="winner-badge">🏆 GANADOR</span>' if partido['Ganador'] else ''}
                            {f'<span class="bye-badge">⭐ BYE</span>' if partido['Competidor1'] == "BYE" or partido['Competidor2'] == "BYE" else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Leyenda
            st.markdown("""
            <div style="display:flex; gap:20px; justify-content:center; margin:20px 0; padding:15px; background:rgba(0,0,0,0.2); border-radius:8px;">
                <span><span style="color:#ff2b2b;">⬤</span> Partido pendiente</span>
                <span><span style="color:gold;">⬤</span> Ganador definido</span>
                <span><span style="color:gold;">⭐</span> BYE (descansa)</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📌 No hay brackets generados. Haz clic en 'GENERAR BRACKETS' para crear las llaves del torneo.")

# ========== TAB 4: ADMIN ==========
with tab4:
    st.markdown("## ⚙️ ADMIN")
    password = st.text_input("Contraseña", type="password")
    
    if verificar_admin(password):
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        tabs = st.tabs(["📋 INSCRIPCIONES", "🏆 BRACKETS", "📊 ESTADÍSTICAS"])
        
        with tabs[0]:
            df_admin = leer_inscripciones()
            if not df_admin.empty:
                st.dataframe(df_admin, use_container_width=True, hide_index=True)
                csv = df_admin.to_csv(index=False)
                st.download_button("📥 DESCARGAR CSV", csv, "inscripciones.csv", use_container_width=True)
        
        with tabs[1]:
            df_b = leer_brackets()
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                
                # Editor de ganadores
                with st.expander("Actualizar ganadores"):
                    with st.form("edit_brackets"):
                        categorias_b = df_b['Categoria'].unique()
                        cat_b = st.selectbox("Categoría", categorias_b)
                        
                        df_cat_b = df_b[df_b['Categoria'] == cat_b]
                        partido_id = st.selectbox("Partido", df_cat_b['Partido_ID'].unique())
                        
                        df_partido = df_cat_b[df_cat_b['Partido_ID'] == partido_id].iloc[0]
                        
                        if df_partido['Competidor1'] != "BYE" and df_partido['Competidor2'] != "BYE":
                            opciones = [df_partido['Competidor1'], df_partido['Competidor2']]
                            ganador = st.radio("Ganador", opciones)
                            
                            if st.form_submit_button("ACTUALIZAR"):
                                df_b.loc[(df_b['Categoria'] == cat_b) & (df_b['Partido_ID'] == partido_id), 'Ganador'] = ganador
                                guardar_brackets(df_b)
                                st.success("✅ Actualizado")
                                st.rerun()
                
                if st.button("🔄 REGENERAR BRACKETS", use_container_width=True):
                    df_vacio = pd.DataFrame(columns=df_b.columns)
                    guardar_brackets(df_vacio)
                    r, m = generar_brackets_dinamicos()
                    st.success(m)
                    st.rerun()
        
        with tabs[2]:
            df_stats = leer_inscripciones()
            if not df_stats.empty:
                df_conf = df_stats[df_stats['Estado'] == 'CONFIRMADO']
                col1, col2, col3 = st.columns(3)
                with col1:
                    total = len(df_conf[df_conf['Metodo'] != 'VIP']) * PRECIO
                    st.metric("Ingresos", formatear_peso(total))
                with col2:
                    st.metric("VIP", len(df_stats[df_stats['Metodo'] == 'VIP']))
                with col3:
                    st.metric("Pendientes", len(df_stats[df_stats['Metodo'] == 'Pendiente']))
        
        st.markdown('</div>', unsafe_allow_html=True)
    elif password:
        st.error("❌ Contraseña incorrecta")

# === FOOTER ===
st.markdown("""
<div style="text-align:center; color:#666; padding:30px 0; border-top:1px solid #333;">
    <p>© 2024 World Kyokushin Budokai Chile · Brackets Dinámicos</p>
</div>
""", unsafe_allow_html=True)
