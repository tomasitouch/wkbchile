import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import uuid
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Inscripciones",
    page_icon="🥋",
    layout="centered"
)

# --- ESTILOS BÁSICOS ---
st.markdown("""
<style>
    .main-title {
        color: #FDB931;
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin: 20px 0;
    }
    .form-container {
        background: #1f2937;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #374151;
    }
    .success-box {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        color: #10b981;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
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

def guardar_inscripcion(datos):
    """Guarda en tiempo real en sheets"""
    try:
        conn = get_connection()
        
        # Leer datos existentes
        df_existente = conn.read(worksheet="Inscripciones")
        
        # Crear nueva fila
        nueva_fila = pd.DataFrame([datos])
        
        # Combinar
        if df_existente.empty:
            df_final = nueva_fila
        else:
            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        
        # Guardar en sheets
        conn.update(worksheet="Inscripciones", data=df_final)
        
        # Backup automático
        try:
            conn.update(worksheet="Backup", data=df_final)
        except:
            pass
            
        return True
    except Exception as e:
        st.error(f"Error guardando: {e}")
        return False

# --- FUNCIONES DE VALIDACIÓN ---
def validar_email(email):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, email) is not None

def validar_telefono(telefono):
    telefono = re.sub(r'\D', '', telefono)
    return len(telefono) == 9 and telefono[0] in ['9', '2']

# --- PÁGINA PRINCIPAL ---
def main():
    st.markdown('<h1 class="main-title">🥋 WKB CHILE - INSCRIPCIONES</h1>', unsafe_allow_html=True)
    
    # Logo
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-PCwsXVnqhlX-vNev8BDqbszitBpm3cC8GQ&s", use_container_width=True)
    
    # Información del torneo
    st.info("📅 15-16 Marzo 2025 | 📍 Gimnasio Polideportivo, Santiago")
    
    # --- FORMULARIO DE INSCRIPCIÓN ---
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.subheader("📝 Datos del Competidor")
        
        with st.form("form_inscripcion"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre Completo *", placeholder="Ej: Juan Pérez")
                edad = st.number_input("Edad *", min_value=18, max_value=99, step=1)
                email = st.text_input("Email *", placeholder="ejemplo@correo.com")
            
            with col2:
                dojo = st.text_input("Dojo/Escuela *", placeholder="Ej: WKB Santiago")
                telefono = st.text_input("Teléfono *", placeholder="Ej: 912345678")
                categoria = st.selectbox("Categoría *", CATEGORIAS)
            
            st.markdown("---")
            acepta = st.checkbox("Acepto los términos y condiciones del torneo *")
            
            # Botón de envío
            submit = st.form_submit_button("✅ INSCRIBIRME", type="primary", use_container_width=True)
            
            if submit:
                # Validaciones
                errores = []
                if not nombre:
                    errores.append("Nombre es obligatorio")
                if not email or not validar_email(email):
                    errores.append("Email inválido")
                if not telefono or not validar_telefono(telefono):
                    errores.append("Teléfono inválido (formato: 912345678)")
                if not dojo:
                    errores.append("Dojo es obligatorio")
                if not acepta:
                    errores.append("Debes aceptar los términos")
                
                if errores:
                    for error in errores:
                        st.error(error)
                else:
                    # Preparar datos
                    id_unico = str(uuid.uuid4())[:8].upper()
                    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    datos_inscripcion = {
                        "ID": id_unico,
                        "Fecha": fecha_actual,
                        "Nombre": nombre,
                        "Edad": edad,
                        "Email": email,
                        "Telefono": telefono,
                        "Dojo": dojo,
                        "Categoria": categoria,
                        "Estado": "Pendiente"
                    }
                    
                    # Guardar en sheets (tiempo real)
                    with st.spinner("Guardando inscripción..."):
                        if guardar_inscripcion(datos_inscripcion):
                            st.balloons()
                            st.markdown(f'''
                            <div class="success-box">
                                <h3>✅ ¡INSCRIPCIÓN REGISTRADA!</h3>
                                <p>Tu número de inscripción es: <strong>{id_unico}</strong></p>
                                <p>Te contactaremos para confirmar el pago.</p>
                            </div>
                            ''', unsafe_allow_html=True)
                            
                            # Mostrar resumen
                            with st.expander("📋 Ver resumen de tu inscripción"):
                                st.json(datos_inscripcion)
                            
                            # Botón para nueva inscripción
                            if st.button("📝 NUEVA INSCRIPCIÓN"):
                                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # --- VER INSCRITOS (opcional) ---
    with st.expander("👥 Ver inscritos actuales"):
        try:
            conn = get_connection()
            df = conn.read(worksheet="Inscripciones")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.caption(f"Total: {len(df)} inscripciones")
            else:
                st.info("No hay inscritos aún")
        except:
            st.warning("No se pudo cargar la lista")

if __name__ == "__main__":
    main()
