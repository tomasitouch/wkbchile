import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import plotly.express as px
import plotly.graph_objects as go
import uuid
import time
from datetime import datetime, timedelta
import hashlib
import re
from typing import Optional, Dict, Any
import logging

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB ALL AMERICAN 2026 | Official Registration",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CONSTANTES & CONFIGURACIÓN ---
class Config:
    """Configuración centralizada de la aplicación"""
    CODIGO_VIP = "WKB2026"
    LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
    FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
    PRECIO = 250
    MAX_CAPACIDAD = 500
    WORKSHEET_NAME = "Inscripciones"
    
    CATEGORIAS = [
        "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
        "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
        "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
        "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
    ]
    
    PAISES = ["Chile", "Argentina", "Perú", "Brasil", "Uruguay", "Paraguay", 
              "Bolivia", "Ecuador", "Colombia", "Venezuela", "Otro"]

# --- UTILITIES ---
class Utils:
    """Funciones utilitarias"""
    
    @staticmethod
    def hash_id(text: str) -> str:
        """Genera un ID único basado en hash"""
        return hashlib.md5(text.encode()).hexdigest()[:8].upper()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de teléfono (básico)"""
        phone = re.sub(r'\D', '', phone)
        return len(phone) >= 8
    
    @staticmethod
    def format_currency(amount: int) -> str:
        """Formatea moneda CLP"""
        return f"${amount:,.0f}".replace(",", ".")
    
    @staticmethod
    def get_time_remaining() -> Dict[str, int]:
        """Calcula tiempo restante para el torneo"""
        delta = Config.FECHA_TORNEO - datetime.now()
        dias = delta.days
        horas, resto = divmod(delta.seconds, 3600)
        minutos, segundos = divmod(resto, 60)
        return {"dias": dias, "horas": horas, "minutos": minutos, "segundos": segundos}

# --- DATABASE MANAGER ---
class DatabaseManager:
    """Maneja todas las operaciones con Google Sheets"""
    
    def __init__(self):
        self.conn = st.connection("gsheets", type=GSheetsConnection)
    
    def get_all(self) -> pd.DataFrame:
        """Obtiene todas las inscripciones"""
        try:
            df = self.conn.read(worksheet=Config.WORKSHEET_NAME, ttl=0)
            if df.empty:
                return pd.DataFrame(columns=[
                    "ID", "Fecha", "Nombre", "Email", "Dojo", "Categoria", 
                    "Telefono", "Edad", "Pais", "Estado", "Metodo", "Notas"
                ])
            return df
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
            return pd.DataFrame()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas rápidas"""
        df = self.get_all()
        if df.empty:
            return {"total": 0, "confirmados": 0, "dojos": 0, "categorias": 0}
        
        df_conf = df[df['Estado'] == 'CONFIRMADO'] if 'Estado' in df.columns else df
        
        return {
            "total": len(df),
            "confirmados": len(df_conf),
            "dojos": df_conf['Dojo'].nunique() if not df_conf.empty else 0,
            "categorias": df_conf['Categoria'].nunique() if not df_conf.empty else 0,
            "disponibles": Config.MAX_CAPACIDAD - len(df_conf)
        }
    
    def check_duplicate(self, email: str, nombre: str) -> bool:
        """Verifica si ya existe un registro similar"""
        df = self.get_all()
        if df.empty:
            return False
        
        # Verificar por email o nombre + fecha reciente
        email_exists = email in df['Email'].values if 'Email' in df.columns else False
        
        if email_exists:
            return True
        
        # Verificar inscripciones recientes con mismo nombre (última hora)
        if 'Nombre' in df.columns and 'Fecha' in df.columns:
            nombre_match = df[df['Nombre'].str.lower() == nombre.lower()]
            if not nombre_match.empty:
                # Verificar si alguna es de las últimas 24 horas
                try:
                    fechas = pd.to_datetime(nombre_match['Fecha'])
                    hace_24h = datetime.now() - timedelta(hours=24)
                    if any(fechas > hace_24h):
                        return True
                except:
                    pass
        
        return False
    
    def save_registration(self, datos: Dict[str, Any], metodo: str) -> bool:
        """Guarda una nueva inscripción"""
        try:
            df_existente = self.get_all()
            
            # Verificar duplicados
            if not df_existente.empty and datos['id'] in df_existente['ID'].values:
                return True
            
            nueva_fila = pd.DataFrame([{
                "ID": datos['id'],
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nombre": datos['nombre'].upper(),
                "Email": datos['email'].lower(),
                "Dojo": datos['dojo'].upper(),
                "Categoria": datos['categoria'],
                "Telefono": datos['telefono'],
                "Edad": datos['edad'],
                "Pais": datos.get('pais', 'Chile'),
                "Estado": "CONFIRMADO",
                "Metodo": metodo,
                "Notas": datos.get('notas', '')
            }])
            
            df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
            self.conn.update(worksheet=Config.WORKSHEET_NAME, data=df_final)
            
            # Logging
            logging.info(f"Registro guardado: {datos['id']} - {metodo}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error guardando registro: {str(e)}")
            st.error(f"Error en base de datos: {str(e)}")
            return False

# --- PAYMENT MANAGER ---
class PaymentManager:
    """Maneja integración con MercadoPago"""
    
    def __init__(self):
        try:
            self.sdk = mercadopago.SDK(st.secrets["mercadopago"]["access_token"])
        except Exception as e:
            logging.error(f"Error inicializando MercadoPago: {str(e)}")
            self.sdk = None
    
    def create_preference(self, datos: Dict[str, Any]) -> Optional[str]:
        """Crea una preferencia de pago"""
        if not self.sdk:
            return None
        
        try:
            base_url = st.secrets["general"].get("public_url", "https://wkb2026.streamlit.app")
            
            preference_data = {
                "items": [{
                    "title": f"WKB 2026: {datos['categoria']}",
                    "quantity": 1,
                    "currency_id": "CLP",
                    "unit_price": Config.PRECIO,
                    "description": f"Inscripción {datos['nombre']} - {datos['dojo']}"
                }],
                "payer": {
                    "email": datos['email'],
                    "name": datos['nombre'].split()[0] if datos['nombre'] else "",
                    "surname": " ".join(datos['nombre'].split()[1:]) if len(datos['nombre'].split()) > 1 else ""
                },
                "back_urls": {
                    "success": f"{base_url}?status=approved",
                    "failure": f"{base_url}?status=failure",
                    "pending": f"{base_url}?status=pending"
                },
                "auto_return": "approved",
                "external_reference": datos['id'],
                "statement_descriptor": "WKB CHILE 2026",
                "payment_methods": {
                    "excluded_payment_types": [],
                    "installments": 6
                }
            }
            
            preference = self.sdk.preference().create(preference_data)
            
            if preference["status"] == 201:
                return preference["response"]["init_point"]
            else:
                logging.error(f"Error MP: {preference}")
                return None
                
        except Exception as e:
            logging.error(f"Error creando preferencia: {str(e)}")
            return None

# --- UI COMPONENTS ---
class UIComponents:
    """Componentes de UI reutilizables"""
    
    @staticmethod
    def apply_custom_css():
        """Aplica CSS personalizado"""
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');
        
        /* Base Styles */
        .stApp {
            background: linear-gradient(135deg, #0a0c10 0%, #1a1c24 100%);
            background-attachment: fixed;
        }
        
        h1, h2, h3, h4 {
            font-family: 'Orbitron', sans-serif !important;
            color: #fff;
            text-shadow: 0 0 10px rgba(255, 43, 43, 0.3);
            letter-spacing: 1px;
        }
        
        /* Glassmorphism Cards */
        .glass-card {
            background: rgba(20, 22, 30, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-left: 4px solid #ff2b2b;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transition: transform 0.3s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-2px);
        }
        
        /* Logo Container */
        .logo-container {
            text-align: center;
            padding: 1rem 0;
            position: relative;
        }
        
        .logo-container img {
            width: min(550px, 89%);
            filter: drop-shadow(0 0 20px rgba(255, 43, 43, 0.2));
            transition: filter 0.3s;
        }
        
        .logo-container img:hover {
            filter: drop-shadow(0 0 30px rgba(255, 43, 43, 0.4));
        }
        
        /* Countdown */
        .countdown-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .countdown-item {
            background: linear-gradient(145deg, #1e2028, #14161e);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 1px solid #333;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);
        }
        
        .countdown-value {
            font-family: 'Orbitron', monospace;
            font-size: clamp(1.5rem, 4vw, 2.5rem);
            font-weight: 900;
            color: #ff2b2b;
            line-height: 1;
        }
        
        .countdown-label {
            font-family: 'Rajdhani', sans-serif;
            font-size: 0.8rem;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, #8b0000 0%, #ff2b2b 100%);
            color: white !important;
            font-family: 'Orbitron', sans-serif !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            letter-spacing: 1px !important;
            transition: all 0.3s !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        .stButton > button:hover {
            box-shadow: 0 0 20px rgba(255, 43, 43, 0.5);
            transform: scale(1.02);
        }
        
        /* Inputs */
        .stTextInput > div > div, .stNumberInput > div > div, .stSelectbox > div > div {
            background-color: #1e2028 !important;
            border: 1px solid #333 !important;
            border-radius: 8px !important;
            color: white !important;
        }
        
        .stTextInput > label, .stNumberInput > label, .stSelectbox > label {
            color: #aaa !important;
            font-family: 'Rajdhani', sans-serif !important;
            font-size: 0.9rem !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-family: 'Orbitron', monospace !important;
            font-size: 2rem !important;
            color: #ff2b2b !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-family: 'Rajdhani', sans-serif !important;
            color: #aaa !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: rgba(20, 22, 30, 0.5);
            padding: 0.5rem;
            border-radius: 12px;
        }
        
        .stTabs [data-baseweb="tab"] {
            font-family: 'Orbitron', sans-serif !important;
            color: #fff !important;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .countdown-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .glass-card {
                padding: 1rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_countdown():
        """Renderiza cuenta regresiva"""
        tiempo = Utils.get_time_remaining()
        
        st.markdown(f"""
        <div class="countdown-grid">
            <div class="countdown-item">
                <div class="countdown-value">{tiempo['dias']}</div>
                <div class="countdown-label">DÍAS</div>
            </div>
            <div class="countdown-item">
                <div class="countdown-value">{tiempo['horas']}</div>
                <div class="countdown-label">HORAS</div>
            </div>
            <div class="countdown-item">
                <div class="countdown-value">{tiempo['minutos']}</div>
                <div class="countdown-label">MINUTOS</div>
            </div>
            <div class="countdown-item">
                <div class="countdown-value">{tiempo['segundos']}</div>
                <div class="countdown-label">SEGUNDOS</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_charts(df: pd.DataFrame):
        """Renderiza gráficos interactivos"""
        if df.empty:
            st.info("📊 No hay datos suficientes para mostrar estadísticas")
            return
        
        df_conf = df[df['Estado'] == 'CONFIRMADO'] if 'Estado' in df.columns else df
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de distribución por categoría
            if 'Categoria' in df_conf.columns:
                counts = df_conf['Categoria'].value_counts().head(8)
                fig = go.Figure(data=[
                    go.Bar(
                        x=counts.values,
                        y=counts.index,
                        orientation='h',
                        marker=dict(
                            color=counts.values,
                            colorscale='Reds',
                            showscale=True,
                            colorbar=dict(title="Inscritos")
                        ),
                        text=counts.values,
                        textposition='outside',
                        hovertemplate='<b>%{y}</b><br>Inscritos: %{x}<extra></extra>'
                    )
                ])
                
                fig.update_layout(
                    title="Distribución por Categoría",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Rajdhani'),
                    xaxis=dict(showgrid=False, color='#888'),
                    yaxis=dict(showgrid=False, color='#fff'),
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de evolución temporal
            if 'Fecha' in df_conf.columns:
                try:
                    df_fechas = df_conf.copy()
                    df_fechas['Fecha'] = pd.to_datetime(df_fechas['Fecha'])
                    df_fechas = df_fechas.set_index('Fecha').resample('D').size().reset_index()
                    df_fechas.columns = ['Fecha', 'Inscritos']
                    df_fechas['Acumulado'] = df_fechas['Inscritos'].cumsum()
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=df_fechas['Fecha'],
                        y=df_fechas['Acumulado'],
                        mode='lines+markers',
                        name='Acumulado',
                        line=dict(color='#ff2b2b', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(255,43,43,0.1)'
                    ))
                    
                    fig.update_layout(
                        title="Evolución de Inscripciones",
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', family='Rajdhani'),
                        xaxis=dict(showgrid=False, color='#888'),
                        yaxis=dict(showgrid=False, color='#fff'),
                        height=400,
                        margin=dict(l=0, r=0, t=40, b=0)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.warning("No hay suficientes datos históricos")
    
    @staticmethod
    def render_payment_summary(data: Dict[str, Any]):
        """Renderiza resumen de pago"""
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, #1e2028, #14161e); 
                    border-radius: 12px; 
                    padding: 1.5rem; 
                    margin: 1rem 0;
                    border: 1px solid #333;">
            <h4 style="margin:0 0 0.5rem 0; color:#ff2b2b;">{data['nombre']}</h4>
            <p style="margin:0; color:#888;">{data['categoria']}</p>
            <p style="margin:0; color:#888;">{data['dojo']}</p>
            <div style="margin-top:1rem; padding-top:1rem; border-top:1px solid #333;">
                <span style="color:#aaa;">Total a pagar:</span>
                <span style="float:right; font-family:'Orbitron'; font-size:1.5rem; color:#ff2b2b;">
                    {Utils.format_currency(Config.PRECIO)}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- MAIN APP ---
class WKBApp:
    """Clase principal de la aplicación"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.payment = PaymentManager()
        self.ui = UIComponents()
        
        # Inicializar estado de sesión
        if 'step' not in st.session_state:
            st.session_state.step = 1
        if 'tmp_data' not in st.session_state:
            st.session_state.tmp_data = {}
    
    def handle_payment_callback(self):
        """Maneja callbacks de pago"""
        if "status" in st.query_params:
            status = st.query_params["status"]
            
            if status == "approved" and st.session_state.tmp_data:
                with st.spinner("Procesando pago..."):
                    if self.db.save_registration(st.session_state.tmp_data, "MercadoPago"):
                        st.balloons()
                        st.success("✅ Pago aprobado. ¡Inscripción confirmada!")
                        
                        # Limpiar sesión
                        st.session_state.tmp_data = {}
                        st.session_state.step = 1
                        st.query_params.clear()
                        
                        time.sleep(2)
                        st.rerun()
            
            elif status == "failure":
                st.error("❌ El pago no pudo ser completado. Intenta nuevamente.")
                st.query_params.clear()
    
    def render_header(self):
        """Renderiza header principal"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f"""
            <div class="logo-container">
                <img src="{Config.LOGO_URL}" alt="WKB Logo">
                <h1 style="font-size: clamp(1.5rem, 5vw, 3rem); 
                           margin: 0.5rem 0 0 0;
                           background: linear-gradient(45deg, #fff, #ff2b2b);
                           -webkit-background-clip: text;
                           -webkit-text-fill-color: transparent;">
                    ALL AMERICAN 2026
                </h1>
                <p style="color: #666; letter-spacing: 3px;">SANTIAGO · CHILE</p>
            </div>
            """, unsafe_allow_html=True)
        
        self.ui.render_countdown()
    
    def render_dashboard(self):
        """Renderiza dashboard principal"""
        st.markdown("## 📊 LIVE DASHBOARD")
        
        stats = self.db.get_stats()
        df = self.db.get_all()
        
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Inscritos",
                stats['confirmados'],
                delta=None
            )
        
        with col2:
            st.metric(
                "Cupos Disponibles",
                stats['disponibles'],
                delta=f"{int((stats['confirmados']/Config.MAX_CAPACIDAD)*100)}%",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Dojos Representados",
                stats['dojos'],
                delta=None
            )
        
        with col4:
            st.metric(
                "Categorías Activas",
                stats['categorias'],
                delta=None
            )
        
        # Gráficos
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            self.ui.render_charts(df)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Información de premios
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 🏆 PREMIOS")
            
            premios = [
                ("🥇 1er Lugar", "Medalla de Oro + Copa + Trofeo"),
                ("🥈 2do Lugar", "Medalla de Plata + Copa"),
                ("🥉 3er Lugar", "Medalla de Bronce")
            ]
            
            for premio, desc in premios:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; 
                            padding:0.75rem; border-bottom:1px solid #333;">
                    <span style="color:#ff2b2b; font-weight:bold;">{premio}</span>
                    <span style="color:#aaa;">{desc}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### ⏰ HORARIOS")
            
            horarios = [
                ("08:00 - 09:00", "Acreditación"),
                ("09:00 - 10:00", "Ceremonia de Apertura"),
                ("10:00 - 13:00", "Eliminatorias Kumite"),
                ("13:00 - 14:00", "Almuerzo"),
                ("14:00 - 17:00", "Finales Kumite"),
                ("17:00 - 18:00", "Competencia Kata"),
                ("18:00 - 19:00", "Premiación")
            ]
            
            for hora, evento in horarios:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; 
                            padding:0.5rem; border-bottom:1px solid #333;">
                    <span style="color:#ff2b2b;">{hora}</span>
                    <span style="color:#aaa;">{evento}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_registration(self):
        """Renderiza formulario de registro"""
        st.markdown("## 📝 REGISTRATION PORTAL")
        
        if st.session_state.step == 1:
            self.render_form_step1()
        else:
            self.render_form_step2()
    
    def render_form_step1(self):
        """Paso 1: Datos personales"""
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### DATOS DEL COMPETIDOR")
        
        with st.form("registration_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input(
                    "Nombre Completo *",
                    help="Ingresa tu nombre tal como aparece en tu documento"
                )
                email = st.text_input(
                    "Email *",
                    help="Correo electrónico para confirmación"
                )
                telefono = st.text_input(
                    "Teléfono / WhatsApp *",
                    help="Incluye código de país (ej: +56 9 1234 5678)"
                )
            
            with col2:
                edad = st.number_input(
                    "Edad *",
                    min_value=18,
                    max_value=99,
                    value=18
                )
                dojo = st.text_input(
                    "Dojo / Escuela *",
                    help="Nombre de tu escuela o gimnasio"
                )
                pais = st.selectbox(
                    "País *",
                    options=Config.PAISES
                )
            
            categoria = st.selectbox(
                "Categoría *",
                options=Config.CATEGORIAS,
                help="Selecciona la categoría en la que deseas competir"
            )
            
            terminos = st.checkbox(
                "Acepto los términos y condiciones del torneo *",
                help="Debes aceptar para continuar"
            )
            
            st.markdown("---")
            submitted = st.form_submit_button(
                "CONTINUAR AL PAGO",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validaciones
                errors = []
                
                if not nombre:
                    errors.append("❌ El nombre es obligatorio")
                elif len(nombre.split()) < 2:
                    errors.append("❌ Ingresa nombre y apellido")
                
                if not email:
                    errors.append("❌ El email es obligatorio")
                elif not Utils.validate_email(email):
                    errors.append("❌ Formato de email inválido")
                
                if not telefono:
                    errors.append("❌ El teléfono es obligatorio")
                elif not Utils.validate_phone(telefono):
                    errors.append("❌ El teléfono debe tener al menos 8 dígitos")
                
                if not dojo:
                    errors.append("❌ El dojo es obligatorio")
                
                if not terminos:
                    errors.append("❌ Debes aceptar los términos y condiciones")
                
                # Verificar duplicados
                if self.db.check_duplicate(email, nombre):
                    errors.append("❌ Ya existe un registro con estos datos")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Guardar datos temporales
                    st.session_state.tmp_data = {
                        "id": Utils.hash_id(f"{nombre}{email}{datetime.now()}"),
                        "nombre": nombre.strip(),
                        "email": email.lower().strip(),
                        "telefono": telefono.strip(),
                        "edad": edad,
                        "dojo": dojo.strip(),
                        "pais": pais,
                        "categoria": categoria
                    }
                    
                    st.session_state.step = 2
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_form_step2(self):
        """Paso 2: Confirmación y pago"""
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🔐 CONFIRMAR INSCRIPCIÓN")
        
        # Mostrar resumen
        self.ui.render_payment_summary(st.session_state.tmp_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("← EDITAR DATOS", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
        
        with col2:
            # Pago con MercadoPago
            link = self.payment.create_preference(st.session_state.tmp_data)
            if link:
                st.markdown(f"""
                <a href="{link}" target="_blank">
                    <button style="width:100%; background:linear-gradient(90deg, #00aaff, #0066cc); 
                                  color:white; border:none; padding:0.75rem; border-radius:8px;
                                  font-family:Orbitron; font-weight:bold; cursor:pointer;">
                        💳 PAGAR CON MERCADOPAGO
                    </button>
                </a>
                """, unsafe_allow_html=True)
            else:
                st.error("Error en sistema de pagos. Intenta más tarde.")
        
        st.markdown("---")
        st.markdown("### 🎟️ CÓDIGO DE INVITACIÓN")
        
        with st.expander("¿Tienes un código VIP?"):
            vip_code = st.text_input(
                "Ingresa tu código",
                type="password",
                key="vip_code_input"
            )
            
            if st.button("VALIDAR CÓDIGO", use_container_width=True):
                if vip_code == Config.CODIGO_VIP:
                    with st.spinner("Procesando..."):
                        if self.db.save_registration(st.session_state.tmp_data, "VIP"):
                            st.balloons()
                            st.success("✅ ¡Código válido! Inscripción confirmada.")
                            
                            # Limpiar sesión
                            st.session_state.tmp_data = {}
                            st.session_state.step = 1
                            
                            time.sleep(2)
                            st.rerun()
                else:
                    st.error("❌ Código inválido")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_admin(self):
        """Panel de administración"""
        st.markdown("## ⚙️ ADMIN PANEL")
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        # Autenticación
        password = st.text_input(
            "Contraseña de administrador",
            type="password",
            key="admin_password"
        )
        
        admin_password = st.secrets["general"].get("admin_password", "admin123")
        
        if password == admin_password:
            df = self.db.get_all()
            
            if not df.empty:
                # Métricas rápidas
                stats = self.db.get_stats()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Registros", stats['total'])
                with col2:
                    st.metric("Confirmados", stats['confirmados'])
                with col3:
                    st.metric("Pendientes", stats['total'] - stats['confirmados'])
                
                # Filtros
                st.markdown("### Filtros")
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'Categoria' in df.columns:
                        categorias = ["Todas"] + list(df['Categoria'].unique())
                        filtro_cat = st.selectbox("Categoría", categorias)
                
                with col2:
                    if 'Estado' in df.columns:
                        estados = ["Todos"] + list(df['Estado'].unique())
                        filtro_estado = st.selectbox("Estado", estados)
                
                # Aplicar filtros
                df_filtered = df.copy()
                
                if filtro_cat != "Todas":
                    df_filtered = df_filtered[df_filtered['Categoria'] == filtro_cat]
                
                if filtro_estado != "Todos":
                    df_filtered = df_filtered[df_filtered['Estado'] == filtro_estado]
                
                # Mostrar datos
                st.markdown("### Datos")
                st.dataframe(
                    df_filtered,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.TextColumn("ID", width="small"),
                        "Fecha": st.column_config.DatetimeColumn("Fecha", width="medium"),
                        "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                        "Email": st.column_config.TextColumn("Email", width="medium"),
                        "Telefono": st.column_config.TextColumn("Teléfono", width="small"),
                        "Dojo": st.column_config.TextColumn("Dojo", width="small"),
                        "Categoria": st.column_config.TextColumn("Categoría", width="medium"),
                        "Pais": st.column_config.TextColumn("País", width="small"),
                        "Estado": st.column_config.TextColumn("Estado", width="small"),
                        "Metodo": st.column_config.TextColumn("Método", width="small")
                    }
                )
                
                # Exportar
                st.markdown("### Exportar")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = df_filtered.to_csv(index=False)
                    st.download_button(
                        "📥 DESCARGAR CSV",
                        csv,
                        "wkb_inscripciones.csv",
                        "text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    json_str = df_filtered.to_json(orient='records', indent=2)
                    st.download_button(
                        "📥 DESCARGAR JSON",
                        json_str,
                        "wkb_inscripciones.json",
                        "application/json",
                        use_container_width=True
                    )
            else:
                st.info("No hay datos registrados")
        
        elif password:
            st.error("Contraseña incorrecta")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def run(self):
        """Ejecuta la aplicación"""
        # Aplicar CSS
        self.ui.apply_custom_css()
        
        # Manejar callback de pago
        self.handle_payment_callback()
        
        # Renderizar header
        self.render_header()
        
        # Tabs principales
        tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📝 REGISTRO", "⚙️ ADMIN"])
        
        with tab1:
            self.render_dashboard()
        
        with tab2:
            self.render_registration()
        
        with tab3:
            self.render_admin()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; color:#666; padding:2rem 0;">
            <p>© 2024 World Kyokushin Budokai Chile. Todos los derechos reservados.</p>
            <p style="font-size:0.8rem;">Versión 2.0.0 | Sistema de Inscripciones Oficial</p>
        </div>
        """, unsafe_allow_html=True)

# --- ENTRY POINT ---
if __name__ == "__main__":
    app = WKBApp()
    app.run()

