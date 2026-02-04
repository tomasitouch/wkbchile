import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import hashlib
import datetime
import urllib.parse
import base64

# --- 1. CONFIGURACIÓN Y SEGURIDAD ---
st.set_page_config(
    page_title="WKB Official Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

# HASH DE LA CONTRASEÑA "admin123"
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
# CÓDIGO DE PAGO SIMULADO
PAYMENT_CODE = "WKB2026" 

# LINK GOOGLE SHEET
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 2. ESTILOS CSS (MEJORADO PARA SCROLL HORIZONTAL) ---
if 'theme' not in st.session_state: st.session_state.theme = 'dark'

bg_color = "#0e1117" if st.session_state.theme == 'dark' else "#f0f2f6"
text_color = "white" if st.session_state.theme == 'dark' else "#0e1117"
card_bg = "#1f2937" if st.session_state.theme == 'dark' else "#ffffff"
border_color = "#374151" if st.session_state.theme == 'dark' else "#d1d5db"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&display=swap');
    @viewport {{ width: device-width; scale: 1; }}
    
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    h1, h2, h3, h4, div, button, label, input {{ font-family: 'Roboto Condensed', sans-serif !important; text-transform: uppercase; }}
    
    /* HEADER */
    .header-container {{ 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px 20px; background: linear-gradient(180deg, {card_bg} 0%, {bg_color} 100%); 
        border-bottom: 1px solid {border_color}; margin-bottom: 20px; flex-wrap: wrap;
    }}
    .sponsor-logo {{ height: 45px; margin-left: 15px; opacity: 0.8; filter: grayscale(100%); }}
    
    /* SCROLL HORIZONTAL FORZADO (PC Y MÓVIL) */
    .bracket-wrapper {{
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 20px;
    }}
    .bracket-container {{ 
        display: flex; 
        justify-content: flex-start; /* Alinea a la izquierda para permitir scroll */
        min-width: 1000px; /* Fuerza el ancho mínimo para que no se apile */
        padding: 20px; 
    }}
    .round {{ 
        min-width: 220px; 
        margin: 0 15px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-around; 
    }}
    
    /* CAJAS JUGADORES */
    .player-box {{ 
        background: {card_bg}; padding: 10px; margin: 6px 0; border-radius: 6px; 
        position: relative; z-index: 2; box-shadow: 0 4px 6px rgba(0,0,0,0.2); 
        border: 1px solid {border_color};
    }}
    
    /* Colores Esquinas */
    .border-red {{ border-left: 6px solid #ef4444; }}
    .border-white {{ border-left: 6px solid #ffffff; }}
    
    .p-name {{ font-size: 14px; font-weight: bold; color: {text_color}; }}
    .p-details {{ font-size: 10px; color: #9ca3af; display: flex; justify-content: space-between; }}
    
    /* CONECTORES */
    .line-r {{ position: absolute; right: -18px; width: 18px; border-bottom: 2px solid #6b7280; top: 50%; z-index: 1; }}
    .conn-v {{ position: absolute; right: -18px; width: 10px; border-right: 2px solid #6b7280; z-index: 1; }}
    
    /* FORMULARIOS */
    .stTextInput input, .stNumberInput input {{ background-color: {card_bg}; color: {text_color}; border: 1px solid {border_color}; }}
</style>
""", unsafe_allow_html=True)

# --- 3. GESTIÓN DE DATOS ---

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

# Inicializar Estado
if 'registration_cart' not in st.session_state: st.session_state.registration_cart = []
if 'page' not in st.session_state: st.session_state.page = 0

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# Cargar Datos Torneo
@st.cache_data(ttl=15)
def load_tournament_data():
    conn = get_connection()
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Hoja1", ttl=15)
        if df.empty or "Category" not in df.columns:
            # Generar estructura si está vacía
            data = []
            for cat in ALL_CATS:
                for m in ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']:
                    data.append({"Category": cat, "Match_ID": m, "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0, "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0, "Winner": None, "Live": False})
            df = pd.DataFrame(data)
            conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
        return df
    except: return pd.DataFrame() # Return empty on error

# Guardar Inscripción
def save_registration_to_sheet(participants_list):
    conn = get_connection()
    try:
        # Leer hoja de inscripciones existente o crear nueva
        try:
            existing_df = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones", ttl=0)
        except:
            existing_df = pd.DataFrame(columns=["Nombre", "Edad", "Peso", "Estatura", "Grado", "Dojo", "Organizacion", "Contacto", "Consentimiento", "Descargo", "Foto_Base64", "Fecha_Registro"])
        
        new_data = pd.DataFrame(participants_list)
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        
        conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=updated_df)
        return True
    except Exception as e:
        st.error(f"Error al guardar inscripción: {e}")
        return False

# Guardar Torneo
def save_bracket_data(df):
    conn = get_connection()
    conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
    load_tournament_data.clear()

main_df = load_tournament_data()

# --- 4. NAVEGACIÓN ---
if 'view' not in st.session_state: st.session_state.view = "HOME"
if 'cat' not in st.session_state: st.session_state.cat = None

def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

# --- HEADER ---
def render_header():
    logo_org = "https://cdn-icons-png.flaticon.com/512/1603/1603754.png"
    logo_spon1 = "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg"
    
    st.markdown(f"""
    <div class="header-container">
        <div style="display:flex; align-items:center;">
            <img src="{logo_org}" height="50" style="margin-right:15px; filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));">
            <div>
                <h2 style="margin:0; font-size: 20px; letter-spacing: 1px;">WKB CHILE</h2>
                <small style="color:#FDB931; font-weight:bold;">OFFICIAL HUB</small>
            </div>
        </div>
        <div>
            <img src="{logo_spon1}" class="sponsor-logo">
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. VISTA: INSCRIPCIÓN (NUEVA) ---
if st.session_state.view == "REGISTER":
    render_header()
    if st.button("⬅ VOLVER AL INICIO"): go("HOME")
    
    st.title("📝 INSCRIPCIÓN AL TORNEO")
    
    # Selector de Modo
    reg_mode = st.radio("Tipo de Inscripción", ["Individual", "Colectiva (Dojo/Equipo)"], horizontal=True)
    
    st.markdown("---")
    
    with st.form("participant_form", clear_on_submit=True):
        st.subheader("Datos del Participante")
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre Completo")
        edad = c2.number_input("Edad", min_value=4, max_value=99, step=1)
        
        c3, c4, c5 = st.columns(3)
        peso = c3.number_input("Peso (kg)", min_value=20.0, step=0.5)
        estatura = c4.number_input("Estatura (cm)", min_value=100, step=1)
        grado = c5.slider("Grado (Kyu/Dan)", 1, 10, 10)
        
        c6, c7 = st.columns(2)
        dojo = c6.text_input("Dojo")
        org = c7.text_input("Organización")
        
        contacto = st.text_input("Número de Contacto (+569...)")
        
        foto = st.file_uploader("Foto Frontal (Estilo Carnet)", type=['jpg', 'png', 'jpeg'])
        
        st.markdown("#### Términos Legales")
        consent = st.checkbox("Acepto el Consentimiento Informado")
        descargo = st.checkbox("Acepto el Descargo de Responsabilidad Legal")
        
        # Botón para añadir (Diferente texto según modo)
        btn_text = "AGREGAR A LA LISTA" if "Colectiva" in reg_mode else "CONTINUAR AL PAGO"
        add_btn = st.form_submit_button(btn_text)
        
        if add_btn:
            if not (nombre and dojo and contacto and consent and descargo):
                st.error("Faltan datos obligatorios o aceptar términos.")
            else:
                # Procesar imagen a base64 (string corto)
                img_str = "No Adjuntada"
                if foto:
                    try:
                        img_bytes = foto.read()
                        img_str = base64.b64encode(img_bytes).decode()
                    except: pass
                
                participant = {
                    "Nombre": nombre, "Edad": edad, "Peso": peso, "Estatura": estatura,
                    "Grado": grado, "Dojo": dojo, "Organizacion": org, "Contacto": contacto,
                    "Consentimiento": consent, "Descargo": descargo, "Foto_Base64": img_str[:100] + "...", # Truncado para visual
                    "Foto_Full": img_str, # Guardar completo
                    "Fecha_Registro": str(datetime.datetime.now())
                }
                
                st.session_state.registration_cart.append(participant)
                st.success(f"{nombre} agregado correctamente.")

    # --- ZONA DE PAGO Y FINALIZACIÓN ---
    if st.session_state.registration_cart:
        st.markdown("### 🛒 LISTA DE INSCRIPCIÓN")
        cart_df = pd.DataFrame(st.session_state.registration_cart)
        # Mostrar tabla sin la foto base64 larga
        st.dataframe(cart_df.drop(columns=["Foto_Full", "Foto_Base64"]), use_container_width=True)
        
        total_pago = len(st.session_state.registration_cart) * 15000 # Ejemplo 15.000 por persona
        st.markdown(f"### TOTAL A PAGAR: :green[${total_pago:,}] CLP")
        
        st.info("Para confirmar, realiza la transferencia y luego ingresa el código de validación.")
        
        c_code, c_btn = st.columns([3, 1])
        pay_code = c_code.text_input("Código de Validación de Pago", placeholder="Ej: WKB2026")
        
        if c_btn.button("CONFIRMAR INSCRIPCIÓN"):
            if pay_code == PAYMENT_CODE:
                # Guardar en Google Sheets
                if save_registration_to_sheet(st.session_state.registration_cart):
                    st.balloons()
                    st.success("¡INSCRIPCIÓN EXITOSA! Nos vemos en el tatami.")
                    st.session_state.registration_cart = [] # Limpiar carrito
                    time.sleep(3)
                    go("HOME")
            else:
                st.error("Código de pago inválido. Contacta a la organización.")
                
        if st.button("🗑️ Limpiar Lista"):
            st.session_state.registration_cart = []
            st.rerun()

# --- 6. VISTA HOME (PRINCIPAL) ---
elif st.session_state.view == "HOME":
    render_header()
    
    # Botón Gigante de Inscripción
    if st.button("📝 INSCRÍBETE AQUÍ (INDIVIDUAL O EQUIPO)", type="primary", use_container_width=True):
        go("REGISTER")
    
    st.markdown("---")
    st.markdown("### 📂 SEGUIMIENTO DE LLAVES")
    
    # Paginación
    CATEGORIES_PER_PAGE = 6
    start_idx = st.session_state.page * CATEGORIES_PER_PAGE
    end_idx = start_idx + CATEGORIES_PER_PAGE
    current_cats = ALL_CATS[start_idx:end_idx]
    
    cols = st.columns(2)
    for i, full_cat_name in enumerate(current_cats):
        display_name = full_cat_name.replace("KUMITE - ", "").replace("KATA - ", "🥋 ")
        if cols[i % 2].button(display_name, key=full_cat_name):
            go("BRACKET", full_cat_name)
            
    c1, c2, c3 = st.columns([1, 2, 1])
    if st.session_state.page > 0:
        if c1.button("⬅ Anterior"): st.session_state.page -= 1; st.rerun()
    if end_idx < len(ALL_CATS):
        if c3.button("Siguiente ➡"): st.session_state.page += 1; st.rerun()

# --- 7. VISTA BRACKET (HORIZONTAL) ---
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    cat_df = main_df[main_df['Category'] == cat].set_index('Match_ID')
    
    def get_row(mid): 
        try: return cat_df.loc[mid]
        except: return pd.Series()
    def get_val(row, col): return row[col] if col in row and pd.notna(row[col]) else "..."

    render_header()
    if st.button("⬅ VOLVER"): go("HOME")
    st.markdown(f"<h3 style='text-align:center; color:#FDB931;'>{cat}</h3>", unsafe_allow_html=True)

    # ADMIN
    with st.sidebar:
        st.header("Admin")
        if not st.session_state.get('is_admin'):
            if st.button("Login") and check_admin(st.text_input("Pwd",type="password")):
                st.session_state.is_admin = True; st.rerun()
        else:
            if st.button("Logout"): st.session_state.is_admin = False; st.rerun()
            mid = st.selectbox("Match", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
            with st.form("ed"):
                row = get_row(mid)
                n1 = st.text_input("Rojo", get_val(row,'P1_Name'))
                n2 = st.text_input("Blanco", get_val(row,'P2_Name'))
                win = st.selectbox("Winner", ["", n1, n2])
                if st.form_submit_button("Guardar"):
                    idx = main_df[(main_df['Category']==cat)&(main_df['Match_ID']==mid)].index
                    if not idx.empty:
                        main_df.at[idx[0],'P1_Name']=n1; main_df.at[idx[0],'P2_Name']=n2
                        main_df.at[idx[0],'Winner']=win
                        save_bracket_data(main_df); st.rerun()

    # GENERADOR HTML DE BRACKET HORIZONTAL
    def render_card(mid):
        row = get_row(mid)
        p1, p2 = get_val(row,'P1_Name'), get_val(row,'P2_Name')
        w = get_val(row,'Winner')
        return f"""
        <div class="player-box border-red"><div class="p-name">{p1 if p1 else "..."}</div></div>
        <div class="player-box border-white"><div class="p-name">{p2 if p2 else "..."}</div><div class="line-r"></div></div>
        """

    # HTML ESTRUCTURA
    html = f"""
    <div class="bracket-wrapper">
        <div class="bracket-container">
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">CUARTOS</div>
                {render_card('Q1')}<div style="height:30px"></div>
                {render_card('Q2')}<div style="height:30px"></div>
                {render_card('Q3')}<div style="height:30px"></div>
                {render_card('Q4')}
            </div>
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">SEMIFINAL</div>
                <div style="height:60px"></div>
                {render_card('S1')}
                <div style="height:120px"></div>
                {render_card('S2')}
            </div>
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">FINAL</div>
                <div style="height:150px"></div>
                {render_card('F1')}
            </div>
            <div class="round">
                <div style="text-align:center;font-size:10px;margin-bottom:10px">CAMPEÓN</div>
                <div style="height:150px"></div>
                <div class="champion-box">{get_val(get_row('F1'),'Winner') if get_val(get_row('F1'),'Winner') != "..." else "?"} 🏆</div>
            </div>
        </div>
    </div>
    """
    st.html(html)
