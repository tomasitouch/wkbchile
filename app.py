import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import uuid
import datetime
import re
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Inscripciones",
    page_icon="🥋",
    layout="wide"
)

# --- CONSTANTES ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
PRECIO = 15000
CODIGO_SECRETO = "WKB2025"  # Código para pagos gratis (pruebas)

CATEGORIAS = [
    "KUMITE -65kg (18+)",
    "KUMITE -70kg (18+)",
    "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)",
    "KUMITE -90kg (18+)",
    "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino",
    "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino",
    "KATA (18+) Mixto"
]

# --- CONEXIÓN SHEETS ---
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    """Carga todos los datos del sheets"""
    try:
        conn = get_connection()
        return conn.read(worksheet="Inscripciones")
    except:
        return pd.DataFrame()

def guardar_inscripcion(datos):
    """Guarda en sheets"""
    try:
        conn = get_connection()
        df_existente = cargar_datos()
        
        nueva_fila = pd.DataFrame([datos])
        
        if df_existente.empty:
            df_final = nueva_fila
        else:
            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# --- MERCADOPAGO ---
@st.cache_resource
def init_mp():
    try:
        return mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
    except:
        return None

def crear_pago_mp(nombre, email, categoria):
    sdk = init_mp()
    if not sdk:
        return None
    
    preference_data = {
        "items": [
            {
                "title": f"Inscripción WKB - {categoria}",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": PRECIO,
            }
        ],
        "payer": {"name": nombre, "email": email},
        "back_urls": {
            "success": "https://wkbchile.streamlit.app/?success=1",
            "failure": "https://wkbchile.streamlit.app/?failure=1",
        },
        "auto_return": "approved",
    }
    
    try:
        preference = sdk.preference().create(preference_data)
        if preference["status"] == 201:
            return preference["response"]["init_point"]
    except:
        return None

# --- ESTADÍSTICAS ---
def mostrar_estadisticas(df):
    """Muestra contadores por categoría"""
    if df.empty:
        st.warning("No hay inscritos aún")
        return
    
    # Total
    st.metric("TOTAL INSCRITOS", len(df))
    
    # Por categoría
    st.subheader("📊 Inscritos por Categoría")
    cols = st.columns(3)
    
    categorias_counts = df['Categoria'].value_counts()
    
    for i, (cat, count) in enumerate(categorias_counts.items()):
        with cols[i % 3]:
            st.info(f"**{cat}**\n\n{count} inscritos")

# --- FORMULARIO DE INSCRIPCIÓN ---
def formulario_inscripcion():
    st.header("📝 NUEVA INSCRIPCIÓN")
    
    with st.form("form_inscripcion"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre Completo *")
            edad = st.number_input("Edad *", 18, 99, 25)
            email = st.text_input("Email *")
        
        with col2:
            dojo = st.text_input("Dojo *")
            telefono = st.text_input("Teléfono *")
            categoria = st.selectbox("Categoría *", CATEGORIAS)
        
        submitted = st.form_submit_button("CONTINUAR AL PAGO", use_container_width=True)
        
        if submitted:
            if nombre and email and dojo and telefono:
                st.session_state['temp_inscripcion'] = {
                    'nombre': nombre,
                    'edad': edad,
                    'email': email,
                    'dojo': dojo,
                    'telefono': telefono,
                    'categoria': categoria,
                    'id': str(uuid.uuid4())[:8].upper()
                }
                st.session_state['paso'] = 'pago'
                st.rerun()
            else:
                st.error("Completa todos los campos")

# --- PANTALLA DE PAGO ---
def pantalla_pago():
    datos = st.session_state['temp_inscripcion']
    
    st.header("💰 CONFIRMAR PAGO")
    st.info(f"**Inscribiendo a:** {datos['nombre']}")
    st.info(f"**Categoría:** {datos['categoria']}")
    st.info(f"**Total a pagar:** ${PRECIO:,}")
    
    tab1, tab2 = st.tabs(["💳 MercadoPago", "🔑 Ingresar Código"])
    
    with tab1:
        st.write("Paga con tarjeta de crédito/débito")
        
        if st.button("GENERAR LINK DE PAGO", use_container_width=True):
            link = crear_pago_mp(datos['nombre'], datos['email'], datos['categoria'])
            if link:
                st.markdown(f"[➡️ HACER CLIC PARA PAGAR]({link})")
                st.info("Después de pagar, espera la confirmación")
                
                # Botón simulación
                if st.button("✅ SIMULAR PAGO EXITOSO"):
                    st.session_state['paso'] = 'confirmar'
                    st.rerun()
            else:
                st.error("Error con MercadoPago")
    
    with tab2:
        st.write("Ingresa el código de acceso")
        codigo = st.text_input("Código", type="password")
        
        if st.button("VALIDAR CÓDIGO", use_container_width=True):
            if codigo == CODIGO_SECRETO:
                st.session_state['paso'] = 'confirmar'
                st.rerun()
            else:
                st.error("Código incorrecto")
    
    if st.button("⬅️ VOLVER"):
        st.session_state['paso'] = 'formulario'
        st.rerun()

# --- CONFIRMACIÓN Y GUARDADO ---
def confirmar_inscripcion():
    datos = st.session_state['temp_inscripcion']
    
    fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    registro = {
        "ID": datos['id'],
        "Fecha": fecha,
        "Nombre": datos['nombre'],
        "Edad": datos['edad'],
        "Email": datos['email'],
        "Telefono": datos['telefono'],
        "Dojo": datos['dojo'],
        "Categoria": datos['categoria'],
        "Estado": "Confirmado",
        "Monto": PRECIO,
        "Metodo": "MercadoPago/Código"
    }
    
    if guardar_inscripcion(registro):
        st.balloons()
        st.success(f"✅ ¡INSCRIPCIÓN CONFIRMADA!\n\nID: {datos['id']}")
        
        # Limpiar sesión
        if st.button("📝 NUEVA INSCRIPCIÓN"):
            for key in ['temp_inscripcion', 'paso']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    else:
        st.error("Error guardando")

# --- PANEL ADMIN BÁSICO ---
def panel_admin():
    st.header("⚙️ ADMINISTRACIÓN")
    
    password = st.text_input("Contraseña", type="password")
    
    if password == "admin123":
        df = cargar_datos()
        
        if not df.empty:
            st.subheader("Todas las inscripciones")
            st.dataframe(df, use_container_width=True)
            
            # Exportar
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 DESCARGAR CSV", csv, "inscripciones.csv")
            
            # Estadísticas
            st.subheader("Resumen")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", len(df))
            col2.metric("Confirmados", len(df[df['Estado'] == 'Confirmado']))
            col3.metric("Monto total", f"${len(df) * PRECIO:,}")
        else:
            st.info("No hay datos")

# --- MENÚ PRINCIPAL ---
def main():
    st.title("🥋 WKB CHILE - TORNEO 2025")
    
    # Menú de navegación simple
    menu = st.sidebar.radio(
        "Menú",
        ["🏠 Inicio", "📝 Inscribirse", "👥 Ver inscritos", "⚙️ Admin"]
    )
    
    # Cargar datos para estadísticas
    df = cargar_datos()
    df_confirmados = df[df['Estado'] == 'Confirmado'] if not df.empty else pd.DataFrame()
    
    # Sidebar con estadísticas siempre visible
    with st.sidebar:
        st.markdown("---")
        st.subheader("📊 ESTADÍSTICAS")
        
        if not df_confirmados.empty:
            st.metric("Total confirmados", len(df_confirmados))
            
            # Top 3 categorías
            st.write("**Por categoría:**")
            top_cats = df_confirmados['Categoria'].value_counts().head(3)
            for cat, count in top_cats.items():
                st.caption(f"• {cat[:20]}...: {count}")
        else:
            st.info("Sin inscritos aún")
    
    # Contenido según menú
    if menu == "🏠 Inicio":
        st.header("Bienvenido al Torneo WKB 2025")
        st.write("📅 15-16 Marzo 2025")
        st.write("📍 Gimnasio Polideportivo, Santiago")
        
        if not df_confirmados.empty:
            mostrar_estadisticas(df_confirmados)
    
    elif menu == "📝 Inscribirse":
        if 'paso' not in st.session_state:
            st.session_state['paso'] = 'formulario'
        
        if st.session_state['paso'] == 'formulario':
            formulario_inscripcion()
        elif st.session_state['paso'] == 'pago':
            pantalla_pago()
        elif st.session_state['paso'] == 'confirmar':
            confirmar_inscripcion()
    
    elif menu == "👥 Ver inscritos":
        st.header("Lista de Inscritos")
        
        if not df_confirmados.empty:
            # Filtro rápido
            categoria_filtro = st.selectbox("Filtrar por categoría", ["Todas"] + CATEGORIAS)
            
            df_mostrar = df_confirmados.copy()
            if categoria_filtro != "Todas":
                df_mostrar = df_mostrar[df_mostrar['Categoria'] == categoria_filtro]
            
            st.dataframe(df_mostrar[['Nombre', 'Dojo', 'Categoria', 'Fecha']], use_container_width=True)
            st.caption(f"Mostrando {len(df_mostrar)} inscritos")
        else:
            st.info("No hay inscritos confirmados")
    
    elif menu == "⚙️ Admin":
        panel_admin()

if __name__ == "__main__":
    main()
