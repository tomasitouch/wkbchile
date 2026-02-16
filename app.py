import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import uuid
import datetime
import hashlib
import time
import logging
import re

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="WKB Inscripciones",
    page_icon="🥋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Meta tags para móvil
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1f2e 100%);
    }
    /* Tarjeta de inscripción */
    .card {
        background: #1f2937;
        border-radius: 15px;
        padding: 25px;
        border: 1px solid #374151;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    /* Títulos */
    .title {
        color: #FDB931;
        font-size: 28px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    /* Precio */
    .price-tag {
        background: linear-gradient(135deg, #FDB931 0%, #ffaa00 100%);
        color: #0e1117;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0;
    }
    /* Estados de pago */
    .success-message {
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10b981;
        color: #10b981;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .error-message {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid #ef4444;
        color: #ef4444;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 3. CONSTANTES ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1hFlkSSPWqoQDSjkiPV5uaIIx-iHjoihLg2yokDJm-4E/edit?gid=0#gid=0"
PRECIO_INSCRIPCION = 15000  # $15,000 CLP

CATEGORIAS = [
    "KUMITE -65kg (18+)",
    "KUMITE -70kg (18+)",
    "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)",
    "KUMITE -90kg (18+)",
    "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) - Femenino",
    "KUMITE -60kg (18+) - Femenino",
    "KUMITE +65kg (18+) - Femenino",
    "KATA (18+) - Mixto"
]

# --- 4. CONEXIÓN GOOGLE SHEETS ---
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

def cargar_inscripciones():
    """Carga las inscripciones existentes"""
    try:
        conn = get_connection()
        return conn.read(spreadsheet=SHEET_URL, worksheet="Inscripciones")
    except Exception as e:
        logger.error(f"Error cargando inscripciones: {e}")
        return pd.DataFrame()

def guardar_inscripcion(datos):
    """Guarda una nueva inscripción en sheets"""
    try:
        conn = get_connection()
        df_existente = cargar_inscripciones()
        
        # Crear nueva fila
        nueva_fila = pd.DataFrame([datos])
        
        # Combinar
        if df_existente.empty:
            df_final = nueva_fila
        else:
            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        
        # Guardar
        conn.update(
            spreadsheet=SHEET_URL,
            worksheet="Inscripciones",
            data=df_final
        )
        
        # Backup automático
        try:
            conn.update(
                spreadsheet=SHEET_URL,
                worksheet="Backup",
                data=df_final
            )
        except:
            pass
            
        return True
    except Exception as e:
        logger.error(f"Error guardando inscripción: {e}")
        return False

def guardar_pago(datos_pago):
    """Guarda información del pago en sheets"""
    try:
        conn = get_connection()
        df_pagos = conn.read(spreadsheet=SHEET_URL, worksheet="Pagos")
        
        nueva_fila = pd.DataFrame([datos_pago])
        
        if df_pagos.empty:
            df_final = nueva_fila
        else:
            df_final = pd.concat([df_pagos, nueva_fila], ignore_index=True)
        
        conn.update(
            spreadsheet=SHEET_URL,
            worksheet="Pagos",
            data=df_final
        )
        return True
    except Exception as e:
        logger.error(f"Error guardando pago: {e}")
        return False

# --- 5. MERCADOPAGO ---
@st.cache_resource
def init_mercadopago():
    """Inicializa SDK de MercadoPago"""
    try:
        access_token = st.secrets["mercadopago"]["access_token"]
        return mercadopago.SDK(access_token)
    except Exception as e:
        logger.error(f"Error inicializando MercadoPago: {e}")
        return None

def crear_preferencia_pago(datos_comprador, preferencia_id):
    """Crea una preferencia de pago en MercadoPago"""
    sdk = init_mercadopago()
    if not sdk:
        return None
    
    # Datos del comprador
    comprador = datos_comprador["comprador"]
    items = datos_comprador["items"]
    
    # Crear preferencia
    preference_data = {
        "items": [
            {
                "title": f"Inscripción Torneo WKB - {items['categoria']}",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": PRECIO_INSCRIPCION,
                "description": f"Competidor: {comprador['nombre']} - Dojo: {comprador['dojo']}"
            }
        ],
        "payer": {
            "name": comprador["nombre"],
            "email": comprador["email"],
            "phone": {
                "number": comprador["telefono"]
            }
        },
        "back_urls": {
            "success": "https://wkb-torneo.streamlit.app/?success=true",
            "failure": "https://wkb-torneo.streamlit.app/?failure=true",
            "pending": "https://wkb-torneo.streamlit.app/?pending=true"
        },
        "auto_return": "approved",
        "external_reference": preferencia_id,
        "notification_url": "https://tu-dominio.com/webhook/mercadopago",
        "statement_descriptor": "WKB CHILE",
        "payment_methods": {
            "excluded_payment_types": [
                {"id": "atm"},
                {"id": "ticket"}
            ],
            "installments": 1
        }
    }
    
    try:
        preference_response = sdk.preference().create(preference_data)
        if preference_response["status"] == 201:
            return preference_response["response"]
        else:
            logger.error(f"Error creando preferencia: {preference_response}")
            return None
    except Exception as e:
        logger.error(f"Excepción en MercadoPago: {e}")
        return None

def verificar_pago(payment_id):
    """Verifica el estado de un pago"""
    sdk = init_mercadopago()
    if not sdk:
        return None
    
    try:
        payment_info = sdk.payment().get(payment_id)
        if payment_info["status"] == 200:
            return payment_info["response"]
        return None
    except:
        return None

# --- 6. VALIDACIONES ---
def validar_email(email):
    """Valida formato de email"""
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, email) is not None

def validar_telefono(telefono):
    """Valida teléfono chileno"""
    telefono = re.sub(r'\D', '', telefono)
    patron = r'^(9|2)[0-9]{8}$'
    return re.match(patron, telefono) is not None

def generar_id_unico():
    """Genera ID único para la inscripción"""
    return str(uuid.uuid4()).replace('-', '')[:12].upper()

# --- 7. FORMULARIO DE INSCRIPCIÓN ---
def render_formulario():
    """Renderiza el formulario de inscripción"""
    
    st.markdown('<h1 class="title">🥋 INSCRIPCIÓN TORNEO WKB</h1>', unsafe_allow_html=True)
    
    # Logo y banner
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://inertiax.store/cdn/shop/files/wmremove-transformed-removebg-preview.png", use_container_width=True)
    
    # Información del torneo
    st.markdown("""
    <div class="card">
        <h3 style="color:#FDB931; margin-top:0;">📅 Información del Torneo</h3>
        <p style="color:#e5e7eb;">📍 Fecha: 15-16 Marzo 2025</p>
        <p style="color:#e5e7eb;">🏟️ Lugar: Gimnasio Polideportivo, Santiago</p>
        <p style="color:#e5e7eb;">⏰ Peso: 09:00 hrs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Precio
    st.markdown(f"""
    <div class="price-tag">
        💰 VALOR INSCRIPCIÓN: ${PRECIO_INSCRIPCION:,} CLP
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar estado
    if 'paso' not in st.session_state:
        st.session_state.paso = 'formulario'
    if 'datos_competidor' not in st.session_state:
        st.session_state.datos_competidor = {}
    if 'preferencia_id' not in st.session_state:
        st.session_state.preferencia_id = None
    
    # Flujo de inscripción
    if st.session_state.paso == 'formulario':
        render_paso1()
    elif st.session_state.paso == 'pago':
        render_paso2()
    elif st.session_state.paso == 'confirmacion':
        render_paso3()
    elif st.session_state.paso == 'error':
        render_error()

def render_paso1():
    """Paso 1: Formulario de datos"""
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📝 Datos del Competidor")
    
    with st.form("form_inscripcion"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre Completo *", 
                                  placeholder="Ej: Juan Pérez González")
            edad = st.number_input("Edad *", min_value=18, max_value=99, step=1)
            email = st.text_input("Email *", 
                                 placeholder="ejemplo@correo.com")
        
        with col2:
            dojo = st.text_input("Dojo/Escuela *", 
                                placeholder="Ej: WKB Santiago")
            telefono = st.text_input("Teléfono *", 
                                    placeholder="Ej: 912345678")
            categoria = st.selectbox("Categoría *", CATEGORIAS)
        
        # Términos y condiciones
        st.markdown("---")
        acepta = st.checkbox("Acepto los términos y condiciones del torneo *")
        
        # Botón submit
        submit = st.form_submit_button("CONTINUAR AL PAGO", 
                                       use_container_width=True,
                                       type="primary")
        
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
                # Guardar datos
                st.session_state.datos_competidor = {
                    "nombre": nombre,
                    "edad": edad,
                    "email": email,
                    "dojo": dojo,
                    "telefono": telefono,
                    "categoria": categoria,
                    "id_inscripcion": generar_id_unico(),
                    "fecha_registro": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.paso = 'pago'
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer con información de pago
    st.markdown("""
    <div style="text-align:center; color:#9ca3af; font-size:12px; margin-top:30px;">
        <p>🔒 Pago procesado por MercadoPago</p>
        <p>Aceptamos tarjetas de crédito, débito y transferencia</p>
    </div>
    """, unsafe_allow_html=True)

def render_paso2():
    """Paso 2: Procesar pago"""
    
    datos = st.session_state.datos_competidor
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💳 Confirmar y Pagar")
    
    # Resumen de inscripción
    st.markdown("""
    <style>
        .resumen-item {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid #374151;
        }
        .resumen-label {
            color: #9ca3af;
        }
        .resumen-value {
            color: #FDB931;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="resumen-item">
            <span class="resumen-label">Competidor:</span>
            <span class="resumen-value">{datos['nombre']}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">Categoría:</span>
            <span class="resumen-value">{datos['categoria']}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">Dojo:</span>
            <span class="resumen-value">{datos['dojo']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="resumen-item">
            <span class="resumen-label">Email:</span>
            <span class="resumen-value">{datos['email']}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">Teléfono:</span>
            <span class="resumen-value">{datos['telefono']}</span>
        </div>
        <div class="resumen-item">
            <span class="resumen-label">ID:</span>
            <span class="resumen-value">{datos['id_inscripcion']}</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Total
    st.markdown(f"""
    <div style="background: #111827; padding: 15px; border-radius: 10px; margin: 20px 0;">
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #e5e7eb; font-size: 18px;">Total a pagar:</span>
            <span style="color: #FDB931; font-size: 24px; font-weight: bold;">${PRECIO_INSCRIPCION:,} CLP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← VOLVER", use_container_width=True):
            st.session_state.paso = 'formulario'
            st.rerun()
    
    with col2:
        if st.button("PAGAR AHORA 💳", type="primary", use_container_width=True):
            with st.spinner("Preparando pago..."):
                # Crear preferencia en MercadoPago
                preferencia_id = f"WKB-{datos['id_inscripcion']}-{int(time.time())}"
                
                datos_pago = {
                    "comprador": {
                        "nombre": datos["nombre"],
                        "email": datos["email"],
                        "telefono": datos["telefono"]
                    },
                    "items": {
                        "categoria": datos["categoria"]
                    }
                }
                
                preferencia = crear_preferencia_pago(datos_pago, preferencia_id)
                
                if preferencia and "init_point" in preferencia:
                    # Guardar referencia
                    st.session_state.preferencia_id = preferencia_id
                    
                    # Mostrar link de pago
                    st.markdown(f"""
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{preferencia['init_point']}" target="_blank">
                            <button style="background: #00aaff; color: white; padding: 15px 30px; 
                                         border: none; border-radius: 10px; font-size: 18px; 
                                         font-weight: bold; cursor: pointer;">
                                🔗 HAZ CLIC PARA PAGAR
                            </button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("⚠️ Después de pagar, espera la confirmación automática")
                    
                    # Botón para simular pago (desarrollo)
                    if st.button("✅ SIMULAR PAGO EXITOSO (solo pruebas)", use_container_width=True):
                        st.session_state.paso = 'confirmacion'
                        st.rerun()
                else:
                    st.error("Error al crear el pago. Intenta nuevamente.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_paso3():
    """Paso 3: Confirmación exitosa"""
    
    datos = st.session_state.datos_competidor
    
    # Guardar en sheets
    with st.spinner("Confirmando inscripción..."):
        # Datos para guardar
        registro = {
            "ID_Inscripcion": datos["id_inscripcion"],
            "Fecha_Registro": datos["fecha_registro"],
            "Nombre_Completo": datos["nombre"],
            "Edad": datos["edad"],
            "Email": datos["email"],
            "Telefono": datos["telefono"],
            "Dojo": datos["dojo"],
            "Categoria": datos["categoria"],
            "Estado_Pago": "Confirmado",
            "Monto_Pagado": PRECIO_INSCRIPCION,
            "Metodo_Pago": "MercadoPago",
            "Preferencia_ID": st.session_state.get("preferencia_id", ""),
            "Fecha_Pago": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Guardar en sheets
        if guardar_inscripcion(registro):
            # Guardar también en la hoja de pagos
            pago = {
                "ID_Inscripcion": datos["id_inscripcion"],
                "Nombre": datos["nombre"],
                "Monto": PRECIO_INSCRIPCION,
                "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Estado": "aprobado",
                "Metodo": "MercadoPago"
            }
            guardar_pago(pago)
            
            # Mostrar confirmación
            st.balloons()
            
            st.markdown(f"""
            <div class="success-message">
                <h2>✅ ¡INSCRIPCIÓN CONFIRMADA!</h2>
                <p style="font-size: 18px; margin: 20px 0;">
                    Gracias por inscribirte al Torneo WKB 2025
                </p>
                <div style="background: #0e1117; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <p><strong>ID de Inscripción:</strong> {datos['id_inscripcion']}</p>
                    <p><strong>Competidor:</strong> {datos['nombre']}</p>
                    <p><strong>Categoría:</strong> {datos['categoria']}</p>
                    <p><strong>Dojo:</strong> {datos['dojo']}</p>
                </div>
                <p>Te enviaremos un email con más información a <strong>{datos['email']}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botón para nueva inscripción
            if st.button("📝 NUEVA INSCRIPCIÓN", use_container_width=True):
                # Limpiar estado
                for key in ['paso', 'datos_competidor', 'preferencia_id']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            st.error("Error guardando la inscripción. Contacta al organizador.")
            st.session_state.paso = 'error'
            st.rerun()

def render_error():
    """Muestra error en el proceso"""
    
    st.markdown("""
    <div class="error-message">
        <h2>❌ ERROR EN LA INSCRIPCIÓN</h2>
        <p>Hubo un problema procesando tu inscripción.</p>
        <p>Por favor, intenta nuevamente o contacta a los organizadores.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 INTENTAR NUEVAMENTE", use_container_width=True):
        for key in ['paso', 'datos_competidor', 'preferencia_id']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# --- 8. PANEL ADMIN SIMPLE ---
def render_admin():
    """Panel de administración básico"""
    
    st.markdown('<h1 class="title">⚙️ PANEL ADMIN</h1>', unsafe_allow_html=True)
    
    password = st.text_input("Contraseña", type="password")
    
    if password == "wkbadmin2025":  # Cambiar en producción
        # Cargar datos
        df = cargar_inscripciones()
        
        if not df.empty:
            st.success(f"Total inscripciones: {len(df)}")
            
            # Estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                confirmados = len(df[df['Estado_Pago'] == 'Confirmado'])
                st.metric("✅ Confirmados", confirmados)
            with col2:
                pendientes = len(df[df['Estado_Pago'] != 'Confirmado'])
                st.metric("⏳ Pendientes", pendientes)
            with col3:
                st.metric("💰 Total recaudado", f"${len(df[df['Estado_Pago'] == 'Confirmado']) * PRECIO_INSCRIPCION:,}")
            
            # Mostrar datos
            st.dataframe(df, use_container_width=True)
            
            # Descargar CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Descargar CSV",
                csv,
                "inscripciones_wkb.csv",
                "text/csv"
            )
        else:
            st.info("No hay inscripciones aún")

# --- 9. MAIN ---
def main():
    """Función principal"""
    
    # Parámetros de URL
    query_params = st.query_params
    
    # Verificar retorno de pago
    if "success" in query_params and query_params["success"] == "true":
        if 'paso' in st.session_state and st.session_state.paso == 'pago':
            st.session_state.paso = 'confirmacion'
            st.rerun()
    
    # Navegación
    st.sidebar.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-PCwsXVnqhlX-vNev8BDqbszitBpm3cC8GQ&s", width=100)
    st.sidebar.title("WKB CHILE")
    
    opcion = st.sidebar.radio("Menú", ["📝 Inscripción", "⚙️ Admin"])
    
    if opcion == "📝 Inscripción":
        render_formulario()
    else:
        render_admin()

if __name__ == "__main__":
    main()
