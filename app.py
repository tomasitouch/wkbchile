import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import uuid
import re
import time
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Inscripción Oficial WKB 2025",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZADO (Estética Profesional) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    .stButton>button {
        background-color: #00A650; /* Verde MercadoPago */
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #008f45;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .header-style {
        font-size: 24px;
        font-weight: 700;
        color: #333;
        margin-bottom: 20px;
        border-bottom: 2px solid #E6E6E6;
        padding-bottom: 10px;
    }
    
    .success-box {
        padding: 20px;
        background-color: #D4EDDA;
        color: #155724;
        border-radius: 10px;
        border: 1px solid #C3E6CB;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
PRECIO = 15000
CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# --- GESTIÓN DE ESTADO ---
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- FUNCIONES BACKEND ---

def get_db_connection():
    """Conexión a Google Sheets"""
    return st.connection("gsheets", type=GSheetsConnection)

def get_all_registrations():
    """Obtiene todos los registros actuales"""
    conn = get_db_connection()
    try:
        return conn.read(worksheet="Inscripciones", ttl=0) # ttl=0 para datos frescos
    except:
        return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Dojo", "Categoria", "Estado", "Metodo", "Payment_ID"])

def save_registration(data, payment_id="MANUAL"):
    """Guarda una nueva inscripción en Sheets"""
    conn = get_db_connection()
    try:
        df_existente = get_all_registrations()
        
        # Verificar si el ID ya existe para evitar duplicados al refrescar
        if not df_existente.empty and data['id'] in df_existente['ID'].values:
            return True # Ya existe, tratamos como éxito

        nueva_fila = {
            "ID": data['id'],
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nombre": data['nombre'],
            "Email": data['email'],
            "Dojo": data['dojo'],
            "Categoria": data['categoria'],
            "Telefono": data['telefono'],
            "Edad": data['edad'],
            "Estado": "CONFIRMADO",
            "Metodo": "MercadoPago" if payment_id != "MANUAL" else "Manual/Admin",
            "Payment_ID": payment_id
        }
        
        df_nueva = pd.DataFrame([nueva_fila])
        df_final = pd.concat([df_existente, df_nueva], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error guardando datos: {e}")
        return False

def create_mercadopago_preference(user_data):
    """Genera el link de pago"""
    try:
        sdk = mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
        
        base_url = st.secrets["general"]["public_url"]
        
        preference_data = {
            "items": [
                {
                    "id": "INS-WKB-2025",
                    "title": f"Inscripción Torneo WKB - {user_data['categoria']}",
                    "quantity": 1,
                    "currency_id": "CLP",
                    "unit_price": float(PRECIO)
                }
            ],
            "payer": {
                "name": user_data['nombre'],
                "email": user_data['email']
            },
            "back_urls": {
                "success": f"{base_url}?status=approved",
                "failure": f"{base_url}?status=failure",
                "pending": f"{base_url}?status=pending"
            },
            "auto_return": "approved",
            "external_reference": user_data['id'],
            "statement_descriptor": "WKB CHILE"
        }
        
        preference_response = sdk.preference().create(preference_data)
        return preference_response["response"]["init_point"]
    except Exception as e:
        st.error(f"Error conectando con MercadoPago: {e}")
        return None

def validar_form(nombre, email, dojo, telefono):
    if not nombre or len(nombre) < 3: return False, "Nombre inválido"
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): return False, "Email inválido"
    if not dojo: return False, "Falta el Dojo"
    if not telefono: return False, "Falta teléfono"
    return True, ""

# --- INTERFAZ DE USUARIO ---

def show_header():
    col1, col2 = st.columns([1, 4])
    with col1:
        st.write("🥋") # Aquí podrías poner st.image("logo.png")
    with col2:
        st.title("WKB Chile | Inscripción 2025")
        st.markdown("**Fecha:** 15-16 Marzo 2025 | **Lugar:** Polideportivo Santiago")

def step_1_form():
    st.markdown('<div class="header-style">1. Datos del Competidor</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre Completo")
            email = st.text_input("Correo Electrónico")
            telefono = st.text_input("Teléfono / WhatsApp")
            
        with col2:
            edad = st.number_input("Edad", min_value=18, max_value=99, value=25)
            dojo = st.text_input("Dojo / Escuela")
            categoria = st.selectbox("Categoría", CATEGORIAS)
            
        if st.button("CONTINUAR AL PAGO ➡️"):
            valid, msg = validar_form(nombre, email, dojo, telefono)
            if valid:
                st.session_state.user_data = {
                    "id": str(uuid.uuid4())[:12].upper(),
                    "nombre": nombre,
                    "email": email,
                    "telefono": telefono,
                    "edad": edad,
                    "dojo": dojo,
                    "categoria": categoria
                }
                st.session_state.step = 2
                st.rerun()
            else:
                st.error(msg)

def step_2_payment():
    st.markdown('<div class="header-style">2. Confirmar y Pagar</div>', unsafe_allow_html=True)
    
    data = st.session_state.user_data
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.info("📋 **Resumen de Inscripción**")
        st.write(f"**Atleta:** {data['nombre']}")
        st.write(f"**Categoría:** {data['categoria']}")
        st.write(f"**Dojo:** {data['dojo']}")
        st.markdown(f"### Total: ${PRECIO:,.0f} CLP")
        
        if st.button("⬅️ Corregir datos"):
            st.session_state.step = 1
            st.rerun()

    with col2:
        st.write("Selecciona tu método de pago:")
        
        # Generar Link MP
        mp_link = create_mercadopago_preference(data)
        
        if mp_link:
            st.link_button("💳 PAGAR AHORA CON MERCADOPAGO", mp_link, use_container_width=True)
            st.caption("Serás redirigido a Mercado Pago de forma segura. Al finalizar, volverás automáticamente aquí.")
        else:
            st.error("No se pudo generar el link de pago. Intenta más tarde.")

def handle_return_url():
    """Maneja el retorno desde MercadoPago"""
    query_params = st.query_params
    status = query_params.get("status", None)
    
    if status == "approved":
        if 'user_data' in st.session_state and st.session_state.user_data:
            data = st.session_state.user_data
            
            with st.status("Procesando tu inscripción...", expanded=True) as status_box:
                st.write("Verificando pago...")
                time.sleep(1)
                st.write("Registrando en base de datos...")
                
                payment_id = query_params.get("payment_id", "MP_UNKNOWN")
                exito = save_registration(data, payment_id)
                
                if exito:
                    status_box.update(label="¡Inscripción Exitosa!", state="complete", expanded=False)
                    st.markdown(f"""
                        <div class="success-box">
                            <h1>✅ ¡Listo, {data['nombre']}!</h1>
                            <p>Tu inscripción ha sido confirmada correctamente.</p>
                            <p>ID de Registro: <strong>{data['id']}</strong></p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                    
                    # Limpiar sesión para nueva inscripción
                    if st.button("Realizar nueva inscripción"):
                        st.session_state.user_data = {}
                        st.session_state.step = 1
                        st.query_params.clear()
                        st.rerun()
                else:
                    st.error("Hubo un error guardando tu registro, pero el pago fue exitoso. Por favor contacta al administrador.")
        else:
            st.warning("Pago detectado, pero se perdió la sesión del formulario. Si recibiste el correo de MercadoPago, estás cubierto.")
            
    elif status == "failure":
        st.error("❌ El pago fue rechazado o cancelado. Por favor intenta nuevamente.")
        if st.button("Intentar de nuevo"):
            st.query_params.clear()
            st.rerun()

def admin_panel():
    st.title("Panel de Administración")
    pwd = st.text_input("Contraseña de Admin", type="password")
    
    if pwd == st.secrets["general"].get("admin_password", "admin"):
        df = get_all_registrations()
        
        st.metric("Total Inscritos", len(df))
        st.metric("Recaudación Estimada", f"${len(df)*PRECIO:,.0f}")
        
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar CSV", csv, "inscritos_wkb.csv", "text/csv")

# --- MAIN APP FLOW ---

def main():
    # Detectar si estamos en modo Admin (por URL o menú oculto)
    menu = st.sidebar.selectbox("Navegación", ["Inscripción", "Admin"])
    
    if menu == "Admin":
        admin_panel()
        return

    # Flujo Normal de Inscripción
    show_header()
    
    # Chequear si venimos volviendo de MercadoPago
    if "status" in st.query_params:
        handle_return_url()
    else:
        if st.session_state.step == 1:
            step_1_form()
        elif st.session_state.step == 2:
            step_2_payment()

if __name__ == "__main__":
    main()
