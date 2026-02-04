import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import hashlib
import datetime
from PIL import Image
import io
import base64
import random
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="WKB Tournament Manager", layout="wide", page_icon="🥋")

# URL de tu Sheet (Asegúrate de que sea pública para "Cualquiera con el enlace puede editar" o configurar credenciales)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit#gid=0"
ADMIN_PASS_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9" # Password: admin (por defecto)

# --- 2. LÓGICA DE DATOS ---
CATEGORIES = [
    "KUMITE - MEN | -70kg", "KUMITE - MEN | +70kg",
    "KUMITE - WOMEN | -60kg", "KUMITE - WOMEN | +60kg",
    "KATA | Open"
]

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASS_HASH

@st.cache_resource
def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    conn = get_conn()
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet, ttl=5)

def save_data(df, worksheet):
    conn = get_conn()
    conn.update(spreadsheet=SHEET_URL, worksheet=worksheet, data=df)
    st.cache_data.clear()

# Inicialización de Brackets vacíos
def get_empty_brackets():
    data = []
    matches = ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']
    for cat in CATEGORIES:
        for m in matches:
            data.append({
                "Category": cat, "Match_ID": m,
                "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0,
                "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0,
                "Winner": "", "Live": False
            })
    return pd.DataFrame(data)

# --- 3. ESTILOS ---
st.markdown("""
<style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .bracket-card { background: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #FDB931; margin-bottom: 10px; }
    .winner-text { color: #FDB931; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. ESTADO DE SESIÓN ---
if 'admin_auth' not in st.session_state: st.session_state.admin_auth = False
if 'view' not in st.session_state: st.session_state.view = "Public"

# --- 5. LÓGICA DE CIERRE Y LLAVES ---
def generate_random_brackets(category):
    inscripciones = load_data("Inscripciones")
    # Filtrar atletas de esta categoría que no estén eliminados
    atletas = inscripciones[(inscripciones['Categoria'] == category) & (inscripciones['Estado'] != 'Eliminado')]
    
    lista_atletas = atletas.to_dict('records')
    random.shuffle(lista_atletas)
    
    brackets = load_data("Hoja1")
    
    # Lógica de emparejamiento para Cuartos (Q1-Q4)
    for i in range(4):
        match_id = f'Q{i+1}'
        idx = brackets[(brackets['Category'] == category) & (brackets['Match_ID'] == match_id)].index[0]
        
        # Atleta 1
        if len(lista_atletas) > 0:
            a1 = lista_atletas.pop(0)
            brackets.at[idx, 'P1_Name'] = a1['Nombre_Completo']
            brackets.at[idx, 'P1_Dojo'] = a1['Dojo']
        
        # Atleta 2
        if len(lista_atletas) > 0:
            a2 = lista_atletas.pop(0)
            brackets.at[idx, 'P2_Name'] = a2['Nombre_Completo']
            brackets.at[idx, 'P2_Dojo'] = a2['Dojo']
        else:
            # Si no hay oponente, pasa directo (Winner es Atleta 1)
            if brackets.at[idx, 'P1_Name'] != "":
                brackets.at[idx, 'Winner'] = brackets.at[idx, 'P1_Name']
                # Mover a la siguiente ronda (S1 o S2)
                target_s = 'S1' if i < 2 else 'S2'
                target_p = 'P1' if i % 2 == 0 else 'P2'
                s_idx = brackets[(brackets['Category'] == category) & (brackets['Match_ID'] == target_s)].index[0]
                brackets.at[s_idx, f'{target_p}_Name'] = brackets.at[idx, 'P1_Name']
                brackets.at[s_idx, f'{target_p}_Dojo'] = brackets.at[idx, 'P1_Dojo']

    save_data(brackets, "Hoja1")
    st.success(f"¡Llaves generadas para {category}!")

# --- 6. INTERFAZ ---
st.title("🥋 WKB Official Hub")

# Sidebar Admin
with st.sidebar:
    st.header("Administración")
    if not st.session_state.admin_auth:
        pwd = st.text_input("Password Admin", type="password")
        if st.button("Login"):
            if check_admin(pwd):
                st.session_state.admin_auth = True
                st.rerun()
    else:
        st.success("Sesión Iniciada")
        if st.button("Cerrar Sesión"):
            st.session_state.admin_auth = False
            st.rerun()
        
        st.markdown("---")
        if st.button("🚨 RESET TOTAL", type="primary"):
            save_data(get_empty_brackets(), "Hoja1")
            # Crear dataframe vacío con columnas correctas para Inscripciones
            empty_insc = pd.DataFrame(columns=["ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", "Grado_Valor", "Dojo", "Organizacion", "Telefono", "Email", "Categoria", "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64", "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID", "Estado"])
            save_data(empty_insc, "Inscripciones")
            st.warning("Sistema reseteado a cero.")
            time.sleep(1)
            st.rerun()

# Tabs principales
tab_insc, tab_bracket = st.tabs(["📝 Inscripciones", "🏆 Brackets / Votación"])

with tab_insc:
    st.header("Etapa 1: Registro de Atletas")
    with st.form("form_registro"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre Completo")
        dojo = col2.text_input("Dojo")
        cat = st.selectbox("Categoría", CATEGORIES)
        email = col1.text_input("Email")
        telefono = col2.text_input("WhatsApp")
        
        submitted = st.form_submit_button("Registrar Inscripción")
        if submitted:
            if nombre and dojo:
                df_insc = load_data("Inscripciones")
                new_data = pd.DataFrame([{
                    "ID": str(random.randint(1000, 9999)),
                    "Nombre_Completo": nombre,
                    "Dojo": dojo,
                    "Categoria": cat,
                    "Email": email,
                    "Telefono": telefono,
                    "Estado": "Activo",
                    "Fecha_Inscripcion": str(datetime.datetime.now())
                }])
                df_insc = pd.concat([df_insc, new_data], ignore_index=True)
                save_data(df_insc, "Inscripciones")
                st.success(f"¡{nombre} inscrito correctamente!")
            else:
                st.error("Faltan campos obligatorios")

with tab_bracket:
    sel_cat = st.selectbox("Seleccionar Categoría para ver", CATEGORIES)
    
    # Controles de Admin para la categoría
    if st.session_state.admin_auth:
        col_adm1, col_adm2 = st.columns(2)
        if col_adm1.button(f"🔒 Cerrar Inscripciones y Generar Llaves {sel_cat}"):
            generate_random_brackets(sel_cat)
            
    # Mostrar Brackets
    df_b = load_data("Hoja1")
    cat_matches = df_b[df_b['Category'] == sel_cat]
    
    st.subheader(f"Cuadro de Competición - {sel_cat}")
    
    for _, match in cat_matches.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="bracket-card">
                <b>Match {match['Match_ID']}</b><br>
                🔴 {match['P1_Name']} ({match['P1_Dojo']}) vs ⚪ {match['P2_Name']} ({match['P2_Dojo']})<br>
                <span class="winner-text">Ganador: {match['Winner'] if match['Winner'] else 'Pendiente'}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Sistema de Votación (Si ya hay nombres)
            if match['P1_Name'] and match['P2_Name'] and not match['Winner']:
                v_col1, v_col2 = st.columns(2)
                if v_col1.button(f"Votar 🔴 {match['P1_Name']}", key=f"v1_{match['Match_ID']}"):
                    st.toast("¡Voto registrado!")
                if v_col2.button(f"Votar ⚪ {match['P2_Name']}", key=f"v2_{match['Match_ID']}"):
                    st.toast("¡Voto registrado!")
