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

# === CONFIGURACIÓN ===
st.set_page_config(page_title="WKB WORLD CUP 2026", page_icon="🥋", layout="wide")
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
CATEGORIAS = ["KUMITE -65kg", "KUMITE -70kg", "KUMITE -75kg", "KUMITE -80kg", "KUMITE +80kg"]

# === ESTILOS CSS (GLOBAL) ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap');
    .stApp { background: radial-gradient(circle at 50% 0%, #1a0505 0%, #000000 100%); font-family: 'Rajdhani', sans-serif; }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: white !important; }
    
    /* SCROLLBAR */
    ::-webkit-scrollbar { height: 12px; }
    ::-webkit-scrollbar-track { background: #0a0c10; }
    ::-webkit-scrollbar-thumb { background: #ff2b2b; border-radius: 6px; }
    
    .stButton>button { width: 100%; background: linear-gradient(90deg, #8b0000, #ff2b2b); border: none; color: white; }
</style>
""", unsafe_allow_html=True)

# === FUNCIONES DE DATOS ===
@st.cache_data(ttl=5)
def leer_datos(hoja):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        return conn.read(worksheet=hoja, ttl=0)
    except:
        cols = ["ID", "Nombre", "Dojo", "Categoria", "Estado"] if hoja == "Inscripciones" else \
               ["Categoria", "Ronda", "Partido_ID", "Competidor1", "Competidor2", "Ganador", "Posicion", "Total_Rondas"]
        return pd.DataFrame(columns=cols)

def guardar_datos(hoja, df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=hoja, data=df)
        return True
    except: return False

# === LÓGICA DE BRACKETS ===
def generar_brackets():
    df = leer_datos("Inscripciones")
    if df.empty: return False, "Sin datos"
    
    df_conf = df[df['Estado'] == 'CONFIRMADO']
    todos_partidos = []
    pid = 1
    
    for cat in CATEGORIAS:
        inscritos = df_conf[df_conf['Categoria'] == cat].to_dict('records')
        n = len(inscritos)
        if n < 2: continue
        
        random.shuffle(inscritos)
        rondas = math.ceil(math.log2(n))
        capacidad = 2**rondas
        
        # Rellenar con BYEs
        lista = inscritos + [None]*(capacidad - n)
        
        # Ronda 1
        for i in range(0, len(lista), 2):
            c1, c2 = lista[i], lista[i+1]
            p = {
                "Categoria": cat, "Ronda": 1, "Partido_ID": pid,
                "Competidor1": c1['Nombre'] if c1 else "BYE",
                "Competidor2": c2['Nombre'] if c2 else "BYE",
                "Ganador": c2['Nombre'] if not c1 else (c1['Nombre'] if not c2 else ""),
                "Posicion": i//2, "Total_Rondas": rondas
            }
            todos_partidos.append(p)
            pid += 1
            
        # Rondas siguientes (vacías)
        matches = capacidad // 2
        for r in range(2, rondas + 1):
            matches //= 2
            for j in range(matches):
                todos_partidos.append({
                    "Categoria": cat, "Ronda": r, "Partido_ID": pid,
                    "Competidor1": "", "Competidor2": "", "Ganador": "",
                    "Posicion": j, "Total_Rondas": rondas
                })
                pid += 1
                
    if todos_partidos:
        guardar_datos("Brackets", pd.DataFrame(todos_partidos))
        return True, "Generado"
    return False, "Error"

# === INTERFAZ ===
col1, col2 = st.columns([1,3])
with col1: st.image(LOGO_URL, width=100)
with col2: st.title("WORLD CUP 2026")

tab1, tab2, tab3 = st.tabs(["📝 INSCRIPCIÓN", "🏆 BRACKETS", "⚙️ ADMIN"])

with tab1:
    with st.form("reg"):
        nombre = st.text_input("Nombre")
        cat = st.selectbox("Categoría", CATEGORIAS)
        if st.form_submit_button("Inscribir"):
            datos = pd.DataFrame([{"ID": str(time.time()), "Nombre": nombre, "Categoria": cat, "Estado": "CONFIRMADO"}])
            df_old = leer_datos("Inscripciones")
            guardar_datos("Inscripciones", pd.concat([df_old, datos], ignore_index=True))
            st.success("Listo")

# === AQUÍ ESTÁ LA MAGIA HORIZONTAL ===
with tab2:
    if st.button("🔄 Generar Llaves"):
        ok, msg = generar_brackets()
        if ok: st.success(msg); time.sleep(1); st.rerun()

    df_b = leer_datos("Brackets")
    if not df_b.empty:
        cat_sel = st.selectbox("Ver Categoría", df_b['Categoria'].unique())
        df_cat = df_b[df_b['Categoria'] == cat_sel]
        
        if not df_cat.empty:
            total_rondas = int(df_cat['Total_Rondas'].iloc[0])
            
            # 1. INICIO DEL HTML GIGANTE (Flex Row Force)
            html = f"""
            <div style="width:100%; overflow-x:auto; padding-bottom:20px;">
                <div style="display:flex; flex-direction:row; min-width:max-content; padding:20px; gap:50px;">
            """
            
            # 2. COLUMNAS POR RONDA
            for r in sorted(df_cat['Ronda'].unique()):
                matches = df_cat[df_cat['Ronda'] == r].sort_values('Posicion')
                titulo = "🏆 FINAL" if r == total_rondas else f"RONDA {r}"
                
                # Columna flexible vertical
                html += f"""
                <div style="display:flex; flex-direction:column; justify-content:space-around; width:260px; position:relative;">
                    <div style="text-align:center; color:#ff2b2b; font-weight:bold; border-bottom:2px solid #ff2b2b; margin-bottom:20px;">{titulo}</div>
                """
                
                # 3. TARJETAS DE PARTIDO
                for _, m in matches.iterrows():
                    # Estilos dinámicos
                    win1 = "color:#ffd700; font-weight:bold;" if m['Ganador'] == m['Competidor1'] and m['Ganador'] else "color:white;"
                    win2 = "color:#ffd700; font-weight:bold;" if m['Ganador'] == m['Competidor2'] and m['Ganador'] else "color:white;"
                    bg1 = "background:rgba(255,215,0,0.1);" if m['Ganador'] == m['Competidor1'] and m['Ganador'] else ""
                    bg2 = "background:rgba(255,215,0,0.1);" if m['Ganador'] == m['Competidor2'] and m['Ganador'] else ""
                    
                    # Línea conectora (si no es final)
                    linea = ""
                    if r < total_rondas:
                        linea = '<div style="position:absolute; top:50%; right:-50px; width:50px; height:2px; background:#555;"></div>'

                    html += f"""
                    <div style="background:#14161e; border:1px solid #444; border-radius:6px; margin:10px 0; position:relative; box-shadow:0 4px 10px black;">
                        <div style="position:absolute; top:-10px; right:5px; background:black; color:#666; font-size:10px; padding:0 4px; border:1px solid #333;">#{m['Partido_ID']}</div>
                        
                        <div style="padding:8px; border-bottom:1px solid #333; border-left:4px solid #ff2b2b; {bg1}">
                            <div style="{win1} font-size:14px;">{m['Competidor1'] or '---'}</div>
                        </div>
                        
                        <div style="padding:8px; border-left:4px solid #1e90ff; {bg2}">
                            <div style="{win2} font-size:14px;">{m['Competidor2'] or '---'}</div>
                        </div>
                        
                        {linea}
                    </div>
                    """
                html += "</div>" # Cierra columna
            
            html += "</div></div>" # Cierra contenedor principal
            
            # 4. RENDERIZAR TODO DE UNA VEZ
            st.markdown(html, unsafe_allow_html=True)

with tab3:
    st.write("Panel Admin (Protegido)")
    if st.checkbox("Simular Login"):
        df_edit = st.data_editor(leer_datos("Brackets"))
        if st.button("Guardar Cambios"):
            guardar_datos("Brackets", df_edit)
            st.rerun()
