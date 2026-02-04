import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import hashlib
import random
import time

# --- CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="WKB Tournament Hub", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .category-box { 
        background: #1f2937; padding: 15px; border-radius: 8px; 
        border: 1px solid #374151; margin-bottom: 10px;
    }
    .fighter-tag {
        background: #374151; padding: 5px 10px; border-radius: 4px;
        display: inline-block; margin: 2px; font-size: 14px;
    }
    .bracket-card { 
        background: linear-gradient(145deg, #111827, #1f2937);
        padding: 15px; border-radius: 10px; border-left: 5px solid #ef4444; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit#gid=0"
ADMIN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

CATEGORIES = [
    "KUMITE - MEN | -70kg", "KUMITE - MEN | +70kg",
    "KUMITE - WOMEN | -60kg", "KUMITE - WOMEN | +60kg"
]

@st.cache_resource
def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    conn = get_conn()
    return conn.read(spreadsheet=SHEET_URL, worksheet=worksheet, ttl=2)

def save_data(df, worksheet):
    conn = get_conn()
    conn.update(spreadsheet=SHEET_URL, worksheet=worksheet, data=df)
    st.cache_data.clear()

# --- FUNCIONES DE TORNEO ---

def reset_system():
    # 1. Limpiar Brackets
    empty_brackets = pd.DataFrame(columns=["Category", "Match_ID", "P1_Name", "P1_Dojo", "P1_Votes", "P2_Name", "P2_Dojo", "P2_Votes", "Winner", "Live"])
    save_data(empty_brackets, "Hoja1")
    # 2. Limpiar Inscritos
    empty_insc = pd.DataFrame(columns=["Nombre_Completo", "Dojo", "Categoria", "Estado"])
    save_data(empty_insc, "Inscripciones")
    st.success("Sistema reseteado: Sin atletas, sin llaves.")

def generate_brackets(category):
    inscritos = load_data("Inscripciones")
    atletas = inscritos[inscritos['Categoria'] == category].to_dict('records')
    random.shuffle(atletas)
    
    if len(atletas) < 2:
        st.error(f"No hay suficientes atletas en {category} para armar llaves.")
        return

    brackets = load_data("Hoja1")
    # Limpiar brackets previos de esta categoría
    brackets = brackets[brackets['Category'] != category]
    
    # Armar llaves (Máximo 4 peleas en cuartos para el ejemplo)
    matches = []
    num_peleas = (len(atletas) + 1) // 2
    
    for i in range(num_peleas):
        p1 = atletas.pop(0) if atletas else None
        p2 = atletas.pop(0) if atletas else None
        
        match_data = {
            "Category": category,
            "Match_ID": f"Q{i+1}",
            "P1_Name": p1['Nombre_Completo'] if p1 else "",
            "P1_Dojo": p1['Dojo'] if p1 else "",
            "P1_Votes": 0,
            "P2_Name": p2['Nombre_Completo'] if p2 else "BYE (Pasa Directo)",
            "P2_Dojo": p2['Dojo'] if p2 else "",
            "P2_Votes": 0,
            "Winner": p1['Nombre_Completo'] if p1 and not p2 else "",
            "Live": False
        }
        matches.append(match_data)
    
    new_brackets = pd.concat([brackets, pd.DataFrame(matches)], ignore_index=True)
    save_data(new_brackets, "Hoja1")

# --- INTERFAZ ---

st.title("🥋 WKB Tournament Management")

# Manejo de sesión Admin
if 'is_admin' not in st.session_state: st.session_state.is_admin = False

with st.sidebar:
    st.header("⚙️ Admin Panel")
    if not st.session_state.is_admin:
        pass_input = st.text_input("Admin Password", type="password")
        if st.button("Unlock"):
            if hashlib.sha256(pass_input.encode()).hexdigest() == ADMIN_HASH:
                st.session_state.is_admin = True
                st.rerun()
    else:
        st.button("Logout", on_click=lambda: st.session_state.update({"is_admin": False}))
        if st.button("🚨 RESET TOTAL DEL TORNEO", type="primary"):
            reset_system()
            st.rerun()

# --- TABS ---
tab_reg, tab_view = st.tabs(["📝 Inscripción", "🏆 Categorías y Brackets"])

with tab_reg:
    st.header("Registro de Atletas")
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Nombre Completo")
        dojo = col2.text_input("Dojo / Club")
        cat = st.selectbox("Categoría", CATEGORIES)
        if st.form_submit_button("Inscribirse"):
            if name and dojo:
                df_i = load_data("Inscripciones")
                new_row = pd.DataFrame([{"Nombre_Completo": name, "Dojo": dojo, "Categoria": cat, "Estado": "Inscrito"}])
                save_data(pd.concat([df_i, new_row], ignore_index=True), "Inscripciones")
                st.success(f"{name} agregado a la lista de {cat}")
            else:
                st.error("Completa los campos")

with tab_view:
    df_inscritos = load_data("Inscripciones")
    df_brackets = load_data("Hoja1")
    
    for c in CATEGORIES:
        st.subheader(f"📍 {c}")
        
        # Filtramos si hay llaves armadas para esta categoría
        c_brackets = df_brackets[df_brackets['Category'] == c]
        
        if c_brackets.empty:
            # ETAPA 1: MOSTRAR LISTA DE INSCRITOS
            c_inscritos = df_inscritos[df_inscritos['Categoria'] == c]
            st.info(f"Etapa actual: **Inscripciones Abiertas**")
            
            if not c_inscritos.empty:
                cols = st.columns(3)
                for idx, row in c_inscritos.iterrows():
                    cols[idx % 3].markdown(f"<div class='fighter-tag'>👤 {row['Nombre_Completo']} <br><small>{row['Dojo']}</small></div>", unsafe_allow_html=True)
            else:
                st.write("Aún no hay inscritos en esta categoría.")
            
            if st.session_state.is_admin and not c_inscritos.empty:
                if st.button(f"🔒 Cerrar y Sortear Llaves: {c}", key=f"btn_{c}"):
                    generate_brackets(c)
                    st.rerun()
        else:
            # ETAPA 2: MOSTRAR BRACKETS (LLAVES)
            st.success("Etapa actual: **Competencia / Brackets Formados**")
            for _, match in c_brackets.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="bracket-card">
                        <small>Combate {match['Match_ID']}</small><br>
                        <b>🔴 {match['P1_Name']}</b> vs <b>⚪ {match['P2_Name']}</b>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botones de Voto para el público
                    if not match['Winner'] and match['P2_Name'] != "BYE (Pasa Directo)":
                        vcol1, vcol2 = st.columns(2)
                        vcol1.button(f"Votar 🔴", key=f"v1{match['Match_ID']}{c}")
                        vcol2.button(f"Votar ⚪", key=f"v2{match['Match_ID']}{c}")
                    
                    # Control Admin para ganador
                    if st.session_state.is_admin:
                        ganador = st.selectbox("Definir Ganador", ["", match['P1_Name'], match['P2_Name']], key=f"win_{match['Match_ID']}{c}")
