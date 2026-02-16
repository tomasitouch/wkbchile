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
        # En producción usa st.secrets, aquí simulamos para que no falle si no hay secrets
        try:
            hash_real = st.secrets["general"]["admin_token_hash"]
            hash_input = hashlib.sha256(password.encode()).hexdigest()
            return hash_input == hash_real
        except:
            return password == "admin123" # Fallback temporal
    return False

# === FUNCIONES DE GOOGLE SHEETS ===
@st.cache_data(ttl=5)
def leer_inscripciones():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Inscripciones", ttl=0)
        if df.empty:
            return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo"])
        return df
    except:
        return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo"])

def guardar_inscripcion(datos):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            df_existente = leer_inscripciones()
        except:
            df_existente = pd.DataFrame()
            
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
        st.error(f"Error al guardar: {e}")
        return False

@st.cache_data(ttl=5)
def leer_brackets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Brackets", ttl=0)
        if df.empty:
            return pd.DataFrame(columns=["Categoria", "Ronda", "Partido_ID", "Competidor1", "Dojo1", "Competidor2", "Dojo2", "Ganador", "Siguiente_Partido", "Posicion", "Total_Rondas"])
        return df
    except:
        return pd.DataFrame(columns=["Categoria", "Ronda", "Partido_ID", "Competidor1", "Dojo1", "Competidor2", "Dojo2", "Ganador", "Siguiente_Partido", "Posicion", "Total_Rondas"])

def guardar_brackets(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except:
        return False

# === GENERADOR DE BRACKETS ===
def generar_brackets_dinamicos():
    df = leer_inscripciones()
    if df.empty: return False, "No hay inscripciones"
    
    df_conf = df[df['Estado'] == 'CONFIRMADO'].copy()
    if len(df_conf) < 2: return False, "Se necesitan al menos 2 competidores"
    
    todos_partidos = []
    stats_categorias = {}
    partido_id_global = 1
    
    for categoria in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == categoria]
        num_competidores = len(df_cat)
        
        if num_competidores >= 2:
            participantes = df_cat.to_dict('records')
            random.shuffle(participantes)
            
            num_rondas = math.ceil(math.log2(num_competidores))
            capacidad_total = 2 ** num_rondas
            
            stats_categorias[categoria] = {'competidores': num_competidores, 'rondas': num_rondas}
            
            competidores_lista = participantes.copy()
            byes_necesarios = capacidad_total - num_competidores
            
            # Insertar Byes distribuidos
            for i in range(byes_necesarios):
                competidores_lista.insert(i * 2, None) # Estrategia simple de distribución
            
            # Primera Ronda
            ronda_actual_parts = []
            
            # Generar Round 1
            for i in range(0, len(competidores_lista), 2):
                if i + 1 < len(competidores_lista):
                    c1 = competidores_lista[i]
                    c2 = competidores_lista[i + 1]
                    
                    p = {
                        "Categoria": categoria, "Ronda": 1, "Partido_ID": partido_id_global,
                        "Competidor1": c1['Nombre'] if c1 else "BYE", "Dojo1": c1.get('Dojo', '-') if c1 else "-",
                        "Competidor2": c2['Nombre'] if c2 else "BYE", "Dojo2": c2.get('Dojo', '-') if c2 else "-",
                        "Ganador": "", "Posicion": i // 2, "Total_Rondas": num_rondas
                    }
                    
                    # Auto-win si es BYE
                    if p['Competidor1'] == "BYE": p['Ganador'] = p['Competidor2']
                    elif p['Competidor2'] == "BYE": p['Ganador'] = p['Competidor1']
                    
                    todos_partidos.append(p)
                    partido_id_global += 1
            
            # Generar Rondas siguientes (vacías)
            partidos_nivel = capacidad_total // 2
            for r in range(2, num_rondas + 1):
                partidos_nivel //= 2
                for j in range(partidos_nivel):
                    p = {
                        "Categoria": categoria, "Ronda": r, "Partido_ID": partido_id_global,
                        "Competidor1": "", "Dojo1": "", "Competidor2": "", "Dojo2": "",
                        "Ganador": "", "Posicion": j, "Total_Rondas": num_rondas
                    }
                    todos_partidos.append(p)
                    partido_id_global += 1

    if todos_partidos:
        df_brackets = pd.DataFrame(todos_partidos)
        if guardar_brackets(df_brackets):
            return True, "✅ Brackets generados correctamente"
    
    return False, "Error al generar"

# === CSS ESTILO ÁRBOL HORIZONTAL ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1a0505 0%, #000000 100%);
        font-family: 'Rajdhani', sans-serif;
    }
    
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: white !important; }
    
    /* SCROLLBAR */
    ::-webkit-scrollbar { height: 10px; width: 10px; }
    ::-webkit-scrollbar-track { background: #0a0c10; }
    ::-webkit-scrollbar-thumb { background: #ff2b2b; border-radius: 5px; }

    /* CONTENEDOR PRINCIPAL DEL BRACKET */
    .bracket-container {
        display: flex;
        flex-direction: row; /* Horizontal */
        overflow-x: auto;
        padding: 40px 20px;
        margin: 20px 0;
        background: rgba(0,0,0,0.3);
        border: 1px solid #333;
        border-radius: 12px;
        min-height: 600px;
    }

    /* COLUMNA DE RONDA */
    .round-column {
        display: flex;
        flex-direction: column;
        justify-content: space-around; /* CENTRADO VERTICAL AUTOMÁTICO */
        min-width: 280px;
        margin-right: 50px;
        position: relative;
    }

    .round-title {
        text-align: center;
        font-family: 'Orbitron';
        color: #ff2b2b;
        margin-bottom: 20px;
        border-bottom: 2px solid #ff2b2b;
        background: rgba(0,0,0,0.5);
        padding: 5px;
        position: absolute;
        top: -40px;
        width: 100%;
    }

    /* TARJETA DE PARTIDO COMPACTA */
    .match-card {
        background: #14161e;
        border: 1px solid #444;
        border-radius: 4px;
        margin: 10px 0;
        position: relative;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        display: flex;
        flex-direction: column;
        z-index: 2;
    }

    /* LÍNEAS CONECTORAS */
    .round-column:not(:last-child) .match-card::after {
        content: '';
        position: absolute;
        top: 50%;
        right: -50px; /* Largo de la línea */
        width: 50px;
        height: 2px;
        background: #555;
        z-index: 1;
    }

    /* SLOT COMPETIDOR */
    .competitor-slot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 10px;
        background: #222;
        border-bottom: 1px solid #333;
        height: 45px;
    }

    /* BORDES ROJO (AKA) Y AZUL (AO) */
    .competitor-slot:first-child { border-left: 4px solid #ff2b2b; }
    .competitor-slot:last-child { border-left: 4px solid #1e90ff; border-bottom: none; }

    /* ESTADO GANADOR */
    .competitor-slot.winner {
        background: rgba(255, 215, 0, 0.15);
    }
    .competitor-slot.winner .competitor-name {
        color: #ffd700;
        font-weight: bold;
    }
    .competitor-slot.winner::after {
        content: '✔';
        color: gold;
        margin-left: 5px;
    }

    .competitor-name {
        font-size: 0.9rem;
        color: #ddd;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 180px;
    }
    
    .match-meta {
        position: absolute;
        top: -8px;
        right: 5px;
        background: #000;
        color: #555;
        font-size: 0.6rem;
        padding: 0 4px;
        border: 1px solid #333;
    }
    
    /* UTILS */
    .glass-card {
        background: rgba(20, 22, 30, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 25px;
        margin: 20px 0;
    }
    .stButton > button {
        background: linear-gradient(90deg, #8b0000, #ff2b2b);
        color: white;
        border: none;
        width: 100%;
    }
    
    /* COUNTDOWN */
    .countdown-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin: 20px 0;
        text-align: center;
    }
    .countdown-number {
        font-family: 'Orbitron';
        font-size: 2rem;
        color: #ff2b2b;
    }
</style>
""", unsafe_allow_html=True)

# === HEADER ===
col1, col2, col3 = st.columns([1,2,1])
with col2:
    st.markdown(f"""
    <div style="text-align:center;">
        <img src="{LOGO_URL}" width="150">
        <h1>WORLD CUP 2026</h1>
        <p style="color:#888;">SANTIAGO · CHILE · ABRIL 2026</p>
    </div>
    """, unsafe_allow_html=True)

dias, horas, minutos, segundos = tiempo_restante()
st.markdown(f"""
<div class="countdown-grid">
    <div><div class="countdown-number">{dias}</div>DÍAS</div>
    <div><div class="countdown-number">{horas}</div>HRS</div>
    <div><div class="countdown-number">{minutos}</div>MIN</div>
    <div><div class="countdown-number">{segundos}</div>SEG</div>
</div>
""", unsafe_allow_html=True)

# === TABS ===
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "📝 INSCRIPCIÓN", "🏆 BRACKETS", "⚙️ ADMIN"])

# ========== TAB 1: DASHBOARD ==========
with tab1:
    st.markdown("## 📊 PANEL DE CONTROL")
    df = leer_inscripciones()
    if not df.empty:
        df_conf = df[df['Estado'] == 'CONFIRMADO']
        col1, col2, col3 = st.columns(3)
        col1.metric("INSCRITOS", len(df_conf))
        col2.metric("CATEGORÍAS", df_conf['Categoria'].nunique())
        col3.metric("DOJOS", df_conf['Dojo'].nunique())
        
        counts = df_conf['Categoria'].value_counts().reset_index()
        counts.columns = ['Categoria', 'Count']
        fig = px.bar(counts, x='Count', y='Categoria', orientation='h', color='Count', color_continuous_scale=['#440000', '#ff2b2b'])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin inscripciones aún")

# ========== TAB 2: INSCRIPCIÓN ==========
with tab2:
    st.markdown("## 📝 FORMULARIO")
    with st.form("form_inscripcion"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre Completo")
        email = col1.text_input("Email")
        telefono = col1.text_input("Teléfono")
        edad = col2.number_input("Edad", 18, 99, 25)
        dojo = col2.text_input("Dojo")
        pais = col2.selectbox("País", PAISES)
        categoria = st.selectbox("Categoría", CATEGORIAS)
        
        metodo = st.radio("Pago", ["VIP", "Normal"])
        vip_code = ""
        if metodo == "VIP": vip_code = st.text_input("Código VIP", type="password")
        
        if st.form_submit_button("ENVIAR"):
            if not nombre or not dojo:
                st.error("Faltan datos")
            elif metodo == "VIP" and vip_code != CODIGO_VIP:
                st.error("Código inválido")
            else:
                datos = {
                    'id': generar_id(nombre, email), 'nombre': nombre, 'email': email,
                    'telefono': telefono, 'edad': edad, 'dojo': dojo, 'pais': pais,
                    'categoria': categoria, 'metodo': metodo
                }
                if guardar_inscripcion(datos):
                    st.success("Inscrito!")
                    st.rerun()

# ========== TAB 3: BRACKETS (NUEVO DISEÑO) ==========
with tab3:
    st.markdown("## 🏆 BRACKETS DEL TORNEO")
    
    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("🔄 GENERAR LLAVES"):
            res, msg = generar_brackets_dinamicos()
            if res: st.success(msg); time.sleep(1); st.rerun()
            else: st.error(msg)
            
    df_brackets = leer_brackets()
    
    if not df_brackets.empty:
        cat_sel = st.selectbox("Categoría", df_brackets['Categoria'].unique())
        df_cat = df_brackets[df_brackets['Categoria'] == cat_sel]
        
        if not df_cat.empty:
            total_rondas = df_cat['Total_Rondas'].iloc[0]
            
            # --- RENDERIZADO FLEXBOX HORIZONTAL ---
            st.markdown('<div class="bracket-container">', unsafe_allow_html=True)
            
            rondas = sorted(df_cat['Ronda'].unique())
            for ronda in rondas:
                df_ronda = df_cat[df_cat['Ronda'] == ronda].sort_values('Posicion')
                
                nombre_ronda = "🏆 FINAL" if ronda == total_rondas else f"RONDA {ronda}"
                
                st.markdown(f'<div class="round-column"><div class="round-title">{nombre_ronda}</div>', unsafe_allow_html=True)
                
                for _, p in df_ronda.iterrows():
                    c1_win = "winner" if p['Ganador'] == p['Competidor1'] and p['Ganador'] else ""
                    c2_win = "winner" if p['Ganador'] == p['Competidor2'] and p['Ganador'] else ""
                    
                    st.markdown(f"""
                    <div class="match-card">
                        <div class="match-meta">#{p['Partido_ID']}</div>
                        <div class="competitor-slot {c1_win}">
                            <div style="display:flex; flex-direction:column;">
                                <span class="competitor-name">{p['Competidor1'] or '---'}</span>
                                <span style="font-size:0.6rem; color:#666;">{p['Dojo1']}</span>
                            </div>
                        </div>
                        <div class="competitor-slot {c2_win}">
                            <div style="display:flex; flex-direction:column;">
                                <span class="competitor-name">{p['Competidor2'] or '---'}</span>
                                <span style="font-size:0.6rem; color:#666;">{p['Dojo2']}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True) # End round-column
            
            st.markdown('</div>', unsafe_allow_html=True) # End bracket-container
    else:
        st.info("No hay brackets generados.")

# ========== TAB 4: ADMIN ==========
with tab4:
    st.markdown("## ⚙️ ADMIN")
    pwd = st.text_input("Password", type="password")
    if verificar_admin(pwd):
        st.success("Acceso concedido")
        df_b = leer_brackets()
        
        # Editor rápido de ganadores
        if not df_b.empty:
            st.markdown("### Actualizar Resultado")
            with st.form("admin_res"):
                pid = st.selectbox("ID Partido", df_b['Partido_ID'].unique())
                row = df_b[df_b['Partido_ID'] == pid].iloc[0]
                ganador = st.radio("Ganador", [row['Competidor1'], row['Competidor2']] if row['Competidor1'] else ["Pendiente"])
                
                if st.form_submit_button("Guardar"):
                    df_b.loc[df_b['Partido_ID'] == pid, 'Ganador'] = ganador
                    guardar_brackets(df_b)
                    st.rerun()
