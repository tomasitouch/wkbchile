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
        # En producción usar st.secrets
        try:
            return hashlib.sha256(password.encode()).hexdigest() == st.secrets["general"]["admin_token_hash"]
        except:
            return password == "admin123" # Fallback para pruebas
    return False

# === FUNCIONES DE GOOGLE SHEETS ===
@st.cache_data(ttl=5)
def leer_inscripciones():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Inscripciones", ttl=0)
        df = df.fillna("") # Limpieza preventiva
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
    except:
        return False

@st.cache_data(ttl=5)
def leer_brackets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Brackets", ttl=0)
        df = df.fillna("") # Limpieza preventiva
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

# === GENERADOR DE BRACKETS DINÁMICOS ===
def generar_brackets_dinamicos():
    df = leer_inscripciones()
    if df.empty: return False, "No hay inscripciones"
    
    df_conf = df[df['Estado'] == 'CONFIRMADO'].copy()
    if len(df_conf) < 2: return False, "Se necesitan al menos 2 competidores"
    
    todos_partidos = []
    stats_categorias = {}
    pid = 1 # ID global único para partidos
    
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
            
            for i in range(byes_necesarios):
                competidores_lista.insert(random.randint(0, len(competidores_lista)), None)
            
            # Ronda 1
            for i in range(0, len(competidores_lista), 2):
                c1 = competidores_lista[i]
                c2 = competidores_lista[i + 1]
                
                # Manejo seguro de nombres
                n1 = c1['Nombre'] if c1 else "BYE"
                d1 = c1['Dojo'] if c1 else "-"
                n2 = c2['Nombre'] if c2 else "BYE"
                d2 = c2['Dojo'] if c2 else "-"
                
                winner = ""
                if n1 == "BYE": winner = n2
                elif n2 == "BYE": winner = n1

                partido = {
                    "Categoria": categoria, "Ronda": 1, "Partido_ID": pid,
                    "Competidor1": n1, "Dojo1": d1,
                    "Competidor2": n2, "Dojo2": d2,
                    "Ganador": winner,
                    "Posicion": i // 2, "Total_Rondas": num_rondas
                }
                todos_partidos.append(partido)
                pid += 1
            
            # Rondas siguientes
            partidos_por_ronda = capacidad_total // 2
            for ronda in range(2, num_rondas + 1):
                partidos_por_ronda = partidos_por_ronda // 2
                for j in range(partidos_por_ronda):
                    partido = {
                        "Categoria": categoria, "Ronda": ronda, "Partido_ID": pid,
                        "Competidor1": "", "Dojo1": "",
                        "Competidor2": "", "Dojo2": "",
                        "Ganador": "",
                        "Posicion": j, "Total_Rondas": num_rondas
                    }
                    todos_partidos.append(partido)
                    pid += 1

    if todos_partidos:
        df_brackets = pd.DataFrame(todos_partidos)
        if guardar_brackets(df_brackets):
            mensaje = "✅ Brackets generados:\n"
            for cat, stats in stats_categorias.items():
                mensaje += f"\n• {cat}: {stats['competidores']} luchadores"
            return True, mensaje
    
    return False, "No se generaron brackets"

# === CSS (SIN COMILLAS TRIPLES) ===
# Construimos el CSS linea por linea para evitar errores de parseo
css = "<style>"
css += "@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');"
css += ".stApp { background: radial-gradient(circle at 50% 0%, #1a0505 0%, #0a0c10 100%); font-family: 'Rajdhani', sans-serif; }"
css += "::-webkit-scrollbar { height: 10px; width: 10px; }"
css += "::-webkit-scrollbar-track { background: #0a0c10; }"
css += "::-webkit-scrollbar-thumb { background: #ff2b2b; border-radius: 5px; }"
css += "h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: white !important; text-shadow: 0 0 10px rgba(255, 43, 43, 0.5); }"
css += ".logo-container { text-align: center; padding: 20px 0; }"
css += ".logo-container img { width: min(350px, 80%); filter: drop-shadow(0 0 30px rgba(255, 43, 43, 0.4)); }"
css += ".countdown-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 30px 0; }"
css += ".countdown-item { background: linear-gradient(145deg, #1e2028, #14161e); border: 1px solid #333; border-radius: 15px; padding: 15px; text-align: center; }"
css += ".countdown-number { font-family: 'Orbitron', monospace; font-size: clamp(1.5rem, 4vw, 2.5rem); color: #ff2b2b; font-weight: 900; }"
css += ".glass-card { background: rgba(20, 22, 30, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-left: 4px solid #ff2b2b; border-radius: 16px; padding: 25px; margin: 20px 0; }"
css += ".stButton > button { background: linear-gradient(90deg, #8b0000, #ff2b2b); color: white !important; font-family: 'Orbitron', sans-serif !important; border: none !important; border-radius: 8px !important; padding: 12px 24px !important; font-weight: 600 !important; width: 100%; }"
css += "[data-testid='stMetricValue'] { font-family: 'Orbitron', monospace !important; color: #ff2b2b !important; font-size: 2rem !important; }"
css += "</style>"
st.markdown(css, unsafe_allow_html=True)

# === HEADER ===
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

# === TABS ===
tab1, tab2, tab3, tab4 = st.tabs(["📊 DASHBOARD", "📝 INSCRIPCIÓN", "🏆 BRACKETS", "⚙️ ADMIN"])

# ========== TAB 1: DASHBOARD ==========
with tab1:
    st.markdown("## 📊 PANEL DE CONTROL")
    df = leer_inscripciones()
    
    if not df.empty:
        df_conf = df[df['Estado'] == 'CONFIRMADO']
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("INSCRITOS", len(df_conf))
        col2.metric("CATEGORÍAS", df_conf['Categoria'].nunique())
        col3.metric("DOJOS", df_conf['Dojo'].nunique())
        col4.metric("CUPOS", 500 - len(df_conf))
        
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
        codigo_vip = ""
        if metodo_pago == "Código VIP":
            codigo_vip = st.text_input("Código VIP", type="password")
        
        terminos = st.checkbox("Acepto términos y condiciones")
        
        if st.form_submit_button("INSCRIBIRSE"):
            errores = []
            if not nombre or len(nombre.split()) < 2: errores.append("Nombre completo requerido")
            if not email or not validar_email(email): errores.append("Email inválido")
            if not telefono or len(telefono) < 8: errores.append("Teléfono inválido")
            if not dojo: errores.append("Dojo requerido")
            if not terminos: errores.append("Debes aceptar términos")
            if metodo_pago == "Código VIP" and codigo_vip != CODIGO_VIP: errores.append("Código VIP inválido")
            
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

# ========== TAB 3: BRACKETS (CORREGIDO) ==========
with tab3:
    st.markdown("## 🏆 BRACKETS DEL TORNEO")
    
    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("🔄 GENERAR LLAVES"):
            with st.spinner("Calculando cruces..."):
                resultado, mensaje = generar_brackets_dinamicos()
                if resultado:
                    st.success(mensaje)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning(mensaje)
    
    df_brackets = leer_brackets()
    
    if not df_brackets.empty:
        categorias = df_brackets['Categoria'].unique()
        cat_sel = st.selectbox("📂 Seleccionar categoría", categorias)
        
        df_cat = df_brackets[df_brackets['Categoria'] == cat_sel]
        
        if not df_cat.empty:
            total_rondas = int(df_cat['Total_Rondas'].iloc[0])
            rondas = sorted(df_cat['Ronda'].unique())
            
            # --- CONSTRUCCIÓN SEGURA DEL HTML ---
            # Usamos concatenación simple para evitar errores de sintaxis
            
            # Contenedor principal con Scroll Horizontal
            html = "<div style='overflow-x: auto; margin: 20px 0; padding-bottom: 20px;'>"
            html += "<div style='display: flex; flex-direction: row; gap: 40px; min-width: max-content; padding: 10px;'>"
            
            for ronda in rondas:
                df_ronda = df_cat[df_cat['Ronda'] == ronda].sort_values('Posicion')
                
                # Titulo de ronda
                if ronda == total_rondas: titulo = "🏆 FINAL"
                elif ronda == total_rondas - 1: titulo = "🥈 SEMIFINAL"
                elif ronda == total_rondas - 2: titulo = "🥉 CUARTOS"
                else: titulo = "RONDA " + str(ronda)
                
                # Columna de la ronda
                html += "<div style='display: flex; flex-direction: column; justify-content: space-around; flex-shrink: 0; width: 280px; position: relative;'>"
                html += "<div style='text-align: center; font-family: Orbitron; color: #ff2b2b; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px; padding-bottom: 8px; border-bottom: 2px solid #ff2b2b;'>" + titulo + "</div>"
                
                for _, p in df_ronda.iterrows():
                    # Datos seguros
                    id_p = str(p['Partido_ID'])
                    c1 = str(p['Competidor1']) if p['Competidor1'] else "---"
                    c2 = str(p['Competidor2']) if p['Competidor2'] else "---"
                    d1 = str(p['Dojo1']) if p['Dojo1'] else ""
                    d2 = str(p['Dojo2']) if p['Dojo2'] else ""
                    ganador = str(p['Ganador'])
                    
                    # Estilos dinámicos
                    c1_win = (ganador == c1 and ganador != "" and ganador != "---")
                    c2_win = (ganador == c2 and ganador != "" and ganador != "---")
                    
                    style1 = "background: rgba(255,215,0,0.15); border-left: 4px solid gold;" if c1_win else "border-left: 4px solid #ff2b2b;"
                    style2 = "background: rgba(255,215,0,0.15); border-left: 4px solid gold;" if c2_win else "border-left: 4px solid #1e90ff;"
                    
                    name_style1 = "color:#ffd700; font-weight:bold;" if c1_win else "color:#fff;"
                    name_style2 = "color:#ffd700; font-weight:bold;" if c2_win else "color:#fff;"
                    
                    # Elementos visuales
                    bye_badge = ""
                    if c1 == "BYE" or c2 == "BYE":
                        bye_badge = "<span style='position:absolute; top:-8px; left:5px; background:gold; color:black; font-size:0.6rem; padding:2px 6px; border-radius:10px; font-weight:bold;'>⭐ BYE</span>"
                    
                    conector = ""
                    if ronda < total_rondas:
                        conector = "<div style='position:absolute; top:50%; right:-40px; width:40px; height:2px; background:linear-gradient(90deg, #555, #222);'></div>"
                    
                    # Construcción de la tarjeta
                    html += "<div style='background: #14161e; border: 1px solid #444; border-radius: 6px; margin: 15px 0; position: relative; box-shadow: 0 4px 10px rgba(0,0,0,0.5);'>"
                    html += "<span style='position: absolute; top: -8px; right: 5px; background: #000; color: #666; font-size: 0.6rem; padding: 2px 6px; border: 1px solid #333; border-radius: 4px;'>#" + id_p + "</span>"
                    html += bye_badge
                    html += conector
                    
                    # Competidor 1
                    html += "<div style='padding: 8px 12px; border-bottom: 1px solid #333; " + style1 + "'>"
                    html += "<div><span style='font-size:0.9rem; " + name_style1 + "'>" + c1 + "</span></div>"
                    html += "<div><span style='font-size:0.65rem; color:#888;'>" + d1 + "</span></div>"
                    html += "</div>"
                    
                    # Competidor 2
                    html += "<div style='padding: 8px 12px; " + style2 + "'>"
                    html += "<div><span style='font-size:0.9rem; " + name_style2 + "'>" + c2 + "</span></div>"
                    html += "<div><span style='font-size:0.65rem; color:#888;'>" + d2 + "</span></div>"
                    html += "</div>"
                    
                    html += "</div>" # Fin tarjeta
                
                html += "</div>" # Fin columna
            
            html += "</div></div>" # Fin contenedor
            
            # Renderizado final
            st.markdown(html, unsafe_allow_html=True)
            
            # Leyenda
            st.markdown("""
            <div style="display:flex; gap:20px; justify-content:center; margin:20px 0; padding:15px; background:rgba(0,0,0,0.2); border-radius:8px; flex-wrap: wrap;">
                <span><span style="color:#ff2b2b;">█</span> Aka (Rojo)</span>
                <span><span style="color:#1e90ff;">█</span> Ao (Azul)</span>
                <span style="color:#ffd700;">🏆 Ganador</span>
                <span style="color:gold;">⭐ BYE</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📌 No hay brackets generados.")

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
                st.download_button("📥 DESCARGAR CSV", csv, "inscripciones.csv")
        
        with tabs[1]:
            df_b = leer_brackets()
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                
                with st.expander("Gestionar Resultados"):
                    with st.form("edit_brackets"):
                        categorias_b = df_b['Categoria'].unique()
                        cat_b = st.selectbox("Categoría", categorias_b)
                        
                        df_cat_b = df_b[df_b['Categoria'] == cat_b]
                        partido_id = st.selectbox("ID Partido", df_cat_b['Partido_ID'].unique())
                        
                        df_partido = df_cat_b[df_cat_b['Partido_ID'] == partido_id].iloc[0]
                        
                        c1 = df_partido['Competidor1']
                        c2 = df_partido['Competidor2']
                        
                        if c1 and c2 and c1 != "BYE" and c2 != "BYE":
                            ganador = st.radio("Seleccionar Ganador", [c1, c2], index=None)
                            
                            if st.form_submit_button("GUARDAR RESULTADO"):
                                if ganador:
                                    df_b.loc[(df_b['Categoria'] == cat_b) & (df_b['Partido_ID'] == partido_id), 'Ganador'] = ganador
                                    guardar_brackets(df_b)
                                    st.success(f"✅ Ganador actualizado: {ganador}")
                                    st.rerun()
                                else:
                                    st.error("Selecciona un ganador")
                        else:
                            st.info("Este partido no requiere gestión manual (BYE o Vacío).")
                
                if st.button("⚠️ BORRAR Y REGENERAR TODO"):
                    df_vacio = pd.DataFrame(columns=df_b.columns)
                    guardar_brackets(df_vacio)
                    st.warning("Brackets reiniciados. Ve a la pestaña Brackets para generar nuevos.")
                    st.rerun()
        
        with tabs[2]:
            df_stats = leer_inscripciones()
            if not df_stats.empty:
                df_conf = df_stats[df_stats['Estado'] == 'CONFIRMADO']
                col1, col2, col3 = st.columns(3)
                total = len(df_conf[df_conf['Metodo'] != 'VIP']) * PRECIO
                col1.metric("Ingresos Estimados", formatear_peso(total))
                col2.metric("Inscritos VIP", len(df_stats[df_stats['Metodo'] == 'VIP']))
                col3.metric("Pendientes Pago", len(df_stats[df_stats['Metodo'] == 'Pendiente']))
        
        st.markdown('</div>', unsafe_allow_html=True)
    elif password:
        st.error("❌ Contraseña incorrecta")

# === FOOTER ===
st.markdown("""
<div style="text-align:center; color:#666; padding:30px 0; border-top:1px solid #333;">
    <p>© 2024 World Kyokushin Budokai Chile</p>
</div>
""", unsafe_allow_html=True)
