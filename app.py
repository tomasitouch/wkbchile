import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import mercadopago
import plotly.express as px
import plotly.graph_objects as go
import uuid
import time
import random
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB WORLD CUP 2026 | Official Registration & Brackets",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONSTANTES & CONFIGURACIÓN ---
class Config:
    """Configuración centralizada de la aplicación"""
    CODIGO_VIP = "WKB2026"
    LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
    FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
    PRECIO = 15000
    MAX_CAPACIDAD = 500
    WORKSHEET_NAME = "Inscripciones"
    BRACKETS_WORKSHEET = "Brackets"  # Nueva hoja para brackets
    
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

# --- BRACKET MANAGER ---
class BracketManager:
    """Maneja la creación y gestión de brackets de combate"""
    
    def __init__(self, conn):
        self.conn = conn
    
    def get_brackets(self) -> pd.DataFrame:
        """Obtiene los brackets existentes"""
        try:
            return self.conn.read(worksheet=Config.BRACKETS_WORKSHEET, ttl=0)
        except:
            return pd.DataFrame(columns=[
                "Bracket_ID", "Categoria", "Ronda", "Pareja_ID",
                "Competidor1_ID", "Competidor1_Nombre", "Competidor1_Dojo",
                "Competidor2_ID", "Competidor2_Nombre", "Competidor2_Dojo",
                "Ganador_ID", "Estado", "Fecha_Asignacion", "Tatami"
            ])
    
    def check_activation_flag(self, df_inscripciones: pd.DataFrame) -> bool:
        """Verifica si la columna de emparejar está activada"""
        if 'Emparejar' in df_inscripciones.columns:
            # Buscar cualquier celda con "SI" o "ACTIVAR"
            mask = df_inscripciones['Emparejar'].astype(str).str.upper().isin(['SI', 'ACTIVAR', 'TRUE', '1', 'X'])
            return mask.any()
        return False
    
    def clear_activation_flags(self, df_inscripciones: pd.DataFrame) -> pd.DataFrame:
        """Limpia las banderas de activación después de procesar"""
        if 'Emparejar' in df_inscripciones.columns:
            df_inscripciones['Emparejar'] = ''
        return df_inscripciones
    
    def create_brackets(self, df_inscripciones: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, any]]:
        """
        Crea brackets automáticamente por categoría
        Retorna: (DataFrame de brackets, estadísticas)
        """
        
        # Filtrar solo confirmados
        df_conf = df_inscripciones[df_inscripciones['Estado'] == 'CONFIRMADO'].copy()
        
        if df_conf.empty:
            return pd.DataFrame(), {"error": "No hay competidores confirmados"}
        
        brackets_list = []
        stats = {}
        
        # Procesar cada categoría
        for categoria in Config.CATEGORIAS:
            df_cat = df_conf[df_conf['Categoria'] == categoria]
            
            if len(df_cat) < 2:
                stats[categoria] = {
                    "competidores": len(df_cat),
                    "parejas": 0,
                    "estado": "Insuficientes competidores" if len(df_cat) > 0 else "Sin competidores"
                }
                continue
            
            # Mezclar aleatoriamente para brackets justos
            competidores = df_cat.to_dict('records')
            random.shuffle(competidores)
            
            # Calcular número de rondas necesario
            num_competidores = len(competidores)
            num_parejas = num_competidores // 2
            byes = num_competidores % 2
            
            # Crear parejas
            parejas_creadas = 0
            bracket_id = f"BRACKET_{categoria[:10]}_{datetime.now().strftime('%Y%m%d')}"
            
            for i in range(0, len(competidores) - 1, 2):
                if i + 1 < len(competidores):
                    c1 = competidores[i]
                    c2 = competidores[i + 1]
                    
                    # Determinar ronda (simplificado - todos empiezan en Ronda 1)
                    ronda = "Ronda 1"
                    if num_competidores > 8 and i >= 4:
                        ronda = "Ronda 2" if num_competidores <= 16 else "Clasificatoria"
                    
                    pareja_id = f"P{len(brackets_list)+1:03d}"
                    
                    bracket_entry = {
                        "Bracket_ID": bracket_id,
                        "Categoria": categoria,
                        "Ronda": ronda,
                        "Pareja_ID": pareja_id,
                        "Competidor1_ID": c1.get('ID', ''),
                        "Competidor1_Nombre": c1.get('Nombre', ''),
                        "Competidor1_Dojo": c1.get('Dojo', ''),
                        "Competidor2_ID": c2.get('ID', ''),
                        "Competidor2_Nombre": c2.get('Nombre', ''),
                        "Competidor2_Dojo": c2.get('Dojo', ''),
                        "Ganador_ID": "",
                        "Estado": "Pendiente",
                        "Fecha_Asignacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Tatami": f"Tatami {(len(brackets_list) % 3) + 1}"  # Distribuir en tatamis
                    }
                    
                    brackets_list.append(bracket_entry)
                    parejas_creadas += 1
            
            # Guardar estadísticas de la categoría
            stats[categoria] = {
                "competidores": num_competidores,
                "parejas": parejas_creadas,
                "byes": byes,
                "estado": "OK" if parejas_creadas > 0 else "Sin parejas"
            }
        
        # Crear DataFrame final
        df_brackets = pd.DataFrame(brackets_list)
        
        # Si hay un competidor sin pareja (bye), crear entrada especial
        for categoria in Config.CATEGORIAS:
            df_cat = df_conf[df_conf['Categoria'] == categoria]
            if len(df_cat) % 2 == 1:  # Número impar
                # El último competidor recibe bye
                ultimo = df_cat.iloc[-1]
                bye_entry = {
                    "Bracket_ID": f"BYE_{categoria[:10]}",
                    "Categoria": categoria,
                    "Ronda": "Ronda 1",
                    "Pareja_ID": f"BYE{len(brackets_list)+1:03d}",
                    "Competidor1_ID": ultimo.get('ID', ''),
                    "Competidor1_Nombre": ultimo.get('Nombre', ''),
                    "Competidor1_Dojo": ultimo.get('Dojo', ''),
                    "Competidor2_ID": "BYE",
                    "Competidor2_Nombre": "BYE (Descansa)",
                    "Competidor2_Dojo": "-",
                    "Ganador_ID": ultimo.get('ID', ''),
                    "Estado": "Bye - Automático",
                    "Fecha_Asignacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Tatami": "Descansa"
                }
                df_brackets = pd.concat([df_brackets, pd.DataFrame([bye_entry])], ignore_index=True)
        
        return df_brackets, stats
    
    def save_brackets(self, df_brackets: pd.DataFrame) -> bool:
        """Guarda los brackets en Google Sheets"""
        try:
            # Obtener brackets existentes
            df_existente = self.get_brackets()
            
            # Combinar con nuevos brackets (evitar duplicados)
            if not df_existente.empty:
                # Verificar si ya existen brackets para esta fecha
                hoy = datetime.now().strftime("%Y-%m-%d")
                df_hoy = df_existente[df_existente['Fecha_Asignacion'].str.contains(hoy)]
                
                if not df_hoy.empty:
                    # Si ya hay brackets hoy, preguntar si reemplazar
                    return "EXISTEN"
            
            # Guardar nuevos brackets
            self.conn.update(worksheet=Config.BRACKETS_WORKSHEET, data=df_brackets)
            return True
            
        except Exception as e:
            logging.error(f"Error guardando brackets: {str(e)}")
            return False
    
    def get_bracket_tree(self, categoria: str) -> Dict:
        """Construye el árbol de brackets para una categoría"""
        df = self.get_brackets()
        
        if df.empty:
            return {}
        
        df_cat = df[df['Categoria'] == categoria]
        
        # Organizar por rondas
        brackets = {}
        for _, row in df_cat.iterrows():
            ronda = row['Ronda']
            if ronda not in brackets:
                brackets[ronda] = []
            
            brackets[ronda].append({
                'pareja_id': row['Pareja_ID'],
                'competidor1': row['Competidor1_Nombre'],
                'competidor1_dojo': row['Competidor1_Dojo'],
                'competidor2': row['Competidor2_Nombre'],
                'competidor2_dojo': row['Competidor2_Dojo'],
                'ganador': row['Ganador_ID'],
                'estado': row['Estado'],
                'tatami': row['Tatami']
            })
        
        return brackets

# --- DATABASE MANAGER ---
class DatabaseManager:
    """Maneja todas las operaciones con Google Sheets"""
    
    def __init__(self):
        self.conn = st.connection("gsheets", type=GSheetsConnection)
        self.bracket_manager = BracketManager(self.conn)
    
    def get_all(self) -> pd.DataFrame:
        """Obtiene todas las inscripciones"""
        try:
            df = self.conn.read(worksheet=Config.WORKSHEET_NAME, ttl=0)
            if df.empty:
                return pd.DataFrame(columns=[
                    "ID", "Fecha", "Nombre", "Email", "Dojo", "Categoria", 
                    "Telefono", "Edad", "Pais", "Estado", "Metodo", "Notas", "Emparejar"
                ])
            return df
        except Exception as e:
            st.error(f"Error de conexión: {str(e)}")
            return pd.DataFrame()
    
    def update_sheet(self, df: pd.DataFrame) -> bool:
        """Actualiza la hoja de inscripciones"""
        try:
            self.conn.update(worksheet=Config.WORKSHEET_NAME, data=df)
            return True
        except Exception as e:
            logging.error(f"Error actualizando sheet: {str(e)}")
            return False
    
    def check_and_generate_brackets(self) -> Tuple[bool, str, pd.DataFrame, Dict]:
        """
        Verifica si hay bandera de emparejar y genera brackets
        Retorna: (procesado, mensaje, df_brackets, stats)
        """
        df = self.get_all()
        
        if df.empty:
            return False, "No hay datos en la hoja de inscripciones", pd.DataFrame(), {}
        
        # Verificar bandera de emparejar
        if not self.bracket_manager.check_activation_flag(df):
            return False, "No hay solicitud de emparejamiento activa", pd.DataFrame(), {}
        
        # Generar brackets
        df_brackets, stats = self.bracket_manager.create_brackets(df)
        
        if df_brackets.empty:
            return False, "No se pudieron generar brackets", pd.DataFrame(), stats
        
        # Guardar brackets
        save_result = self.bracket_manager.save_brackets(df_brackets)
        
        if save_result == "EXISTEN":
            return False, "Ya existen brackets generados hoy. Limpia la bandera para regenerar.", df_brackets, stats
        elif save_result:
            # Limpiar banderas de activación
            df_limpio = self.bracket_manager.clear_activation_flags(df)
            self.update_sheet(df_limpio)
            
            return True, f"Brackets generados exitosamente para {len(df_brackets)} parejas", df_brackets, stats
        else:
            return False, "Error al guardar brackets", df_brackets, stats

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
            width: min(600px, 95%);
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
        
        /* Bracket Styles */
        .bracket-container {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .bracket-round {
            flex: 1;
            min-width: 250px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            padding: 1rem;
        }
        
        .bracket-match {
            background: rgba(255,43,43,0.1);
            border: 1px solid #ff2b2b;
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 1rem;
            position: relative;
        }
        
        .bracket-match::after {
            content: '';
            position: absolute;
            right: -1rem;
            top: 50%;
            width: 1rem;
            height: 2px;
            background: #ff2b2b;
        }
        
        .bracket-match:last-child::after {
            display: none;
        }
        
        .competitor {
            display: flex;
            justify-content: space-between;
            padding: 0.25rem 0;
            border-bottom: 1px solid #333;
        }
        
        .competitor:last-child {
            border-bottom: none;
        }
        
        .competitor.winner {
            color: #ff2b2b;
            font-weight: bold;
        }
        
        .tatami-badge {
            display: inline-block;
            background: #ff2b2b;
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            margin-top: 0.5rem;
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
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-family: 'Orbitron', monospace !important;
            font-size: 2rem !important;
            color: #ff2b2b !important;
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
            
            .bracket-container {
                flex-direction: column;
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
    def render_brackets(df_brackets: pd.DataFrame, stats: Dict = None):
        """Renderiza los brackets de combate"""
        
        if df_brackets.empty:
            st.info("📊 No hay brackets generados todavía")
            return
        
        # Estadísticas generales
        if stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                total_parejas = len(df_brackets[df_brackets['Competidor2_ID'] != 'BYE'])
                st.metric("Total Parejas", total_parejas)
            with col2:
                categorias_con_parejas = df_brackets['Categoria'].nunique()
                st.metric("Categorías Activas", categorias_con_parejas)
            with col3:
                total_competidores = len(df_brackets['Competidor1_ID'].unique()) + len(df_brackets[df_brackets['Competidor2_ID'] != 'BYE']['Competidor2_ID'].unique())
                st.metric("Competidores", total_competidores)
        
        # Selector de categoría
        categorias_disponibles = df_brackets['Categoria'].unique()
        categoria_seleccionada = st.selectbox(
            "Seleccionar Categoría",
            categorias_disponibles,
            key="bracket_cat_selector"
        )
        
        if categoria_seleccionada:
            df_cat = df_brackets[df_brackets['Categoria'] == categoria_seleccionada]
            
            # Distribución por tatami
            st.markdown(f"### 🥋 Categoría: {categoria_seleccionada}")
            
            tatamis = df_cat['Tatami'].unique()
            tatami_cols = st.columns(len(tatamis))
            
            for idx, tatami in enumerate(sorted(tatamis)):
                with tatami_cols[idx]:
                    df_tatami = df_cat[df_cat['Tatami'] == tatami]
                    st.markdown(f"**{tatami}**")
                    
                    for _, match in df_tatami.iterrows():
                        winner_class = "winner" if match['Ganador_ID'] else ""
                        
                        # Determinar estilo según resultado
                        if match['Competidor2_ID'] == 'BYE':
                            st.markdown(f"""
                            <div class="bracket-match" style="background: rgba(255,215,0,0.1);">
                                <div class="competitor {winner_class if match['Ganador_ID'] == match['Competidor1_ID'] else ''}">
                                    <span>⭐ {match['Competidor1_Nombre']}</span>
                                    <small>{match['Competidor1_Dojo']}</small>
                                </div>
                                <div style="color: #FFD700; text-align: center; font-size: 0.8rem;">
                                    BYE - Avanza directo
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="bracket-match">
                                <div class="competitor {winner_class if match['Ganador_ID'] == match['Competidor1_ID'] else ''}">
                                    <span>⚔️ {match['Competidor1_Nombre']}</span>
                                    <small>{match['Competidor1_Dojo']}</small>
                                </div>
                                <div class="competitor {winner_class if match['Ganador_ID'] == match['Competidor2_ID'] else ''}">
                                    <span>⚔️ {match['Competidor2_Nombre']}</span>
                                    <small>{match['Competidor2_Dojo']}</small>
                                </div>
                                <div style="text-align: center; margin-top: 0.5rem;">
                                    <span class="tatami-badge">{match['Estado']}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            # Tabla de detalles
            with st.expander("Ver detalles de la categoría"):
                df_display = df_cat[['Pareja_ID', 'Ronda', 'Competidor1_Nombre', 'Competidor2_Nombre', 'Tatami', 'Estado']]
                st.dataframe(df_display, use_container_width=True, hide_index=True)

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
        if 'brackets_generated' not in st.session_state:
            st.session_state.brackets_generated = False
    
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
                    WORLD CUP 2026
                </h1>
                <p style="color: #666; letter-spacing: 3px;">SANTIAGO · CHILE</p>
            </div>
            """, unsafe_allow_html=True)
        
        self.ui.render_countdown()
    
    def render_dashboard(self):
        """Renderiza dashboard principal"""
        st.markdown("## 📊 LIVE DASHBOARD")
        
        df = self.db.get_all()
        
        if df.empty:
            st.info("No hay datos disponibles")
            return
        
        df_conf = df[df['Estado'] == 'CONFIRMADO'] if 'Estado' in df.columns else df
        
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Inscritos",
                len(df_conf),
                delta=None
            )
        
        with col2:
            st.metric(
                "Cupos Disponibles",
                Config.MAX_CAPACIDAD - len(df_conf),
                delta=f"{int((len(df_conf)/Config.MAX_CAPACIDAD)*100)}%",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Dojos Representados",
                df_conf['Dojo'].nunique() if not df_conf.empty else 0,
                delta=None
            )
        
        with col4:
            st.metric(
                "Categorías Activas",
                df_conf['Categoria'].nunique() if not df_conf.empty else 0,
                delta=None
            )
        
        # Gráficos
        with st.container():
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 📈 Distribución por Categoría")
            
            if not df_conf.empty and 'Categoria' in df_conf.columns:
                counts = df_conf['Categoria'].value_counts()
                fig = px.bar(
                    x=counts.values,
                    y=counts.index,
                    orientation='h',
                    color=counts.values,
                    color_continuous_scale=['#440000', '#ff2b2b'],
                    labels={'x': 'Inscritos', 'y': ''}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
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
                nombre = st.text_input("Nombre Completo *")
                email = st.text_input("Email *")
                telefono = st.text_input("Teléfono / WhatsApp *")
            
            with col2:
                edad = st.number_input("Edad *", min_value=18, max_value=99, value=18)
                dojo = st.text_input("Dojo / Escuela *")
                pais = st.selectbox("País *", options=Config.PAISES)
            
            categoria = st.selectbox("Categoría *", options=Config.CATEGORIAS)
            
            terminos = st.checkbox("Acepto los términos y condiciones del torneo *")
            
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
                
                if not email or not Utils.validate_email(email):
                    errors.append("❌ Email inválido")
                
                if not telefono or not Utils.validate_phone(telefono):
                    errors.append("❌ Teléfono inválido (mínimo 8 dígitos)")
                
                if not dojo:
                    errors.append("❌ El dojo es obligatorio")
                
                if not terminos:
                    errors.append("❌ Debes aceptar los términos")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
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
        data = st.session_state.tmp_data
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
                st.error("Error en sistema de pagos")
        
        st.markdown("---")
        st.markdown("### 🎟️ CÓDIGO DE INVITACIÓN")
        
        with st.expander("¿Tienes un código VIP?"):
            vip_code = st.text_input("Ingresa tu código", type="password", key="vip_code_input")
            
            if st.button("VALIDAR CÓDIGO", use_container_width=True):
                if vip_code == Config.CODIGO_VIP:
                    with st.spinner("Procesando..."):
                        if self.db.save_registration(st.session_state.tmp_data, "VIP"):
                            st.balloons()
                            st.success("✅ ¡Código válido! Inscripción confirmada.")
                            st.session_state.tmp_data = {}
                            st.session_state.step = 1
                            time.sleep(2)
                            st.rerun()
                else:
                    st.error("❌ Código inválido")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_brackets_tab(self):
        """Renderiza la pestaña de brackets"""
        st.markdown("## 🏆 BRACKETS DE COMBATE")
        
        # Verificar generación automática
        procesado, mensaje, df_brackets, stats = self.db.check_and_generate_brackets()
        
        if procesado:
            st.balloons()
            st.success(f"✅ {mensaje}")
            st.session_state.brackets_generated = True
            self.ui.render_brackets(df_brackets, stats)
        elif mensaje and not procesado:
            if "No hay solicitud" not in mensaje:
                st.warning(f"ℹ️ {mensaje}")
            
            # Mostrar brackets existentes
            df_existentes = self.db.bracket_manager.get_brackets()
            if not df_existentes.empty:
                self.ui.render_brackets(df_existentes)
            else:
                if "No hay solicitud" in mensaje:
                    st.info("Para generar brackets, agrega una columna 'Emparejar' en el Excel y escribe 'SI' en cualquier celda")
                    
                    # Mostrar ejemplo
                    with st.expander("📋 Ver ejemplo de configuración"):
                        st.markdown("""
                        **Para activar el emparejamiento:**
                        
                        1. En tu hoja de Google Sheets, agrega una columna llamada **`Emparejar`**
                        2. En cualquier celda de esa columna, escribe **`SI`** o **`ACTIVAR`**
                        3. La aplicación detectará automáticamente la solicitud
                        4. Se generarán los brackets y se limpiará la bandera
                        
                        ![Ejemplo](https://via.placeholder.com/400x100?text=Columna+Emparejar+con+SI)
                        """)
    
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
            tabs = st.tabs(["📋 Inscripciones", "🏆 Brackets", "⚙️ Configuración"])
            
            with tabs[0]:
                df = self.db.get_all()
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Exportar
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 DESCARGAR CSV",
                        csv,
                        "wkb_inscripciones.csv",
                        "text/csv",
                        use_container_width=True
                    )
                else:
                    st.info("No hay datos")
            
            with tabs[1]:
                df_brackets = self.db.bracket_manager.get_brackets()
                
                if not df_brackets.empty:
                    st.dataframe(df_brackets, use_container_width=True, hide_index=True)
                    
                    # Exportar brackets
                    csv_brackets = df_brackets.to_csv(index=False)
                    st.download_button(
                        "📥 DESCARGAR BRACKETS",
                        csv_brackets,
                        "wkb_brackets.csv",
                        "text/csv",
                        use_container_width=True
                    )
                    
                    # Botón para limpiar brackets
                    if st.button("🗑️ LIMPIAR BRACKETS", use_container_width=True):
                        if st.checkbox("Confirmar limpieza"):
                            df_vacio = pd.DataFrame(columns=df_brackets.columns)
                            self.db.bracket_manager.save_brackets(df_vacio)
                            st.success("Brackets eliminados")
                            st.rerun()
                else:
                    st.info("No hay brackets generados")
            
            with tabs[2]:
                st.markdown("### Configuración de Emparejamiento")
                st.markdown("""
                **Instrucciones:**
                
                1. **Agregar columna 'Emparejar'** en tu hoja de Google Sheets
                2. **Escribir 'SI'** en cualquier celda para activar la generación
                3. **Los brackets** se crearán automáticamente en la hoja 'Brackets'
                4. **La bandera** se limpiará automáticamente después de generar
                
                **Formato de la columna:**
                - `SI` o `ACTIVAR` - Genera brackets
                - `NO` o vacío - No hace nada
                - `FORCE` - Fuerza regeneración aunque existan brackets
                """)
        
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
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 DASHBOARD", 
            "📝 REGISTRO", 
            "🏆 BRACKETS", 
            "⚙️ ADMIN"
        ])
        
        with tab1:
            self.render_dashboard()
        
        with tab2:
            self.render_registration()
        
        with tab3:
            self.render_brackets_tab()
        
        with tab4:
            self.render_admin()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align:center; color:#666; padding:2rem 0;">
            <p>© 2024 World Kyokushin Budokai Chile. Todos los derechos reservados.</p>
            <p style="font-size:0.8rem;">Versión 3.0.0 | Sistema de Inscripciones y Brackets</p>
        </div>
        """, unsafe_allow_html=True)

# --- ENTRY POINT ---
if __name__ == "__main__":
    app = WKBApp()
    app.run()

