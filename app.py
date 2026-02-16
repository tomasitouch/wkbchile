import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import plotly.express as px
import plotly.graph_objects as go
import uuid
import re
import time
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB World Cup 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PROFESIONALES ---
st.markdown("""
    <style>
    /* Importar fuente moderna */
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&family=Roboto:wght@300;400&display=swap');

    h1, h2, h3 { font-family: 'Oswald', sans-serif; text-transform: uppercase; }
    p, div, span { font-family: 'Roboto', sans-serif; }

    /* Fondo y contenedores */
    .stApp { background-color: #f8f9fa; }
    
    /* Logo Header */
    .logo-container { text-align: center; margin-bottom: 20px; }
    .logo-img { max-width: 150px; }

    /* Cuenta Regresiva */
    .countdown-box {
        background: linear-gradient(135deg, #1a1a1a 0%, #333333 100%);
        color: #d4af37; /* Dorado */
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        border: 2px solid #d4af37;
    }
    .countdown-time { font-size: 2.5rem; font-weight: bold; font-family: 'Oswald'; }
    .countdown-label { font-size: 1rem; color: #fff; letter-spacing: 2px; }

    /* Tarjetas de Métricas */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #d00000; /* Rojo Kyokushin */
    }

    /* Botón Principal */
    .stButton>button {
        background-color: #d00000;
        color: white;
        border-radius: 30px;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #a00000;
        box-shadow: 0 5px 15px rgba(208,0,0,0.4);
    }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
PRECIO = 15000
CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# --- FUNCIONES DE DATOS Y LÓGICA ---

def get_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        return conn.read(worksheet="Inscripciones", ttl=0)
    except:
        return pd.DataFrame(columns=["ID", "Nombre", "Categoria", "Dojo", "Estado", "Fecha"])

def guardar_inscripcion(datos, metodo_pago="MercadoPago"):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df_existente = get_data()
        nueva_fila = pd.DataFrame([{
            "ID": datos['id'],
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Nombre": datos['nombre'],
            "Email": datos['email'],
            "Dojo": datos['dojo'],
            "Categoria": datos['categoria'],
            "Telefono": datos['telefono'],
            "Edad": datos['edad'],
            "Estado": "CONFIRMADO",
            "Metodo": metodo_pago
        }])
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False

def crear_link_mp(datos):
    try:
        sdk = mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
        base_url = st.secrets["general"]["public_url"]
        preference = {
            "items": [{"title": f"WKB 2026 - {datos['categoria']}", "quantity": 1, "currency_id": "CLP", "unit_price": PRECIO}],
            "payer": {"email": datos['email']},
            "back_urls": {
                "success": f"{base_url}?status=approved",
                "failure": f"{base_url}?status=failure"
            },
            "auto_return": "approved",
            "external_reference": datos['id']
        }
        res = sdk.preference().create(preference)
        return res["response"]["init_point"]
    except:
        return None

# --- COMPONENTES VISUALES ---

def mostrar_header():
    st.markdown(f"""
        <div class='logo-container'>
            <img src='{LOGO_URL}' class='logo-img'>
            <h1>WKB CHILE WORLD CUP</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Lógica de Cuenta Regresiva
    ahora = datetime.now()
    restante = FECHA_TORNEO - ahora
    dias = restante.days
    horas, resto = divmod(restante.seconds, 3600)
    minutos, _ = divmod(resto, 60)
    
    st.markdown(f"""
        <div class='countdown-box'>
            <div class='countdown-label'>FALTAN PARA EL GRAN DÍA</div>
            <div class='countdown-time'>{dias}d : {horas}h : {minutos}m</div>
            <div class='countdown-label'>24 ABRIL 2026</div>
        </div>
    """, unsafe_allow_html=True)

def dashboard_avanzado(df):
    st.markdown("### 📊 Analytics del Torneo")
    
    if df.empty:
        st.info("Esperando primeros registros para generar gráficos.")
        return

    # Filtro de datos confirmados
    df = df[df['Estado'] == 'Confirmado'] if 'Estado' in df.columns else df

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Inscritos", len(df))
    c2.metric("Dojos Presentes", df['Dojo'].nunique() if 'Dojo' in df.columns else 0)
    c3.metric("Categorías Activas", df['Categoria'].nunique() if 'Categoria' in df.columns else 0)
    c4.metric("Cupos Restantes", f"{500 - len(df)}")

    # Gráfico 1: Inscritos por Categoría (Barras Horizontales Interactivas)
    conteo_cat = df['Categoria'].value_counts().reset_index()
    conteo_cat.columns = ['Categoría', 'Inscritos']
    
    fig_bar = px.bar(conteo_cat, x='Inscritos', y='Categoría', orientation='h',
                     title="Competitividad por Categoría",
                     text='Inscritos',
                     color='Inscritos',
                     color_continuous_scale=['#333333', '#d00000']) # Negro a Rojo
    fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", font_family="Roboto")
    st.plotly_chart(fig_bar, use_container_width=True)

    # Sección Premios (Podios)
    st.markdown("### 🏆 Disputa por el Podio (1º, 2º, 3º Lugar)")
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        # Gráfico avanzado de Sunburst para ver distribución Dojo -> Categoría
        if 'Dojo' in df.columns:
            fig_sun = px.sunburst(df, path=['Categoria', 'Dojo'], 
                                  title="Distribución de Fuerza (Categoría > Dojo)",
                                  color_discrete_sequence=px.colors.qualitative.Dark24)
            st.plotly_chart(fig_sun, use_container_width=True)

    with col_g2:
        # Tabla estilizada de premios
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:10px; border:1px solid #ddd;">
            <h4 style="color:#d4af37; text-align:center;">PREMIOS EN JUEGO</h4>
            <ul style="list-style:none; padding:0;">
                <li style="margin-bottom:10px;">🥇 <b>1er Lugar:</b> Copa Gran Campeón + Medalla Oro + Certificado</li>
                <li style="margin-bottom:10px;">🥈 <b>2do Lugar:</b> Copa Finalista + Medalla Plata + Certificado</li>
                <li style="margin-bottom:10px;">🥉 <b>3er Lugar:</b> Medalla Bronce + Certificado</li>
            </ul>
            <hr>
            <p style="text-align:center; font-size:0.9rem; color:grey;">
                Total de medallas a entregar: <b>30</b> (3 por categoría)
            </p>
        </div>
        """, unsafe_allow_html=True)

def formulario_inscripcion():
    st.markdown("### 📝 Ficha de Competidor")
    with st.form("form_registro"):
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre Completo")
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
        with c2:
            edad = st.number_input("Edad", 18, 99)
            dojo = st.text_input("Dojo")
            categoria = st.selectbox("Categoría", CATEGORIAS)
        
        submitted = st.form_submit_button("IR AL PAGO", use_container_width=True)
        
        if submitted:
            if nombre and email and dojo:
                st.session_state.temp_data = {
                    "id": str(uuid.uuid4())[:8].upper(),
                    "nombre": nombre, "email": email, "telefono": telefono,
                    "edad": edad, "dojo": dojo, "categoria": categoria
                }
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("Completa los campos obligatorios")

def pasarela_pago():
    data = st.session_state.temp_data
    st.success("✅ Datos Validados")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""
        **Resumen:**
        * Atleta: {data['nombre']}
        * Categoría: {data['categoria']}
        * Dojo: {data['dojo']}
        
        **Total a Pagar: ${PRECIO:,.0f}**
        """)
        if st.button("✏️ Editar"):
            st.session_state.step = 1
            st.rerun()
            
    with c2:
        link = crear_link_mp(data)
        if link:
            st.link_button("💳 PAGAR CON MERCADO PAGO", link, use_container_width=True)
        else:
            st.error("Error conectando con el sistema de pagos")

# --- CONTROLADOR PRINCIPAL ---
def main():
    # Menú Lateral
    menu = st.sidebar.radio("Navegación", ["🏠 Inicio & Stats", "📝 Inscribirse", "🔐 Admin"])
    
    # Manejo de retorno de MP
    if "status" in st.query_params and st.query_params["status"] == "approved":
        if 'temp_data' in st.session_state:
            if guardar_inscripcion(st.session_state.temp_data):
                st.balloons()
                st.success("¡INSCRIPCIÓN ÉXITOSA! Nos vemos en el tatami.")
                st.session_state.temp_data = {}
                st.query_params.clear()
    
    if menu == "🏠 Inicio & Stats":
        mostrar_header()
        df = get_data()
        dashboard_avanzado(df)
        
    elif menu == "📝 Inscribirse":
        mostrar_header()
        if 'step' not in st.session_state: st.session_state.step = 1
        
        if st.session_state.step == 1:
            formulario_inscripcion()
        else:
            pasarela_pago()
            
    elif menu == "🔐 Admin":
        st.title("Panel Administrativo")
        pwd = st.text_input("Contraseña", type="password")
        if pwd == st.secrets["general"].get("admin_password", "admin"):
            df = get_data()
            st.dataframe(df)
            st.download_button("Descargar Excel", df.to_csv(), "inscritos_2026.csv")

if __name__ == "__main__":
    main()
