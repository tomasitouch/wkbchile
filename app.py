import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import hashlib
import datetime
from datetime import timedelta
import base64
from PIL import Image
import io
import numpy as np
import random
import string
import uuid
import mercadopago
import logging
import re
import json
import math

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Official Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

# Meta tags para móvil
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    /* Ocultar elementos nativos intrusivos */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. LOGGING Y SISTEMA ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_event(event_type, details):
    logger.info(f"{event_type}: {details}")

# --- 3. CONEXIÓN A GOOGLE SHEETS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
SHEET_NAMES = {
    "brackets": "Brackets",
    "inscriptions": "Inscripciones",
    "config": "Configuracion",
    "payments": "Pagos",
    "backup": "Backup"
}

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# --- 4. FUNCIONES DE CARGA Y GUARDADO ---
@st.cache_data(ttl=10)
def load_data(worksheet):
    try:
        conn = get_connection()
        return conn.read(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[worksheet])
    except Exception as e:
        log_event(f"ERROR_LOAD_{worksheet.upper()}", str(e))
        return pd.DataFrame()

def save_data(df, worksheet):
    try:
        conn = get_connection()
        conn.update(spreadsheet=SHEET_URL, worksheet=SHEET_NAMES[worksheet], data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        log_event(f"ERROR_SAVE_{worksheet.upper()}", str(e))
        st.error(f"Error guardando datos: {e}")
        return False

# --- 5. LÓGICA DE NEGOCIO Y MODELOS ---
ALL_CATEGORIES = [
    f"{g} | {s}" for g, s in {
        "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
        "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
        "KATA": ["All Categories"]
    }.items() for s in s
]

def init_mercadopago():
    try:
        return mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
    except: return None

# --- 6. ESTILOS CSS PROFESIONALES ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #0e1117; font-family: 'Inter', sans-serif; }
    
    /* Header */
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        padding: 20px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%);
        border-bottom: 1px solid #374151; margin-bottom: 25px; flex-wrap: wrap; gap: 15px;
    }
    
    /* Brackets Profesionales */
    .bracket-wrapper {
        display: flex; flex-direction: row; padding: 40px 20px;
        overflow-x: auto; gap: 0; min-height: 600px;
        align-items: flex-start; /* Alineación superior clave */
    }
    
    .bracket-round {
        display: flex; flex-direction: column; justify-content: space-around;
        width: 280px; flex-shrink: 0; padding: 0 20px; min-height: 600px;
    }
    
    .bracket-match {
        display: flex; flex-direction: column; position: relative;
        margin: 15px 0; padding: 10px 0;
    }
    
    /* Conectores */
    .bracket-match::before {
        content: ""; position: absolute; right: -25px; top: 50%;
        width: 25px; height: 2px; background: #4B5563; z-index: 1;
    }
    
    .bracket-match:nth-child(odd)::after {
        content: ""; position: absolute; right: -25px; top: 50%;
        width: 2px; height: 100%; background: #4B5563; z-index: 1;
        transform: translateY(50%); /* Conecta hacia abajo */
    }
    
    .bracket-match:nth-child(even)::after {
        content: ""; position: absolute; right: -25px; bottom: 50%;
        width: 2px; height: 100%; background: #4B5563; z-index: 1;
        transform: translateY(50%); /* Conecta hacia arriba */
    }
    
    .bracket-round:last-child .bracket-match::before,
    .bracket-round:last-child .bracket-match::after { display: none; }
    
    /* Tarjeta de Jugador */
    .bracket-player {
        background: #1f2937; border: 1px solid #374151;
        padding: 10px 15px; width: 240px; position: relative; z-index: 2;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    .bracket-player.top { border-radius: 8px 8px 0 0; border-bottom: none; }
    .bracket-player.bottom { border-radius: 0 0 8px 8px; margin-top: -1px; }
    
    .bracket-player.winner {
        border-color: #FDB931; background: rgba(253, 185, 49, 0.1);
        color: #FDB931; font-weight: bold;
    }
    
    .player-info { display: flex; flex-direction: column; }
    .player-name { font-weight: bold; font-size: 14px; }
    .player-dojo { font-size: 11px; color: #9ca3af; }
    .vote-count { font-size: 12px; font-weight: bold; color: #FDB931; }
    
    /* Botones y UI */
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; }
    .round-header {
        text-align: center; color: #FDB931; font-weight: bold;
        text-transform: uppercase; margin-bottom: 20px; letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- 7. FUNCIONES DE BRACKETS Y TORNEO ---
def generate_dynamic_brackets(category):
    """Genera brackets dinámicos basados en inscritos"""
    try:
        inscriptions = load_data("inscriptions")
        brackets = load_data("brackets")
        
        # Filtrar confirmados
        participants = inscriptions[
            (inscriptions['Categoria'] == category) & 
            (inscriptions['Estado_Pago'] == 'Confirmado')
        ].to_dict('records')
        
        n = len(participants)
        if n < 2: return False
        
        # Calcular slots (potencia de 2)
        slots = 2**math.ceil(math.log2(n))
        random.shuffle(participants)
        
        # Añadir BYEs
        bracket_participants = participants + [{"Nombre_Completo": "BYE", "ID": "BYE", "Dojo": ""}] * (slots - n)
        
        # Limpiar brackets previos
        brackets = brackets[brackets['Category'] != category]
        new_matches = []
        
        # Estructura de rondas
        rounds = int(math.log2(slots))
        round_names = ["Ronda 1", "Ronda 2", "Cuartos", "Semifinal", "Final"]
        
        # Generar R1 con jugadores
        for i in range(slots // 2):
            p1 = bracket_participants[i*2]
            p2 = bracket_participants[i*2+1]
            
            match = {
                "Category": category, "Match_ID": f"R1-M{i+1}", "Round": round_names[0] if rounds > 1 else "Final",
                "Match_Number": i+1, "P1_Name": p1['Nombre_Completo'], "P1_ID": p1['ID'], "P1_Dojo": p1['Dojo'], "P1_Votes": 0,
                "P2_Name": p2['Nombre_Completo'], "P2_ID": p2['ID'], "P2_Dojo": p2['Dojo'], "P2_Votes": 0,
                "Winner": "", "Winner_ID": "", "Status": "Live"
            }
            
            # Lógica automática de BYE
            if p2['ID'] == 'BYE':
                match.update({"Winner": p1['Nombre_Completo'], "Winner_ID": p1['ID'], "Status": "Completed", "P2_Name": "BYE"})
            
            # Calcular siguiente match
            if rounds > 1:
                match["Next_Match"] = f"R2-M{(i//2)+1}"
                match["Next_Pos"] = "top" if i % 2 == 0 else "bottom"
            else:
                match["Next_Match"] = "CHAMPION"
                
            new_matches.append(match)
            
        # Generar rondas vacías subsiguientes
        matches_in_round = slots // 2
        for r in range(2, rounds + 1):
            matches_in_round //= 2
            r_name = "Final" if r == rounds else f"Ronda {r}"
            
            for m in range(1, matches_in_round + 1):
                new_matches.append({
                    "Category": category, "Match_ID": f"R{r}-M{m}", "Round": r_name,
                    "Match_Number": m, "P1_Name": "", "P1_ID": "", "P1_Votes": 0, "P2_Name": "", "P2_ID": "", "P2_Votes": 0,
                    "Winner": "", "Winner_ID": "", "Status": "Pending",
                    "Next_Match": f"R{r+1}-M{(m+1)//2}" if r < rounds else "CHAMPION",
                    "Next_Pos": "top" if m % 2 != 0 else "bottom"
                })
        
        # Guardar
        full_df = pd.concat([brackets, pd.DataFrame(new_matches)], ignore_index=True)
        
        # Propagar BYEs iniciales
        # (Aquí iría una función recursiva para mover ganadores de BYE a R2, simplificado por ahora)
        
        save_data(full_df, "brackets")
        return True
    except Exception as e:
        log_event("ERROR_GEN_BRACKETS", str(e))
        return False

def render_brackets_view():
    """Visualización Horizontal de Brackets"""
    cat = st.session_state.get('cat', ALL_CATEGORIES[0])
    st.markdown(f"### 🏆 {cat}")
    
    df = load_data("brackets")
    cat_df = df[df['Category'] == cat]
    
    if cat_df.empty:
        st.info("Brackets no generados aún.")
        return

    # Obtener rondas únicas ordenadas
    rounds = cat_df['Round'].unique().tolist()
    # Orden personalizado simple: R1 -> R2 -> ... -> Final
    rounds.sort(key=lambda x: (len(x), x)) 
    
    html = '<div class="bracket-wrapper">'
    
    for r in rounds:
        matches = cat_df[cat_df['Round'] == r].sort_values('Match_Number')
        html += f'<div class="bracket-round"><div class="round-header">{r}</div>'
        
        for _, m in matches.iterrows():
            # Clases de ganador
            w1 = "winner" if str(m['Winner_ID']) == str(m['P1_ID']) and m['P1_ID'] else ""
            w2 = "winner" if str(m['Winner_ID']) == str(m['P2_ID']) and m['P2_ID'] else ""
            
            p1_n = m['P1_Name'] if m['P1_Name'] else "TBD"
            p2_n = m['P2_Name'] if m['P2_Name'] else "TBD"
            
            html += f"""
            <div class="bracket-match">
                <div class="bracket-player top {w1}">
                    <div class="player-info">
                        <span class="player-name">{p1_n}</span>
                        <span class="player-dojo">{m['P1_Dojo'] if not pd.isna(m['P1_Dojo']) else ''}</span>
                    </div>
                    <span class="vote-count">{int(m['P1_Votes']) if m['P1_Votes'] else 0}</span>
                </div>
                <div class="bracket-player bottom {w2}">
                    <div class="player-info">
                        <span class="player-name">{p2_n}</span>
                        <span class="player-dojo">{m['P2_Dojo'] if not pd.isna(m['P2_Dojo']) else ''}</span>
                    </div>
                    <span class="vote-count">{int(m['P2_Votes']) if m['P2_Votes'] else 0}</span>
                </div>
            </div>
            """
        html += '</div>'
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Sistema de Votación (Solo Matches Activos)
    st.markdown("### 🗳️ Votación en Vivo")
    live_matches = cat_df[cat_df['Status'] == 'Live']
    
    if live_matches.empty:
        st.info("No hay combates activos para votar en este momento.")
    else:
        for _, match in live_matches.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([1, 0.5, 1])
                with col1:
                    if st.button(f"👍 {match['P1_Name']}", key=f"v1_{match['Match_ID']}", use_container_width=True):
                        register_vote(match['Match_ID'], match['P1_ID'])
                with col2:
                    st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:20px;'>VS</div>", unsafe_allow_html=True)
                with col3:
                    if st.button(f"👍 {match['P2_Name']}", key=f"v2_{match['Match_ID']}", use_container_width=True):
                        register_vote(match['Match_ID'], match['P2_ID'])

def register_vote(match_id, player_id):
    """Registra voto y avanza ronda si corresponde"""
    df = load_data("brackets")
    mask = (df['Match_ID'] == match_id)
    
    if not df[mask].empty:
        # Incrementar voto
        col = 'P1_Votes' if df.loc[mask, 'P1_ID'].values[0] == player_id else 'P2_Votes'
        df.loc[mask, col] = df.loc[mask, col].fillna(0) + 1
        
        # Verificar ganador (Ejemplo: al llegar a 10 votos o manual)
        # Aquí podrías añadir lógica: "Si votos > X, avanza"
        
        save_data(df, "brackets")
        st.success("✅ Voto registrado")
        st.rerun()

# --- 8. VISTAS PRINCIPALES ---
def render_header():
    st.markdown("""
    <div class="header-container">
        <div style="display:flex; align-items:center;">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-PCwsXVnqhlX-vNev8BDqbszitBpm3cC8GQ&s" style="height:50px; margin-right:15px;">
            <div>
                <h1 style="margin:0; font-size:24px; color:white;">WKB CHILE</h1>
                <p style="margin:0; color:#FDB931; font-size:12px;">OFFICIAL TOURNAMENT HUB</p>
            </div>
        </div>
        <div>
            <img src="https://inertiax.store/cdn/shop/files/wmremove-transformed-removebg-preview.png?v=1743950875&width=500" style="height:40px;">
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_home():
    render_header()
    
    tabs = st.tabs(["🏆 COMPETENCIA", "📝 INSCRIPCIÓN", "⚙️ ADMIN"])
    
    with tabs[0]:
        st.markdown("### Selecciona una Categoría para ver los Brackets")
        cols = st.columns(3)
        for i, cat in enumerate(ALL_CATEGORIES):
            with cols[i % 3]:
                if st.button(cat.split(" | ")[-1], key=cat, use_container_width=True):
                    st.session_state.view = "BRACKET"
                    st.session_state.cat = cat
                    st.rerun()

    with tabs[1]:
        render_inscription_form()
        
    with tabs[2]:
        render_admin_panel()

def render_inscription_form():
    st.markdown("### 📝 Nueva Inscripción")
    with st.form("inscription"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre Completo")
            age = st.number_input("Edad", 18, 99)
        with col2:
            dojo = st.text_input("Dojo")
            cat = st.selectbox("Categoría", ALL_CATEGORIES)
        
        if st.form_submit_button("Ir al Pago", use_container_width=True):
            if name and dojo:
                st.session_state.temp_user = {"Nombre_Completo": name, "Categoria": cat, "Dojo": dojo, "ID": str(uuid.uuid4())[:8]}
                st.session_state.view = "PAYMENT"
                st.rerun()
            else:
                st.error("Faltan datos")

def render_payment():
    render_header()
    st.markdown("### 💳 Confirmación de Pago")
    
    user = st.session_state.get('temp_user', {})
    st.info(f"Vas a inscribir a **{user.get('Nombre_Completo')}** en **{user.get('Categoria')}**")
    
    # Botón simulado para desarrollo
    if st.button("✅ Confirmar Pago (Simulación)", type="primary", use_container_width=True):
        df = load_data("inscriptions")
        new_row = pd.DataFrame([user | {
            "Estado_Pago": "Confirmado", 
            "Fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Codigo_Pago": str(uuid.uuid4())[:6]
        }])
        save_data(pd.concat([df, new_row]), "inscriptions")
        st.balloons()
        st.success("¡Inscripción Exitosa!")
        time.sleep(2)
        st.session_state.view = "HOME"
        st.rerun()
        
    if st.button("Cancelar"):
        st.session_state.view = "HOME"
        st.rerun()

def render_admin_panel():
    st.write("Panel de Administración")
    password = st.text_input("Contraseña", type="password")
    if password == "wkbadmin123": # En producción usar hash
        if st.button("Generar Brackets para Todas las Categorías"):
            with st.status("Generando..."):
                for c in ALL_CATEGORIES:
                    generate_dynamic_brackets(c)
            st.success("Brackets listos!")
        
        if st.button("Resetear Base de Datos (Peligro)"):
            # Lógica de reset aquí
            pass

# --- 9. EJECUCIÓN ---
def main():
    if 'view' not in st.session_state: st.session_state.view = "HOME"
    
    if st.session_state.view == "HOME": render_home()
    elif st.session_state.view == "BRACKET": 
        render_header()
        if st.button("⬅ Volver"): 
            st.session_state.view = "HOME"
            st.rerun()
        render_brackets_view()
    elif st.session_state.view == "PAYMENT": render_payment()

if __name__ == "__main__":
    main()
