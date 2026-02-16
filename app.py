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

# === CONFIGURACION DE PAGINA ===
st.set_page_config(page_title="WKB WORLD CUP 2026", page_icon="🥋", layout="wide")

# === CONSTANTES ===
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
CATEGORIAS = ["KUMITE -65kg", "KUMITE -70kg", "KUMITE -75kg", "KUMITE -80kg", "KUMITE +80kg"]

# === ESTILOS CSS (SIN COMILLAS TRIPLES) ===
css = "<style>"
css += "@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap');"
css += ".stApp { background: radial-gradient(circle at 50% 0%, #1a0505 0%, #000000 100%); font-family: 'Rajdhani', sans-serif; }"
css += "h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: white !important; }"
css += "::-webkit-scrollbar { height: 12px; }"
css += "::-webkit-scrollbar-track { background: #0a0c10; }"
css += "::-webkit-scrollbar-thumb { background: #ff2b2b; border-radius: 6px; }"
css += ".stButton>button { width: 100%; background: linear-gradient(90deg, #8b0000, #ff2b2b); border: none; color: white; }"
css += "</style>"
st.markdown(css, unsafe_allow_html=True)

# === FUNCIONES DE DATOS ===
@st.cache_data(ttl=5)
def leer_datos(hoja):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=hoja, ttl=0)
        # Limpieza critica para evitar 'nan'
        df = df.fillna("")
        return df
    except:
        cols = ["ID", "Nombre", "Dojo", "Categoria", "Estado"]
        if hoja == "Brackets":
            cols = ["Categoria", "Ronda", "Partido_ID", "Competidor1", "Competidor2", "Ganador", "Posicion", "Total_Rondas"]
        return pd.DataFrame(columns=cols)

def guardar_datos(hoja, df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet=hoja, data=df)
        return True
    except: return False

# === LOGICA DE BRACKETS ===
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
        
        lista = inscritos + [None]*(capacidad - n)
        
        # Ronda 1
        for i in range(0, len(lista), 2):
            c1, c2 = lista[i], lista[i+1]
            # Logica para evitar nan en nombres
            n1 = c1['Nombre'] if c1 and pd.notna(c1['Nombre']) else "BYE"
            n2 = c2['Nombre'] if c2 and pd.notna(c2['Nombre']) else "BYE"
            
            p = {
                "Categoria": cat, "Ronda": 1, "Partido_ID": pid,
                "Competidor1": n1,
                "Competidor2": n2,
                "Ganador": n2 if n1 == "BYE" else (n1 if n2 == "BYE" else ""),
                "Posicion": i//2, "Total_Rondas": rondas
            }
            todos_partidos.append(p)
            pid += 1
            
        # Rondas siguientes
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

# === PESTAÑA 3: VISUALIZACION HORIZONTAL ===
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
            
            # --- CONSTRUCCION DE HTML SIN COMILLAS TRIPLES ---
            
            # Contenedor principal (Scroll horizontal y Flex Row)
            html = "<div style='width:100%; overflow-x:auto; padding-bottom:20px;'>"
            html += "<div style='display:flex; flex-direction:row; min-width:max-content; padding:20px; gap:50px;'>"
            
            rondas_unicas = sorted(df_cat['Ronda'].unique())
            
            for r in rondas_unicas:
                matches = df_cat[df_cat['Ronda'] == r].sort_values('Posicion')
                
                titulo = "🏆 FINAL" if r == total_rondas else "RONDA " + str(r)
                
                # Columna de la ronda (Flex Column)
                html += "<div style='display:flex; flex-direction:column; justify-content:space-around; width:280px; position:relative;'>"
                
                # Titulo de ronda
                html += "<div style='text-align:center; color:#ff2b2b; font-weight:bold; border-bottom:2px solid #ff2b2b; margin-bottom:20px; font-family:Orbitron;'>" + titulo + "</div>"
                
                for _, m in matches.iterrows():
                    # Preparar datos
                    id_partido = str(int(float(m['Partido_ID']))) if m['Partido_ID'] != "" else "0"
                    nom1 = str(m['Competidor1'])
                    nom2 = str(m['Competidor2'])
                    ganador = str(m['Ganador'])
                    
                    if nom1 == "nan" or nom1 == "": nom1 = "---"
                    if nom2 == "nan" or nom2 == "": nom2 = "---"
                    
                    # Estilos condicionales
                    es_ganador1 = (ganador == nom1 and ganador != "" and ganador != "---")
                    es_ganador2 = (ganador == nom2 and ganador != "" and ganador != "---")
                    
                    style_win1 = "color:#ffd700; font-weight:bold;" if es_ganador1 else "color:white;"
                    style_win2 = "color:#ffd700; font-weight:bold;" if es_ganador2 else "color:white;"
                    
                    bg_col1 = "background:rgba(255,215,0,0.15);" if es_ganador1 else ""
                    bg_col2 = "background:rgba(255,215,0,0.15);" if es_ganador2 else ""
                    
                    # Linea conectora
                    linea = ""
                    if r < total_rondas:
                        linea = "<div style='position:absolute; top:50%; right:-50px; width:50px; height:2px; background:#555;'></div>"

                    # Tarjeta (Match Card)
                    html += "<div style='background:#14161e; border:1px solid #444; border-radius:6px; margin:10px 0; position:relative; box-shadow:0 4px 10px rgba(0,0,0,0.5);'>"
                    
                    # ID Badge
                    html += "<div style='position:absolute; top:-10px; right:5px; background:black; color:#666; font-size:10px; padding:0 4px; border:1px solid #333;'>#" + id_partido + "</div>"
                    
                    # Competidor 1 (Aka/Rojo)
                    html += "<div style='padding:8px; border-bottom:1px solid #333; border-left:4px solid #ff2b2b; " + bg_col1 + "'>"
                    html += "<div style='" + style_win1 + " font-size:14px;'>" + nom1 + "</div>"
                    html += "</div>"
                    
                    # Competidor 2 (Ao/Azul)
                    html += "<div style='padding:8px; border-left:4px solid #1e90ff; " + bg_col2 + "'>"
                    html += "<div style='" + style_win2 + " font-size:14px;'>" + nom2 + "</div>"
                    html += "</div>"
                    
                    # Insertar linea y cerrar tarjeta
                    html += linea
                    html += "</div>" 
                
                html += "</div>" # Cerrar Columna Ronda
            
            html += "</div></div>" # Cerrar Contenedor Principal
            
            # RENDERIZAR TODO EL HTML JUNTO
            st.markdown(html, unsafe_allow_html=True)

with tab3:
    st.write("Panel Admin (Protegido)")
    if st.checkbox("Simular Login"):
        df_edit = st.data_editor(leer_datos("Brackets"))
        if st.button("Guardar Cambios"):
            guardar_datos("Brackets", df_edit)
            st.rerun()
