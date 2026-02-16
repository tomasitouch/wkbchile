import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import uuid
from datetime import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Chile | Registro Oficial",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 5px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTES Y CONFIGURACIÓN ---
PRECIO = 15000
CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

# --- LÓGICA DE DATOS ---
def get_conn():
    return st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    conn = get_conn()
    try:
        # Forzamos ttl=0 para datos críticos de inscripción
        return conn.read(worksheet="Inscripciones", ttl=0)
    except Exception:
        return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Dojo", "Categoria", "Estado"])

def validar_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- INTEGRACIÓN MERCADOPAGO ---
def generar_link_pago(datos):
    try:
        sdk = mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
        preference_data = {
            "items": [{
                "title": f"Inscripción Torneo WKB - {datos['categoria']}",
                "quantity": 1,
                "unit_price": PRECIO,
                "currency_id": "CLP"
            }],
            "payer": {"email": datos['email'], "name": datos['nombre']},
            "back_urls": {
                "success": "https://wkbchile.streamlit.app/", # Cambiar por tu URL real
                "failure": "https://wkbchile.streamlit.app/"
            },
            "auto_return": "approved",
            "external_reference": datos['id']
        }
        result = sdk.preference().create(preference_data)
        return result["response"]["init_point"]
    except Exception as e:
        st.error(f"Error al conectar con MercadoPago: {e}")
        return None

# --- COMPONENTES DE INTERFAZ ---
def sidebar_stats(df):
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3003/3003831.png", width=100) # Reemplazar con logo WKB
        st.title("Panel de Control")
        
        if not df.empty:
            confirmados = len(df[df['Estado'] == 'Confirmado'])
            st.metric("Total Competidores", f"{confirmados} / 500")
            st.progress(min(confirmados / 500, 1.0))
        
        st.divider()
        st.info("📅 15-16 Marzo 2025\n\n📍 Gimnasio Polideportivo, Santiago")

def formulario():
    st.subheader("📝 Formulario de Inscripción")
    
    with st.container(border=True):
        with st.form("registro_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Completo")
                email = st.text_input("Correo Electrónico")
                telefono = st.text_input("WhatsApp (ej: +569...)")
            
            with col2:
                dojo = st.text_input("Nombre del Dojo / Escuela")
                edad = st.number_input("Edad", 5, 80, 18)
                categoria = st.selectbox("Categoría de Competición", CATEGORIAS)
            
            st.markdown("---")
            enviar = st.form_submit_button("VALIDAR Y PROCEDER AL PAGO", use_container_width=True)

        if enviar:
            if not nombre or not dojo or not validar_email(email):
                st.error("Por favor, completa todos los campos correctamente.")
            else:
                st.session_state.temp_datos = {
                    "id": str(uuid.uuid4())[:8].upper(),
                    "nombre": nombre,
                    "email": email,
                    "telefono": telefono,
                    "dojo": dojo,
                    "edad": edad,
                    "categoria": categoria
                }
                st.session_state.paso = "pago"
                st.rerun()

def checkout():
    datos = st.session_state.temp_datos
    st.subheader("💳 Confirmación de Pago")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("**Resumen de Inscripción:**")
        st.json(datos)
        if st.button("⬅️ Corregir Datos"):
            st.session_state.paso = "registro"
            st.rerun()

    with col2:
        st.warning("Para completar el registro, debes realizar el pago. Una vez aprobado, quedarás inscrito automáticamente.")
        
        link = generar_link_pago(datos)
        if link:
            st.link_button("🚀 PAGAR CON MERCADOPAGO", link, use_container_width=True, type="primary")
            
            st.divider()
            with st.expander("¿Ya pagaste o tienes un código de cortesía?"):
                codigo = st.text_input("Ingresar código")
                if st.button("Validar Registro"):
                    if codigo == st.secrets.get("admin_password", "WKB2025"):
                        completar_registro(datos, "Cortesía/Admin")
                    else:
                        st.error("Código inválido")

def completar_registro(datos, metodo):
    with st.status("Procesando inscripción...", expanded=True) as status:
        try:
            conn = get_conn()
            df_actual = cargar_datos()
            
            nuevo_registro = {
                "ID": datos['id'],
                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Nombre": datos['nombre'],
                "Email": datos['email'],
                "Dojo": datos['dojo'],
                "Categoria": datos['categoria'],
                "Estado": "Confirmado",
                "Metodo": metodo
            }
            
            df_final = pd.concat([df_actual, pd.DataFrame([nuevo_registro])], ignore_index=True)
            conn.update(worksheet="Inscripciones", data=df_final)
            
            status.update(label="¡Inscripción Exitosa!", state="complete", expanded=False)
            st.balloons()
            st.success(f"Felicidades {datos['nombre']}, ya estás registrado.")
            
            # Limpieza de sesión
            for key in ['temp_datos', 'paso']:
                if key in st.session_state: del st.session_state[key]
            
            if st.button("Hacer otra inscripción"):
                st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

# --- APP PRINCIPAL ---
def main():
    if 'paso' not in st.session_state:
        st.session_state.paso = "registro"

    df_total = cargar_datos()
    sidebar_stats(df_total)

    tab_reg, tab_lista, tab_admin = st.tabs(["Registro", "Inscritos", "Administración"])

    with tab_reg:
        if st.session_state.paso == "registro":
            formulario()
        elif st.session_state.paso == "pago":
            checkout()

    with tab_lista:
        st.subheader("Participantes Confirmados")
        if not df_total.empty:
            search = st.text_input("Buscar por nombre o dojo")
            mask = df_total['Nombre'].str.contains(search, case=False) | df_total['Dojo'].str.contains(search, case=False)
            st.dataframe(df_total[mask][["Nombre", "Dojo", "Categoria"]], use_container_width=True)
        else:
            st.info("Aún no hay inscritos.")

    with tab_admin:
        pw = st.text_input("Acceso Admin", type="password")
        if pw == st.secrets.get("admin_password", "admin123"):
            st.download_button("Descargar Base de Datos (CSV)", 
                             df_total.to_csv(index=False), 
                             "inscritos_wkb.csv", "text/csv")
            st.dataframe(df_total)

if __name__ == "__main__":
    main()
