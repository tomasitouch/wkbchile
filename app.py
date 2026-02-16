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

# === 1. CONFIGURACIÓN INICIAL Y ESTADO ===
st.set_page_config(
    page_title="WKB WORLD CUP 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inicializar Estado de Admin si no existe
if 'admin_logged_in' not in st.session_state:
    st.session_state['admin_logged_in'] = False

# === 2. CONSTANTES Y DATOS ===
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

# === 3. ESTILOS CSS PROFESIONALES (FUTURISTA / NEÓN) ===
st.markdown("""
<style>
    /* FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');

    /* FONDO GENERAL */
    .stApp {
        background-color: #050505;
        background-image: 
            radial-gradient(at 50% 0%, #2a0a0a 0%, transparent 70%),
            linear-gradient(180deg, #050505 0%, #1a0505 100%);
        font-family: 'Rajdhani', sans-serif;
        color: #e0e0e0;
    }

    /* SCROLLBAR INVISIBLE PERO FUNCIONAL */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0a0a0a; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #ff2b2b; }

    /* TYPOGRAPHY */
    h1, h2, h3, .big-font {
        font-family: 'Orbitron', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        background: -webkit-linear-gradient(#fff, #aaa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 0px 20px rgba(255, 43, 43, 0.3);
    }
    
    /* TARJETAS DE CRISTAL (GLASSMORPHISM) */
    .glass-card {
        background: rgba(20, 20, 20, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }

    /* BOTONES PERSONALIZADOS */
    .stButton > button {
        background: linear-gradient(135deg, #8b0000 0%, #ff2b2b 100%);
        color: white !important;
        font-family: 'Orbitron', sans-serif !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.6rem 1.2rem !important;
        text-transform: uppercase;
        font-weight: bold !important;
        transition: all 0.3s ease;
        box-shadow: 0 0 15px rgba(255, 43, 43, 0.4);
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 25px rgba(255, 43, 43, 0.7);
    }

    /* INPUTS */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 4px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #ff2b2b !important;
        box-shadow: 0 0 10px rgba(255, 43, 43, 0.2) !important;
    }

    /* COUNTDOWN */
    .countdown-box {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin: 30px 0;
        flex-wrap: wrap;
    }
    .time-unit {
        background: rgba(0,0,0,0.5);
        border: 1px solid #333;
        padding: 15px 20px;
        border-radius: 8px;
        text-align: center;
        min-width: 90px;
        border-bottom: 3px solid #ff2b2b;
    }
    .time-val { font-family: 'Orbitron'; font-size: 1.8rem; font-weight: 900; color: #fff; }
    .time-label { font-size: 0.7rem; color: #888; letter-spacing: 1px; margin-top: 5px; }

    /* --- ESTILOS DE BRACKETS (ÁRBOL) --- */
    
    .bracket-wrapper {
        display: flex;
        justify-content: center; /* Centrar todo el árbol */
        padding: 20px 0;
        overflow-x: auto;
    }

    .bracket-container {
        display: flex;
        flex-direction: row;
        gap: 40px;
    }

    .round-column {
        display: flex;
        flex-direction: column;
        justify-content: space-around; /* LA CLAVE DE LA SIMETRÍA VERTICAL */
        width: 260px;
        position: relative;
    }

    .match-card {
        background: #111;
        border: 1px solid #333;
        border-radius: 6px;
        margin: 10px 0;
        position: relative;
        box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        transition: transform 0.2s;
        z-index: 2;
    }
    .match-card:hover {
        border-color: #666;
        transform: scale(1.02);
    }

    .competitor {
        padding: 8px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 45px;
    }
    
    .aka { border-left: 4px solid #ff2b2b; border-bottom: 1px solid #222; } /* Rojo */
    .ao  { border-left: 4px solid #1e90ff; } /* Azul */
    
    .winner-bg { background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, transparent 100%); }
    .winner-text { color: #ffd700; font-weight: bold; text-shadow: 0 0 5px rgba(255, 215, 0, 0.5); }
    
    .match-id {
        position: absolute;
        top: -8px; right: 5px;
        background: #000;
        color: #555;
        font-size: 0.6rem;
        padding: 1px 5px;
        border: 1px solid #333;
        border-radius: 4px;
    }

    /* CONECTORES (LÍNEAS) */
    .connector {
        position: absolute;
        top: 50%;
        right: -42px; /* Conecta con la siguiente columna */
        width: 42px;
        height: 2px;
        background: #444;
        z-index: 1;
    }

    /* OPTIMIZACIÓN MÓVIL (ZOOM OUT PARA ENCAJAR) */
    @media (max-width: 768px) {
        .bracket-wrapper {
            justify-content: flex-start; /* Alinear a la izq para permitir scroll si es necesario */
            transform-origin: top left;
            /* Truco para "ver toda la llave": reducir escala */
            zoom: 0.65; 
        }
        .round-column {
            width: 220px; /* Tarjetas un poco más estrechas */
            margin-right: 10px;
        }
        .connector {
            width: 30px;
            right: -30px;
        }
        h1 { font-size: 1.5rem !important; }
        .countdown-box { gap: 5px; }
        .time-unit { padding: 10px; min-width: 60px; }
        .time-val { font-size: 1.2rem; }
    }

</style>
""", unsafe_allow_html=True)

# === 4. FUNCIONES DE BACKEND ===

def generar_id(nombre, email):
    texto = f"{nombre}{email}{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

def validar_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

def formatear_peso(valor):
    return f"${valor:,.0f}".replace(",", ".")

def tiempo_restante():
    delta = FECHA_TORNEO - datetime.now()
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return dias, horas, minutos, segundos

def verificar_admin_pass(password):
    # En producción usar st.secrets["admin_password"]
    # Para demostración usamos "admin123"
    pass_real = st.secrets["general"]["admin_token_hash"] if "general" in st.secrets else hashlib.sha256("admin123".encode()).hexdigest()
    pass_input = hashlib.sha256(password.encode()).hexdigest()
    return pass_input == pass_real

# --- GOOGLE SHEETS ---
@st.cache_data(ttl=5)
def leer_datos(hoja):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=hoja, ttl=0)
        return df.fillna("")
    except:
        cols = ["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo"] if hoja == "Inscripciones" else \
               ["Categoria", "Ronda", "Partido_ID", "Competidor1", "Competidor2", "Ganador", "Posicion", "Total_Rondas", "Dojo1", "Dojo2"]
        return pd.DataFrame(columns=cols)

def guardar_datos(hoja, df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=hoja, data=df)
        return True
    except Exception as e:
        st.error(f"Error Database: {e}")
        return False

# --- LÓGICA DE TORNEO ---
def generar_brackets_logica():
    df = leer_datos("Inscripciones")
    if df.empty: return False, "No hay datos de inscripción."
    
    df_conf = df[df['Estado'] == 'CONFIRMADO']
    if df_conf.empty: return False, "No hay competidores confirmados."

    todos_partidos = []
    pid = 1
    
    for cat in CATEGORIAS:
        inscritos = df_conf[df_conf['Categoria'] == cat].to_dict('records')
        n = len(inscritos)
        
        if n < 2: continue # Necesita al menos 2
        
        random.shuffle(inscritos)
        rondas = math.ceil(math.log2(n))
        capacidad = 2**rondas
        
        # Rellenar con BYEs
        lista = inscritos + [None]*(capacidad - n)
        
        # Ronda 1
        for i in range(0, len(lista), 2):
            c1, c2 = lista[i], lista[i+1]
            
            n1 = c1['Nombre'] if c1 else "BYE"
            d1 = c1['Dojo'] if c1 else "-"
            n2 = c2['Nombre'] if c2 else "BYE"
            d2 = c2['Dojo'] if c2 else "-"
            
            # Auto-Winner si es BYE
            ganador = ""
            if n1 == "BYE": ganador = n2
            elif n2 == "BYE": ganador = n1
            
            todos_partidos.append({
                "Categoria": cat, "Ronda": 1, "Partido_ID": pid,
                "Competidor1": n1, "Dojo1": d1,
                "Competidor2": n2, "Dojo2": d2,
                "Ganador": ganador,
                "Posicion": i//2, "Total_Rondas": rondas
            })
            pid += 1
            
        # Rondas Vacías
        matches_count = capacidad // 2
        for r in range(2, rondas + 1):
            matches_count //= 2
            for j in range(matches_count):
                todos_partidos.append({
                    "Categoria": cat, "Ronda": r, "Partido_ID": pid,
                    "Competidor1": "", "Dojo1": "",
                    "Competidor2": "", "Dojo2": "",
                    "Ganador": "",
                    "Posicion": j, "Total_Rondas": rondas
                })
                pid += 1
                
    if todos_partidos:
        guardar_datos("Brackets", pd.DataFrame(todos_partidos))
        return True, "Brackets generados correctamente."
    return False, "Error al generar brackets o faltan competidores."

# === 5. INTERFAZ DE USUARIO ===

# --- HEADER ---
col_L, col_C, col_R = st.columns([1, 6, 1])
with col_C:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{LOGO_URL}" style="width: 120px; filter: drop-shadow(0 0 10px #ff2b2b);">
        <h1 style="margin-top: 10px; font-size: 3rem;">WORLD CUP 2026</h1>
        <p style="color: #888; letter-spacing: 3px; font-size: 0.9rem;">SANTIAGO · CHILE · ABRIL 2026</p>
    </div>
    """, unsafe_allow_html=True)

# COUNTDOWN
d, h, m, s = tiempo_restante()
st.markdown(f"""
<div class="countdown-box">
    <div class="time-unit"><div class="time-val">{d}</div><div class="time-label">DÍAS</div></div>
    <div class="time-unit"><div class="time-val">{h}</div><div class="time-label">HRS</div></div>
    <div class="time-unit"><div class="time-val">{m}</div><div class="time-label">MIN</div></div>
    <div class="time-unit"><div class="time-val">{s}</div><div class="time-label">SEG</div></div>
</div>
""", unsafe_allow_html=True)

# --- NAVEGACIÓN ---
tab_dash, tab_insc, tab_keys, tab_admin = st.tabs(["📊 DASHBOARD", "📝 INSCRIPCIÓN", "🏆 LLAVES (BRACKETS)", "🔒 ADMIN"])

# ================= TAB 1: DASHBOARD =================
with tab_dash:
    st.markdown("### 📊 ESTADÍSTICAS DEL EVENTO")
    df_insc = leer_datos("Inscripciones")
    
    if not df_insc.empty:
        df_ok = df_insc[df_insc['Estado'] == 'CONFIRMADO']
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Competidores", len(df_ok), delta="Confirmados")
        c2.metric("Categorías", df_ok['Categoria'].nunique())
        c3.metric("Dojos", df_ok['Dojo'].nunique())
        c4.metric("Países", df_ok['Pais'].nunique())
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        counts = df_ok['Categoria'].value_counts().sort_values()
        fig = px.bar(x=counts.values, y=counts.index, orientation='h', 
                     color=counts.values, color_continuous_scale=['#330000', '#ff2b2b'],
                     title="Inscritos por Categoría")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', 
                          font_color='white', font_family='Rajdhani')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Aún no hay inscripciones registradas.")

# ================= TAB 2: INSCRIPCIÓN =================
with tab_insc:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### 📝 FORMULARIO OFICIAL")
        st.markdown("Complete sus datos para participar en el evento más grande del año.")
        
        with st.form("registro"):
            nombre = st.text_input("Nombre Completo")
            col_a, col_b = st.columns(2)
            email = col_a.text_input("Email")
            telefono = col_b.text_input("Teléfono")
            
            col_c, col_d, col_e = st.columns(3)
            edad = col_c.number_input("Edad", 18, 99, 25)
            dojo = col_d.text_input("Dojo")
            pais = col_e.selectbox("País", PAISES)
            
            categoria = st.selectbox("Categoría", CATEGORIAS)
            
            st.divider()
            st.caption(f"Valor Inscripción: {formatear_peso(PRECIO)} CLP")
            metodo = st.radio("Método de Pago", ["Transferencia / Pago Posterior", "Código VIP"], horizontal=True)
            vip_code = ""
            if metodo == "Código VIP":
                vip_code = st.text_input("Ingrese Código VIP", type="password")
            
            check = st.checkbox("Acepto las bases del torneo y eximo de responsabilidad a la organización.")
            
            btn = st.form_submit_button("CONFIRMAR INSCRIPCIÓN")
            
            if btn:
                err = []
                if len(nombre) < 3: err.append("Nombre inválido.")
                if not validar_email(email): err.append("Email inválido.")
                if not dojo: err.append("Indique su Dojo.")
                if not check: err.append("Debe aceptar las bases.")
                if metodo == "Código VIP" and vip_code != CODIGO_VIP: err.append("Código VIP incorrecto.")
                
                if not err:
                    nuevo_usuario = pd.DataFrame([{
                        "ID": generar_id(nombre, email),
                        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Nombre": nombre.upper(), "Email": email.lower(), "Telefono": telefono,
                        "Edad": edad, "Dojo": dojo.upper(), "Pais": pais,
                        "Categoria": categoria, "Estado": "CONFIRMADO",
                        "Metodo": "VIP" if metodo == "Código VIP" else "Pendiente"
                    }])
                    df_old = leer_datos("Inscripciones")
                    guardar_datos("Inscripciones", pd.concat([df_old, nuevo_usuario], ignore_index=True))
                    st.success("✅ ¡Inscripción Exitosa! Nos vemos en el Tatami.")
                else:
                    for e in err: st.error(e)

    with c2:
        st.image("https://images.unsplash.com/photo-1555597673-b21d5c935865?q=80&w=2072&auto=format&fit=crop", caption="El espíritu del Kyokushin")
        st.markdown("""
        <div class="glass-card">
            <h4>🥋 Información Importante</h4>
            <ul>
                <li>El pesaje se realizará el día anterior al evento.</li>
                <li>Es obligatorio presentar documento de identidad.</li>
                <li>Protectores bucales y inguinales son obligatorios.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ================= TAB 3: LLAVES (VISUALIZACIÓN PÚBLICA) =================
with tab_keys:
    st.markdown("### 🏆 ÁRBOL DE COMPETENCIA")
    
    df_brackets = leer_datos("Brackets")
    
    if df_brackets.empty:
        st.warning("🚧 Las llaves aún no han sido generadas por la organización.")
    else:
        cat_seleccionada = st.selectbox("📂 Seleccione una Categoría para ver el desarrollo", df_brackets['Categoria'].unique())
        
        df_cat = df_brackets[df_brackets['Categoria'] == cat_seleccionada]
        
        if not df_cat.empty:
            total_rondas = int(df_cat['Total_Rondas'].iloc[0])
            rondas_unicas = sorted(df_cat['Ronda'].unique())
            
            # --- CONSTRUCCIÓN DEL HTML PROLIJO Y SIMÉTRICO ---
            
            # Wrapper principal que permite scroll y centra el contenido
            html = '<div class="bracket-wrapper"><div class="bracket-container">'
            
            for r in rondas_unicas:
                matches = df_cat[df_cat['Ronda'] == r].sort_values('Posicion')
                
                # Nombre de la Ronda
                nombre_ronda = "🏆 GRAN FINAL" if r == total_rondas else ("SEMIFINAL" if r == total_rondas-1 else f"RONDA {r}")
                color_titulo = "#ffd700" if r == total_rondas else "#ff2b2b"
                
                html += f'<div class="round-column">'
                html += f'<div style="text-align:center; color:{color_titulo}; font-weight:bold; margin-bottom:15px; border-bottom:1px solid {color_titulo}; padding-bottom:5px; font-family:Orbitron;">{nombre_ronda}</div>'
                
                for _, m in matches.iterrows():
                    # Datos
                    p_id = str(m['Partido_ID'])
                    c1 = m['Competidor1'] if m['Competidor1'] else "---"
                    c2 = m['Competidor2'] if m['Competidor2'] else "---"
                    d1 = m['Dojo1'] if m['Dojo1'] else ""
                    d2 = m['Dojo2'] if m['Dojo2'] else ""
                    ganador = m['Ganador']
                    
                    # Lógica Visual de Ganadores
                    win1 = (ganador == c1 and ganador not in ["", "---", "BYE"])
                    win2 = (ganador == c2 and ganador not in ["", "---", "BYE"])
                    
                    cls_bg1 = "winner-bg" if win1 else ""
                    cls_bg2 = "winner-bg" if win2 else ""
                    cls_txt1 = "winner-text" if win1 else "color:white;"
                    cls_txt2 = "winner-text" if win2 else "color:white;"
                    
                    # Badge de BYE
                    badge_bye = ""
                    if c1 == "BYE" or c2 == "BYE":
                        badge_bye = '<span style="position:absolute; top:-8px; left:5px; background:gold; color:black; font-size:0.6rem; padding:1px 4px; border-radius:4px; font-weight:bold;">⭐ BYE</span>'

                    # Línea conectora (solo si no es la final)
                    conector_html = '<div class="connector"></div>' if r < total_rondas else ''

                    # HTML de la Tarjeta
                    html += f'''
                    <div class="match-card">
                        <div class="match-id">#{p_id}</div>
                        {badge_bye}
                        
                        <div class="competitor aka {cls_bg1}">
                            <div style="display:flex; flex-direction:column;">
                                <span style="font-size:0.85rem; {cls_txt1}">{c1}</span>
                                <span style="font-size:0.6rem; color:#888;">{d1}</span>
                            </div>
                        </div>
                        
                        <div class="competitor ao {cls_bg2}">
                            <div style="display:flex; flex-direction:column;">
                                <span style="font-size:0.85rem; {cls_txt2}">{c2}</span>
                                <span style="font-size:0.6rem; color:#888;">{d2}</span>
                            </div>
                        </div>
                        
                        {conector_html}
                    </div>
                    '''
                
                html += '</div>' # Fin Round Column
            
            html += '</div></div>' # Fin Bracket Wrapper
            
            st.markdown(html, unsafe_allow_html=True)
            
            # Leyenda
            st.markdown("""
            <div style="text-align:center; font-size:0.8rem; color:#666; margin-top:10px;">
                <span style="margin-right:15px; color:#ff2b2b;">▍ AKA (Rojo)</span>
                <span style="margin-right:15px; color:#1e90ff;">▍ AO (Azul)</span>
                <span style="color:#ffd700;">★ Ganador</span>
            </div>
            """, unsafe_allow_html=True)

# ================= TAB 4: ADMIN (PROTEGIDO) =================
with tab_admin:
    st.markdown("### 🔒 PANEL DE ADMINISTRACIÓN")
    
    # Login simple
    if not st.session_state['admin_logged_in']:
        col_login, _ = st.columns([1, 2])
        with col_login:
            pwd = st.text_input("Ingrese Contraseña de Administrador", type="password")
            if st.button("INGRESAR"):
                if verificar_admin_pass(pwd):
                    st.session_state['admin_logged_in'] = True
                    st.success("Bienvenido Admin.")
                    st.rerun()
                else:
                    st.error("Acceso Denegado.")
    
    else:
        # MENÚ DE ADMIN
        col_logout, _ = st.columns([1,5])
        if col_logout.button("Cerrar Sesión"):
            st.session_state['admin_logged_in'] = False
            st.rerun()
            
        st.divider()
        
        st.markdown("#### 🛠️ GESTIÓN DE TORNEO")
        
        c_gen, c_data, c_res = st.columns(3)
        
        with c_gen:
            st.info("Generación de Llaves")
            if st.button("🔄 GENERAR / REINICIAR BRACKETS"):
                with st.spinner("Procesando inscripciones y creando cruces aleatorios..."):
                    ok, msg = generar_brackets_logica()
                    if ok: st.success(msg)
                    else: st.error(msg)
        
        with c_data:
            st.info("Descargar Datos")
            df_ins = leer_datos("Inscripciones")
            if not df_ins.empty:
                csv = df_ins.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar CSV Inscritos", data=csv, file_name="inscritos_wkb2026.csv", mime="text/csv")
        
        st.divider()
        
        # GESTIÓN DE RESULTADOS
        st.markdown("#### 🏆 ARBITRAJE Y RESULTADOS")
        df_b = leer_datos("Brackets")
        
        if not df_b.empty:
            c_sel_cat, c_sel_match = st.columns(2)
            cat_b = c_sel_cat.selectbox("Categoría a arbitrar", df_b['Categoria'].unique())
            
            df_cat_b = df_b[df_b['Categoria'] == cat_b]
            match_options = df_cat_b[df_cat_b['Competidor1'] != ""] # Filtrar vacíos
            
            # Crear una etiqueta legible para el selector
            match_dict = {f"Combate #{row['Partido_ID']}: {row['Competidor1']} vs {row['Competidor2']} (R{row['Ronda']})": row['Partido_ID'] for _, row in match_options.iterrows()}
            
            sel_label = c_sel_match.selectbox("Seleccionar Combate", list(match_dict.keys()))
            pid_sel = match_dict[sel_label]
            
            # Datos del combate seleccionado
            match_data = df_cat_b[df_cat_b['Partido_ID'] == pid_sel].iloc[0]
            
            col_fight, col_action = st.columns([2, 1])
            
            with col_fight:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                    <h3>COMBATE #{pid_sel}</h3>
                    <div style="display:flex; justify-content:space-between; align-items:center; font-size:1.2rem;">
                        <span style="color:#ff2b2b; font-weight:bold;">{match_data['Competidor1']}</span>
                        <span style="color:#888;">VS</span>
                        <span style="color:#1e90ff; font-weight:bold;">{match_data['Competidor2']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_action:
                st.markdown("**Declarar Ganador:**")
                # Solo si no son BYE
                c1 = match_data['Competidor1']
                c2 = match_data['Competidor2']
                
                if c1 != "BYE" and c2 != "BYE":
                    ganador_input = st.radio("Ganador", [c1, c2], key="win_radio")
                    if st.button("CONFIRMAR RESULTADO"):
                        df_b.loc[df_b['Partido_ID'] == pid_sel, 'Ganador'] = ganador_input
                        guardar_datos("Brackets", df_b)
                        st.success(f"Victoria registrada para {ganador_input}")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("Este combate es un BYE, el ganador es automático.")
