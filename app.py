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
import random
import math

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Official Hub", 
    layout="wide", 
    page_icon="🥋",
    initial_sidebar_state="collapsed"
)

# Meta tags para responsive en móviles
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN GOOGLE SHEETS ---
# REEMPLAZA CON TU URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"

# --- 3. SEGURIDAD ---
# La contraseña es: admin123
ADMIN_TOKEN_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"

def check_admin(password):
    return hashlib.sha256(password.encode()).hexdigest() == ADMIN_TOKEN_HASH

# --- 4. ESTILOS CSS (Mantenemos el diseño PRO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #0e1117; color: white; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Roboto Condensed', sans-serif !important; text-transform: uppercase; }
    
    /* Header */
    .header-container { 
        display: flex; justify-content: space-between; align-items: center; 
        padding: 15px; background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%); 
        border-bottom: 1px solid #374151; margin-bottom: 20px; flex-wrap: wrap;
    }
    
    /* Bracket Container */
    .bracket-container { 
        overflow-x: auto; padding: 20px 10px; display: flex; justify-content: center; 
        min-height: 450px; scrollbar-width: thin;
    }
    .bracket-container::-webkit-scrollbar { height: 8px; }
    .bracket-container::-webkit-scrollbar-thumb { background: #ef4444; border-radius: 4px; }
    
    .rounds-wrapper { display: flex; gap: 30px; padding: 0 20px; }
    
    .round { 
        min-width: 260px; display: flex; flex-direction: column; justify-content: space-around; 
        background: rgba(31,41,55,0.3); border-radius: 10px; padding: 10px;
    }
    
    .round-title { 
        text-align: center; color: #FDB931; font-weight: bold; margin-bottom: 15px; 
        border-bottom: 2px solid #374151; 
    }
    
    /* Player Box */
    .player-box { 
        background: linear-gradient(145deg, #1f2937, #111827); padding: 12px; margin: 10px 0; 
        border-radius: 8px; border: 1px solid #374151; position: relative;
    }
    .border-red { border-left: 5px solid #ef4444; }
    .border-white { border-left: 5px solid #ffffff; }
    
    .p-name { font-weight: bold; font-size: 14px; color: white; }
    .p-details { font-size: 11px; color: #9ca3af; display: flex; justify-content: space-between; }
    
    .conn-v { 
        position: absolute; right: -25px; width: 2px; background: #6b7280; 
        top: 50%; transform: translateY(-50%); z-index: 1; 
    }
    .line-r { 
        position: absolute; right: -25px; width: 25px; height: 2px; 
        background: #6b7280; top: 50%; transform: translateY(-50%); 
    }
    
    /* Botones */
    div.stButton > button { width: 100%; border-radius: 6px; font-weight: bold; }
    
    /* Champion */
    .champion-box {
        background: linear-gradient(135deg, #FDB931, #d9a024); color: black;
        padding: 20px; text-align: center; font-weight: bold; border-radius: 10px;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# --- 5. LÓGICA DE DATOS ---

CATEGORIES_CONFIG = {
    "KUMITE - MEN (18+)": ["-65kg", "-70kg", "-75kg", "-80kg", "-90kg", "+90kg"],
    "KUMITE - WOMEN (18+)": ["-55kg", "-60kg", "+65kg"],
    "KATA": ["All Categories"]
}
ALL_CATS = [f"{g} | {s}" for g, s in CATEGORIES_CONFIG.items() for s in s]

# Definir conexión
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# Cargar Datos (Brackets)
@st.cache_data(ttl=10)
def load_data():
    conn = get_connection()
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Hoja1")
        # Si está vacío o nueva hoja, inicializar
        if df.empty or "P1_Votes" not in df.columns:
            return get_initial_df()
        return df
    except:
        return get_initial_df()

# Cargar Inscripciones
@st.cache_data(ttl=10)
def load_inscriptions():
    conn = get_connection()
    try:
        df = conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones")
        if df.empty:
            return get_initial_inscriptions_df()
        return df
    except:
        return get_initial_inscriptions_df()

def get_initial_df():
    data = []
    matches = ['Q1', 'Q2', 'Q3', 'Q4', 'S1', 'S2', 'F1']
    for cat in ALL_CATS:
        for m in matches:
            is_q = 'Q' in m
            data.append({
                "Category": cat, "Match_ID": m, 
                "P1_Name": "", "P1_Dojo": "", "P1_Votes": 0,
                "P2_Name": "", "P2_Dojo": "", "P2_Votes": 0,
                "Winner": None, "Live": False
            })
    return pd.DataFrame(data)

def get_initial_inscriptions_df():
    return pd.DataFrame(columns=[
        "ID", "Nombre_Completo", "Edad", "Peso", "Estatura", "Grado", 
        "Dojo", "Organizacion", "Telefono", "Email", "Categoria", 
        "Tipo_Inscripcion", "Codigo_Pago", "Fecha_Inscripcion", "Foto_Base64",
        "Consentimiento", "Descargo", "Estado_Pago", "Grupo_ID", "Estado"
    ])

def save_data(df):
    conn = get_connection()
    conn.update(spreadsheet=SHEET_URL, worksheet="Hoja1", data=df)
    st.cache_data.clear()

def save_inscriptions(df):
    conn = get_connection()
    conn.update(spreadsheet=SHEET_URL, worksheet="Inscripciones", data=df)
    st.cache_data.clear()

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- 6. LÓGICA DE NEGOCIO (SORTEO Y RESET) ---

def generate_random_bracket(category):
    """
    Genera llaves aleatorias para una categoría.
    Maneja BYES si el número de participantes no es potencia de 2.
    """
    global main_df, inscriptions_df
    
    # 1. Obtener participantes activos
    candidates = inscriptions_df[(inscriptions_df['Categoria'] == category) & 
                                 (inscriptions_df['Estado'] != 'Eliminado')]
    
    num_p = len(candidates)
    if num_p < 2:
        return False, "Se necesitan mínimo 2 participantes."
    
    # 2. Mezclar aleatoriamente
    participants_list = candidates.to_dict('records')
    random.shuffle(participants_list)
    
    # 3. Calcular tamaño del cuadro (Bracket Size)
    # Potencia de 2 más cercana hacia arriba (ej: 5 inscritos -> bracket de 8)
    bracket_size = 2 ** math.ceil(math.log2(num_p))
    if bracket_size > 8: bracket_size = 8 # Limitado a 8 por el diseño visual actual
    if bracket_size < 2: bracket_size = 2
    
    # Número de "Byes" (Gente que pasa directo)
    num_byes = bracket_size - num_p
    
    # 4. Limpiar datos previos de esa categoría en Hoja1
    cat_idx = main_df[main_df['Category'] == category].index
    main_df.loc[cat_idx, ['P1_Name','P1_Dojo','P1_Votes','P2_Name','P2_Dojo','P2_Votes','Winner']] = ["","",0,"","",0,None]
    
    # 5. Definir qué matches llenar
    matches_to_fill = []
    if bracket_size == 8: matches_to_fill = ['Q1', 'Q2', 'Q3', 'Q4']
    elif bracket_size == 4: matches_to_fill = ['S1', 'S2']
    elif bracket_size == 2: matches_to_fill = ['F1']
    
    # 6. Asignar peleas
    # Estrategia: Llenar P1 con participantes reales. Llenar P2 con participantes reales o BYE.
    # Los BYEs se asignan aleatoriamente debido al shuffle inicial, pero técnicamente
    # en un torneo se ponen al final. Aquí, simplemente llenamos slots.
    
    p_idx = 0
    
    for m_id in matches_to_fill:
        if p_idx < len(participants_list):
            # Jugador 1 (Rojo)
            p1 = participants_list[p_idx]
            p_idx += 1
            
            # Jugador 2 (Blanco) o BYE
            p2_name = "BYE"
            p2_dojo = "-"
            
            # Si todavía hay gente y no necesitamos gastar un BYE obligatorio en este slot específico
            # (Simplificación: Si hay gente, ponla. Si no, Bye).
            # Para distribuir los Byes correctamente: Total espacios restantes vs Gente restante
            slots_remaining = (len(matches_to_fill) * 2) - (matches_to_fill.index(m_id) * 2) - 1
            people_remaining = len(participants_list) - p_idx
            
            # Si gente restante < slots restantes, este podría ser un Bye.
            # En sistema aleatorio puro:
            if p_idx < len(participants_list):
                # ¿Debemos forzar un Bye? Si num_byes > 0
                # En un sorteo de karate, los Byes se distribuyen. 
                # Simplemente: Si quedan Byes, asignamos uno a este match para que P1 pase.
                if num_byes > 0:
                    # Asignamos Bye
                    num_byes -= 1
                    # P2 queda como BYE
                else:
                    # Asignamos oponente real
                    p2 = participants_list[p_idx]
                    p2_name = p2['Nombre_Completo']
                    p2_dojo = p2['Dojo']
                    p_idx += 1
            
            # Guardar en DataFrame
            idx = main_df[(main_df['Category']==category) & (main_df['Match_ID']==m_id)].index
            if not idx.empty:
                i = idx[0]
                main_df.at[i, 'P1_Name'] = p1['Nombre_Completo']
                main_df.at[i, 'P1_Dojo'] = p1['Dojo']
                main_df.at[i, 'P2_Name'] = p2_name
                main_df.at[i, 'P2_Dojo'] = p2_dojo
                
                # Si es BYE, P1 gana automáticamente y avanza
                if p2_name == "BYE":
                    main_df.at[i, 'Winner'] = p1['Nombre_Completo']
                    advance_winner(category, m_id, p1['Nombre_Completo'], p1['Dojo'])

    save_data(main_df)
    return True, f"Sorteo realizado para {num_p} atletas (Top {bracket_size})."

def advance_winner(category, current_match, winner_name, winner_dojo):
    """Mueve al ganador a la siguiente ronda automáticamente"""
    target_match = None
    target_pos = None
    
    if 'Q' in current_match:
        target_match = 'S1' if current_match in ['Q1', 'Q2'] else 'S2'
        target_pos = 'P1' if current_match in ['Q1', 'Q3'] else 'P2'
    elif 'S' in current_match:
        target_match = 'F1'
        target_pos = 'P1' if current_match == 'S1' else 'P2'
        
    if target_match:
        idx = main_df[(main_df['Category'] == category) & (main_df['Match_ID'] == target_match)].index
        if not idx.empty:
            main_df.at[idx[0], f'{target_pos}_Name'] = winner_name
            main_df.at[idx[0], f'{target_pos}_Dojo'] = winner_dojo

def reset_entire_system():
    """BORRADO TOTAL"""
    try:
        # 1. Reset Hoja1
        empty_brackets = get_initial_df()
        save_data(empty_brackets)
        # 2. Reset Inscripciones
        empty_insc = get_initial_inscriptions_df()
        save_inscriptions(empty_insc)
        return True
    except Exception as e:
        return False

# --- 7. CARGA DE ESTADO ---
if 'view' not in st.session_state: st.session_state.view = "HOME"
if 'cat' not in st.session_state: st.session_state.cat = None
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'voted' not in st.session_state: st.session_state.voted = set()

main_df = load_data()
inscriptions_df = load_inscriptions()

def go(view, cat=None):
    st.session_state.view = view
    st.session_state.cat = cat
    st.rerun()

# --- 8. UI PRINCIPAL ---

# Render Header
logo_url = "https://cdn-icons-png.flaticon.com/512/1603/1603754.png"
st.markdown(f"""
<div class="header-container">
    <div style="display:flex; align-items:center;">
        <img src="{logo_url}" height="50" style="margin-right:15px;">
        <div>
            <h2 style="margin:0; color:white;">WKB CHILE</h2>
            <small style="color:#FDB931; font-weight:bold;">OFFICIAL TOURNAMENT HUB</small>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR (ADMIN)
with st.sidebar:
    st.title("🔧 Panel Admin")
    
    if not st.session_state.is_admin:
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if check_admin(pwd):
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Acceso denegado")
    else:
        st.success("Administrador Logueado")
        if st.button("Cerrar Sesión"):
            st.session_state.is_admin = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ⚠️ ZONA DE PELIGRO")
        if st.button("⛔ RESETEO TOTAL DEL SISTEMA"):
            if reset_entire_system():
                st.success("Sistema formateado.")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Error al resetear.")

# VISTA HOME
if st.session_state.view == "HOME":
    
    tab1, tab2 = st.tabs(["🏆 CATEGORÍAS & BRACKETS", "📝 INSCRIPCIÓN DE ATLETAS"])
    
    with tab1:
        st.markdown("### SELECCIONA UNA CATEGORÍA PARA VER LLAVES")
        st.info("Selecciona una categoría para ver los combates, votar o (si eres admin) realizar el sorteo.")
        
        for group, cats in CATEGORIES_CONFIG.items():
            with st.expander(group, expanded=True):
                cols = st.columns(3)
                for i, c in enumerate(cats):
                    full_cat = f"{group} | {c}"
                    # Contar inscritos
                    n_insc = len(inscriptions_df[inscriptions_df['Categoria'] == full_cat])
                    
                    if cols[i%3].button(f"{c} ({n_insc})", key=full_cat, use_container_width=True):
                        go("BRACKET", full_cat)

    with tab2:
        st.markdown("### 📝 FORMULARIO DE INSCRIPCIÓN")
        
        with st.form("inscription_form"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo")
                edad = st.number_input("Edad", 5, 99, 18)
                peso = st.number_input("Peso (kg)", 20.0, 150.0, 70.0)
                estatura = st.number_input("Estatura (cm)", 100, 220, 170)
            with col2:
                dojo = st.text_input("Dojo")
                grado = st.text_input("Grado/Cinturón")
                email = st.text_input("Email")
                telefono = st.text_input("Teléfono")
            
            cat_list = ALL_CATS
            categoria = st.selectbox("Categoría", cat_list)
            foto = st.file_uploader("Foto Perfil", type=['jpg','png'])
            
            submitted = st.form_submit_button("✅ INSCRIBIRSE")
            
            if submitted:
                # Validar si la categoría ya comenzó (tiene brackets generados)
                cat_data = main_df[main_df['Category'] == categoria]
                has_started = any(cat_data['P1_Name'] != "")
                
                if has_started:
                    st.error("⛔ Las inscripciones para esta categoría están CERRADAS porque el torneo ya comenzó.")
                elif nombre and dojo and categoria:
                    # Guardar
                    foto_str = image_to_base64(Image.open(foto)) if foto else ""
                    
                    import uuid
                    pid = str(uuid.uuid4())[:8]
                    
                    new_data = {
                        "ID": pid, "Nombre_Completo": nombre, "Edad": edad, "Peso": peso, 
                        "Estatura": estatura, "Grado": grado, "Dojo": dojo, "Email": email,
                        "Telefono": telefono, "Categoria": categoria, "Tipo_Inscripcion": "Individual",
                        "Fecha_Inscripcion": str(datetime.datetime.now()), "Foto_Base64": foto_str,
                        "Estado": "Activo"
                    }
                    
                    df_new = pd.DataFrame([new_data])
                    inscriptions_df = pd.concat([inscriptions_df, df_new], ignore_index=True)
                    save_inscriptions(inscriptions_df)
                    st.success("Inscripción exitosa!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.warning("Faltan datos obligatorios.")

# VISTA BRACKET
elif st.session_state.view == "BRACKET":
    cat = st.session_state.cat
    cat_df = main_df[main_df['Category'] == cat].set_index('Match_ID')
    
    # Header de la vista
    c1, c2 = st.columns([1, 5])
    if c1.button("⬅️ VOLVER"): go("HOME")
    c2.markdown(f"## {cat}")
    
    # --- ZONA ADMIN DE CATEGORÍA ---
    if st.session_state.is_admin:
        with st.expander("🛠️ GESTIÓN DE CATEGORÍA (ADMIN)", expanded=True):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write("**Estado:**")
                has_started = any(cat_df['P1_Name'] != "")
                if has_started:
                    st.success("🟢 TORNEO EN CURSO")
                else:
                    st.warning("🟡 ESPERANDO CIERRE DE INSCRIPCIONES")
                
                inscritos = inscriptions_df[inscriptions_df['Categoria'] == cat]
                st.metric("Inscritos", len(inscritos))
            
            with col_b:
                if not has_started:
                    if st.button("🔒 CERRAR INSCRIPCIONES Y SORTEAR LLAVES", type="primary"):
                        success, msg = generate_random_bracket(cat)
                        if success:
                            st.success(msg)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    if st.button("♻️ RE-SORTEAR (Borrará resultados actuales)"):
                        generate_random_bracket(cat)
                        st.rerun()
            
            # Edición Manual
            st.markdown("---")
            st.caption("Modificar Resultado Manualmente")
            match_id = st.selectbox("Seleccionar Pelea", ['Q1','Q2','Q3','Q4','S1','S2','F1'])
            winner_name = st.text_input("Nombre Ganador (Debe ser exacto)")
            if st.button("🏆 Declarar Ganador Manual"):
                # Buscar fila
                idx = main_df[(main_df['Category'] == cat) & (main_df['Match_ID'] == match_id)].index
                if not idx.empty and winner_name:
                    main_df.at[idx[0], 'Winner'] = winner_name
                    # Buscar dojo del ganador
                    p1n = main_df.at[idx[0], 'P1_Name']
                    p1d = main_df.at[idx[0], 'P1_Dojo']
                    p2n = main_df.at[idx[0], 'P2_Name']
                    p2d = main_df.at[idx[0], 'P2_Dojo']
                    
                    w_dojo = p1d if winner_name == p1n else p2d
                    advance_winner(cat, match_id, winner_name, w_dojo)
                    save_data(main_df)
                    st.success("Guardado")
                    st.rerun()

    # --- VISUALIZACIÓN DE LLAVES ---
    def get_val(mid, col):
        try: 
            val = cat_df.loc[mid, col]
            return val if pd.notna(val) else ""
        except: return ""

    # Determinar qué rondas mostrar
    show_q = any(get_val(m, 'P1_Name') != "" for m in ['Q1','Q2','Q3','Q4'])
    show_s = any(get_val(m, 'P1_Name') != "" for m in ['S1','S2'])
    
    # Si no ha empezado
    if not show_q and not show_s and get_val('F1', 'P1_Name') == "":
        st.info("⚠️ Las llaves aún no han sido sorteadas. El administrador debe cerrar las inscripciones.")
        # Mostrar lista de inscritos
        st.subheader("Atletas Inscritos:")
        inscritos = inscriptions_df[inscriptions_df['Categoria'] == cat]
        if not inscritos.empty:
            for _, row in inscritos.iterrows():
                st.write(f"🥋 **{row['Nombre_Completo']}** ({row['Dojo']})")
        else:
            st.write("No hay inscritos aún.")
            
    else:
        # Construir HTML Dinámico
        html_content = '<div class="bracket-container"><div class="rounds-wrapper">'
        
        def render_match_html(p1, d1, p2, d2, win):
            # Clases para color
            c1 = "border-red"
            c2 = "border-white"
            return f"""
            <div style="display:flex; flex-direction:column; gap:5px; margin-bottom:20px;">
                <div class="player-box {c1}">
                    <div class="p-name">{p1 if p1 else "..."}</div>
                    <div class="p-details">{d1}</div>
                </div>
                <div class="player-box {c2}">
                    <div class="p-name">{p2 if p2 else "..."}</div>
                    <div class="p-details">{d2}</div>
                </div>
            </div>
            """

        # CUARTOS (Si existen)
        if show_q:
            html_content += '<div class="round"><div class="round-title">CUARTOS</div>'
            for m in ['Q1', 'Q2', 'Q3', 'Q4']:
                html_content += render_match_html(
                    get_val(m, 'P1_Name'), get_val(m, 'P1_Dojo'),
                    get_val(m, 'P2_Name'), get_val(m, 'P2_Dojo'), get_val(m, 'Winner')
                )
            html_content += '</div>'

        # SEMIS
        html_content += '<div class="round"><div class="round-title">SEMIFINALES</div>'
        # Espaciado para centrar si hay cuartos
        spacer = 'style="justify-content: space-around; height: 100%; display: flex; flex-direction: column;"'
        html_content += f'<div {spacer}>'
        for m in ['S1', 'S2']:
             html_content += render_match_html(
                get_val(m, 'P1_Name'), get_val(m, 'P1_Dojo'),
                get_val(m, 'P2_Name'), get_val(m, 'P2_Dojo'), get_val(m, 'Winner')
            )
        html_content += '</div></div>'

        # FINAL
        html_content += '<div class="round"><div class="round-title">FINAL</div>'
        html_content += f'<div {spacer}>'
        html_content += render_match_html(
            get_val('F1', 'P1_Name'), get_val('F1', 'P1_Dojo'),
            get_val('F1', 'P2_Name'), get_val('F1', 'P2_Dojo'), get_val('F1', 'Winner')
        )
        html_content += '</div></div>'
        
        # CAMPEÓN
        winner_f1 = get_val('F1', 'Winner')
        html_content += f"""
        <div class="round">
            <div class="round-title">CAMPEÓN</div>
            <div style="display:flex; align-items:center; height:100%;">
                <div class="champion-box">{winner_f1 if winner_f1 else "?"}</div>
            </div>
        </div>
        """
        
        html_content += '</div></div>'
        st.html(html_content)

        # --- VOTACIÓN ---
        st.markdown("### 🗳️ VOTA POR TU FAVORITO")
        matches_to_vote = []
        if show_q: matches_to_vote.extend(['Q1','Q2','Q3','Q4'])
        matches_to_vote.extend(['S1','S2','F1'])
        
        cols = st.columns(4)
        for i, m in enumerate(matches_to_vote):
            p1 = get_val(m, 'P1_Name')
            p2 = get_val(m, 'P2_Name')
            
            # Solo mostrar botón si hay pelea definida y no es BYE
            if p1 and p2 and p2 != "BYE" and p1 != "BYE":
                with cols[i % 4]:
                    st.markdown(f"**{m}**")
                    if st.button(f"🔴 {p1}", key=f"v1_{m}"):
                        idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==m)].index
                        main_df.at[idx[0], 'P1_Votes'] += 1
                        save_data(main_df)
                        st.toast(f"Voto para {p1}")
                    
                    if st.button(f"⚪ {p2}", key=f"v2_{m}"):
                        idx = main_df[(main_df['Category']==cat) & (main_df['Match_ID']==m)].index
                        main_df.at[idx[0], 'P2_Votes'] += 1
                        save_data(main_df)
                        st.toast(f"Voto para {p2}")
                    
                    # Mostrar Barra
                    v1 = int(get_val(m, 'P1_Votes') or 0)
                    v2 = int(get_val(m, 'P2_Votes') or 0)
                    tot = v1 + v2
                    if tot > 0:
                        p1_pct = int((v1/tot)*100)
                        st.progress(p1_pct)
                        st.caption(f"{p1_pct}% vs {100-p1_pct}%")
