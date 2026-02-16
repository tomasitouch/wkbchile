import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import random
import math
import time
from datetime import datetime
import re

# === CONFIGURACIÓN Y ESTADO ===
st.set_page_config(page_title="WKB WORLD CUP 2026", page_icon="🥋", layout="wide", initial_sidebar_state="collapsed")
if 'admin_logged_in' not in st.session_state: st.session_state['admin_logged_in'] = False

# === CONSTANTES ===
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
PRECIO = 15000
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
CODIGO_VIP = "WKB2026"
CATEGORIAS = ["KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)", "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)", "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino", "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"]
PAISES = ["Chile", "Argentina", "Perú", "Brasil", "Uruguay", "Paraguay", "Bolivia", "Ecuador", "Colombia", "Venezuela", "Otro"]

# === CSS PROFESIONAL Y SIMÉTRICO ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');
    
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(at 50% 0%, #2a0a0a 0%, transparent 70%);
        font-family: 'Rajdhani', sans-serif; color: #e0e0e0;
    }
    
    /* SCROLLBAR */
    ::-webkit-scrollbar { height: 10px; width: 10px; }
    ::-webkit-scrollbar-track { background: #0a0a0a; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 5px; }

    /* TYPOGRAPHY */
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; letter-spacing: 2px; }
    
    /* LOGO Y HEADER */
    .header-container { text-align: center; padding: 30px 20px; }
    .title-main { font-family: 'Orbitron'; font-size: 3rem; font-weight: 900; background: -webkit-linear-gradient(#fff, #aaa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top:10px; }
    .subtitle { color: #888; letter-spacing: 4px; font-size: 0.9rem; text-transform: uppercase; }

    /* COUNTDOWN */
    .countdown-box { display: flex; justify-content: center; gap: 15px; margin: 30px 0; }
    .time-unit { background: rgba(20,20,20,0.8); border: 1px solid #333; padding: 10px 20px; border-radius: 8px; text-align: center; min-width: 80px; border-bottom: 2px solid #ff2b2b; }
    .time-val { font-family: 'Orbitron'; font-size: 1.5rem; font-weight: bold; color: #fff; }
    .time-label { font-size: 0.7rem; color: #888; letter-spacing: 1px; }

    /* --- LOGICA DE ÁRBOL SIMÉTRICO (GRID FLEXIBLE) --- */
    
    .bracket-scroll {
        overflow-x: auto;
        padding: 40px 0;
        text-align: center;
    }

    .bracket-container {
        display: flex;
        flex-direction: row;
        /* El alto se define dinámicamente en Python según participantes */
    }

    .round-column {
        display: flex;
        flex-direction: column;
        width: 280px;
        height: 100%; /* Ocupa todo el alto disponible */
    }

    /* EL SPACER ES LA CLAVE DE LA ALINEACIÓN */
    .match-spacer {
        display: flex;
        flex-direction: column;
        justify-content: center; /* Centra la tarjeta verticalmente */
        flex: 1; /* Se estira para ocupar espacio equitativo */
        position: relative;
    }

    .match-card {
        background: rgba(15, 15, 20, 0.9);
        border: 1px solid #333;
        border-radius: 6px;
        margin: 0 15px; /* Margen lateral */
        position: relative;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        transition: transform 0.2s;
        z-index: 2;
        height: 80px; /* Altura fija para la tarjeta ayuda a la simetría */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .match-card:hover { border-color: #ff2b2b; transform: scale(1.02); }

    /* ESTILOS INTERNOS DE TARJETA */
    .competitor-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 4px 10px; height: 50%; font-size: 0.85rem;
    }
    .c-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }
    .c-dojo { font-size: 0.65rem; color: #666; margin-left: 5px; }
    
    .red-corner { border-left: 3px solid #ff2b2b; border-bottom: 1px solid #222; }
    .blue-corner { border-left: 3px solid #1e90ff; }
    
    .winner-bg { background: linear-gradient(90deg, rgba(255,215,0,0.15), transparent); }
    .winner-text { color: #ffd700; font-weight: bold; }

    /* CONECTORES PERFECTOS */
    /* Línea saliente (Derecha) */
    .connector-right {
        position: absolute;
        top: 50%;
        right: -15px; /* Conecta con el margen de la columna */
        width: 15px;
        height: 2px;
        background: #444;
        z-index: 1;
    }
    
    /* Línea entrante (Izquierda) */
    .connector-left {
        position: absolute;
        top: 50%;
        left: -15px;
        width: 15px;
        height: 2px;
        background: #444;
        z-index: 1;
    }
    
    /* TITULOS DE RONDA */
    .round-header {
        text-align: center;
        color: #ff2b2b;
        font-family: 'Orbitron';
        margin-bottom: 10px;
        height: 30px;
    }

    /* BADGES */
    .badge-id { position: absolute; top: -8px; right: 5px; background: #000; color: #555; font-size: 0.6rem; padding: 1px 5px; border: 1px solid #333; border-radius: 4px; }
    .badge-bye { position: absolute; top: -8px; left: 5px; background: gold; color: #000; font-size: 0.6rem; padding: 1px 5px; border-radius: 4px; font-weight: bold; }

</style>
""", unsafe_allow_html=True)

# === FUNCIONES BACKEND ===
def generar_id(nombre, email):
    texto = f"{nombre}{email}{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

def validar_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def formatear_peso(valor): return f"${valor:,.0f}".replace(",", ".")

def tiempo_restante():
    delta = FECHA_TORNEO - datetime.now()
    return delta.days, *divmod(delta.seconds // 3600, 24)[1:], divmod(delta.seconds % 3600, 60)[0], delta.seconds % 60

def verificar_admin(password):
    try: return hashlib.sha256(password.encode()).hexdigest() == st.secrets["general"]["admin_token_hash"]
    except: return password == "admin123"

# --- GOOGLE SHEETS ---
@st.cache_data(ttl=5)
def leer_datos(hoja):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(worksheet=hoja, ttl=0).fillna("")
    except:
        cols = ["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo"] if hoja == "Inscripciones" else ["Categoria", "Ronda", "Partido_ID", "Competidor1", "Competidor2", "Ganador", "Posicion", "Total_Rondas", "Dojo1", "Dojo2"]
        return pd.DataFrame(columns=cols)

def guardar_datos(hoja, df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=hoja, data=df)
        return True
    except: return False

# --- LOGICA TORNEO MEJORADA (DOJO SEPARATION) ---
def generar_brackets_logica():
    df = leer_datos("Inscripciones")
    if df.empty: return False, "No hay inscripciones."
    df_conf = df[df['Estado'] == 'CONFIRMADO']
    if len(df_conf) < 2: return False, "Mínimo 2 competidores."

    todos_partidos = []
    pid = 1
    
    for cat in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == cat]
        num_competidores = len(df_cat)
        if num_competidores < 2: continue
        
        # 1. Separación Inteligente por Dojos
        participantes = df_cat.to_dict('records')
        dojos = {}
        for p in participantes:
            dojos.setdefault(p['Dojo'], []).append(p)
        
        # Intercalar dojos (A, B, C, A, B, C...)
        lista_ordenada = []
        listas_dojos = sorted(dojos.values(), key=len, reverse=True)
        while any(listas_dojos):
            for lista_dojo in listas_dojos:
                if lista_dojo:
                    idx = random.randint(0, len(lista_dojo) - 1)
                    lista_ordenada.append(lista_dojo.pop(idx))
        
        # 2. Insertar BYEs aleatoriamente
        rondas = math.ceil(math.log2(num_competidores))
        capacidad = 2**rondas
        byes = capacidad - num_competidores
        
        competidores_final = lista_ordenada.copy()
        for _ in range(byes):
            competidores_final.insert(random.randint(0, len(competidores_final)), None)
            
        # 3. Generar Rondas
        # Ronda 1
        for i in range(0, len(competidores_final), 2):
            c1 = competidores_final[i]
            c2 = competidores_final[i+1]
            n1, d1 = (c1['Nombre'], c1['Dojo']) if c1 else ("BYE", "-")
            n2, d2 = (c2['Nombre'], c2['Dojo']) if c2 else ("BYE", "-")
            
            winner = ""
            if n1 == "BYE": winner = n2
            elif n2 == "BYE": winner = n1
            
            todos_partidos.append({
                "Categoria": cat, "Ronda": 1, "Partido_ID": pid,
                "Competidor1": n1, "Dojo1": d1, "Competidor2": n2, "Dojo2": d2,
                "Ganador": winner, "Posicion": i//2, "Total_Rondas": rondas
            })
            pid += 1
            
        # Rondas siguientes (Vacías)
        matches = capacidad // 2
        for r in range(2, rondas + 1):
            matches //= 2
            for j in range(matches):
                todos_partidos.append({
                    "Categoria": cat, "Ronda": r, "Partido_ID": pid,
                    "Competidor1": "", "Dojo1": "", "Competidor2": "", "Dojo2": "",
                    "Ganador": "", "Posicion": j, "Total_Rondas": rondas
                })
                pid += 1

    if todos_partidos:
        guardar_datos("Brackets", pd.DataFrame(todos_partidos))
        return True, "Brackets generados con separación de Dojos."
    return False, "Error al generar."

# === INTERFAZ ===
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" style="width: 120px;">
        <div class="title-main">WORLD CUP 2026</div>
        <div class="subtitle">SANTIAGO · CHILE</div>
    </div>
    """, unsafe_allow_html=True)

d, h, m, s = tiempo_restante()
st.markdown(f"""
<div class="countdown-box">
    <div class="time-unit"><div class="time-val">{d}</div><div class="time-label">DÍAS</div></div>
    <div class="time-unit"><div class="time-val">{h}</div><div class="time-label">HRS</div></div>
    <div class="time-unit"><div class="time-val">{m}</div><div class="time-label">MIN</div></div>
    <div class="time-unit"><div class="time-val">{s}</div><div class="time-label">SEG</div></div>
</div>
""", unsafe_allow_html=True)

tab_dash, tab_insc, tab_keys, tab_admin = st.tabs(["📊 DASHBOARD", "📝 INSCRIPCIÓN", "🏆 LLAVES (BRACKETS)", "⚡ ADMIN"])

with tab_dash:
    df_i = leer_datos("Inscripciones")
    if not df_i.empty:
        df_ok = df_i[df_i['Estado'] == 'CONFIRMADO']
        c1, c2, c3 = st.columns(3)
        c1.metric("INSCRITOS", len(df_ok))
        c2.metric("CATEGORÍAS", df_ok['Categoria'].nunique())
        c3.metric("DOJOS", df_ok['Dojo'].nunique())
        
        counts = df_ok['Categoria'].value_counts().sort_values()
        fig = px.bar(x=counts.values, y=counts.index, orientation='h', 
                     color=counts.values, color_continuous_scale=['#330000', '#ff2b2b'])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Sin inscripciones.")

with tab_insc:
    with st.form("reg"):
        nombre = st.text_input("Nombre")
        col_a, col_b = st.columns(2)
        email = col_a.text_input("Email")
        dojo = col_b.text_input("Dojo")
        cat = st.selectbox("Categoría", CATEGORIAS)
        metodo = st.radio("Pago", ["VIP", "Normal"])
        vip_c = st.text_input("Código VIP", type="password") if metodo == "VIP" else ""
        
        if st.form_submit_button("INSCRIBIR"):
            if nombre and dojo and (metodo != "VIP" or vip_c == CODIGO_VIP):
                nuevo = pd.DataFrame([{
                    "ID": generar_id(nombre, email), "Fecha": str(datetime.now()),
                    "Nombre": nombre.upper(), "Email": email, "Dojo": dojo.upper(),
                    "Categoria": cat, "Estado": "CONFIRMADO", "Metodo": metodo,
                    "Telefono": "", "Edad": 0, "Pais": "Chile"
                }])
                df_old = leer_datos("Inscripciones")
                guardar_datos("Inscripciones", pd.concat([df_old, nuevo], ignore_index=True))
                st.success("Inscrito!")
            else: st.error("Datos incompletos o código inválido.")

# === VISUALIZACIÓN DE BRACKETS SIMÉTRICOS ===
with tab_keys:
    st.markdown("### 🏆 Árbol de Competencia")
    df_b = leer_datos("Brackets")
    
    if not df_b.empty:
        cat_sel = st.selectbox("Ver Categoría", df_b['Categoria'].unique())
        df_cat = df_b[df_b['Categoria'] == cat_sel]
        
        if not df_cat.empty:
            total_rondas = int(df_cat['Total_Rondas'].iloc[0])
            rondas_unicas = sorted(df_cat['Ronda'].unique())
            
            # Calculamos altura dinámica: (Partidos en R1) * (Altura de tarjeta + espacio)
            max_partidos = len(df_cat[df_cat['Ronda'] == 1])
            altura_total = max_partidos * 130 # Pixeles estimados
            
            # Contenedor con scroll
            html = f'<div class="bracket-scroll"><div class="bracket-container" style="height: {altura_total}px; min-width: max-content;">'
            
            for r in rondas_unicas:
                matches = df_cat[df_cat['Ronda'] == r].sort_values('Posicion')
                titulo = "🏆 FINAL" if r == total_rondas else ("SEMIFINAL" if r == total_rondas-1 else f"RONDA {r}")
                
                html += f'<div class="round-column"><div class="round-header">{titulo}</div>'
                
                for _, m in matches.iterrows():
                    # Datos
                    pid = m['Partido_ID']
                    c1, c2 = m['Competidor1'], m['Competidor2']
                    ganador = m['Ganador']
                    
                    # Estilos Winner
                    w1 = "winner-text" if (ganador == c1 and ganador not in ["","BYE"]) else "color:white"
                    w2 = "winner-text" if (ganador == c2 and ganador not in ["","BYE"]) else "color:white"
                    bg1 = "winner-bg" if (ganador == c1 and ganador not in ["","BYE"]) else ""
                    bg2 = "winner-bg" if (ganador == c2 and ganador not in ["","BYE"]) else ""
                    
                    # Badge BYE
                    bye = '<span class="badge-bye">⭐ BYE</span>' if "BYE" in [c1, c2] else ""
                    
                    # Conectores
                    conn_r = '<div class="connector-right"></div>' if r < total_rondas else ''
                    conn_l = '<div class="connector-left"></div>' if r > 1 else ''

                    # TARJETA DENTRO DE SPACER (Flex 1 asegura el centrado vertical)
                    html += f'''
                    <div class="match-spacer">
                        {conn_l}
                        <div class="match-card">
                            <span class="badge-id">#{pid}</span>
                            {bye}
                            <div class="competitor-row red-corner {bg1}">
                                <span class="c-name" style="{w1}">{c1 or '---'}</span>
                                <span class="c-dojo">{m['Dojo1']}</span>
                            </div>
                            <div class="competitor-row blue-corner {bg2}">
                                <span class="c-name" style="{w2}">{c2 or '---'}</span>
                                <span class="c-dojo">{m['Dojo2']}</span>
                            </div>
                        </div>
                        {conn_r}
                    </div>
                    '''
                html += '</div>' # Cierra round-column
            
            html += '</div></div>' # Cierra bracket-container
            st.markdown(html, unsafe_allow_html=True)
            
            # Leyenda
            st.markdown("""
            <div style="text-align:center; margin-top:20px; color:#666; font-size:0.8rem;">
                <span style="color:#ff2b2b">█</span> Aka (Rojo) &nbsp;&nbsp; 
                <span style="color:#1e90ff">█</span> Ao (Azul) &nbsp;&nbsp; 
                <span style="color:#ffd700">★</span> Ganador
            </div>
            """, unsafe_allow_html=True)
    else: st.info("No hay brackets.")

with tab_admin:
    pwd = st.text_input("Password Admin", type="password")
    if verificar_admin(pwd):
        c1, c2 = st.columns(2)
        if c1.button("🔄 GENERAR BRACKETS (Con Seeding)"):
            ok, msg = generar_brackets_logica()
            if ok: st.success(msg)
            else: st.error(msg)
        
        df_b = leer_datos("Brackets")
        if not df_b.empty:
            cat = st.selectbox("Categoría Admin", df_b['Categoria'].unique())
            df_c = df_b[df_b['Categoria'] == cat]
            pid_sel = st.selectbox("ID Partido", df_c['Partido_ID'].unique())
            row = df_c[df_c['Partido_ID'] == pid_sel].iloc[0]
            
            # Solo permitir elegir si no son BYE
            if row['Competidor1'] != "BYE" and row['Competidor2'] != "BYE":
                win = st.radio("Ganador", [row['Competidor1'], row['Competidor2']])
                if st.button("Guardar Resultado"):
                    df_b.loc[df_b['Partido_ID'] == pid_sel, 'Ganador'] = win
                    guardar_datos("Brackets", df_b)
                    st.success("Guardado!")
            else: st.info("Partido Automático (BYE)")
