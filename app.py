import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import random
import math
import time
from datetime import datetime
import re
import numpy as np
import mercadopago
import uuid

# === CONFIGURACIÓN DE PÁGINA ===
st.set_page_config(
    page_title="WKB WORLD CUP 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === CONFIGURACIÓN MERCADO PAGO ===
# Usar st.secrets para las credenciales (más seguro)
MP_ACCESS_TOKEN = st.secrets["mercadopago"]["access_token"] if "mercadopago" in st.secrets else "TEST-788682177400179-021617-ff69935464f7d4fd77ad130c71ce3b30-1459379017"
MP_PUBLIC_KEY = st.secrets["mercadopago"]["public_key"] if "mercadopago" in st.secrets else "TEST-35348a6a-46c2-4baa-9c50-88e806f56f47"

# Inicializar SDK
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# === CONSTANTES ===
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
PRECIO = 15000
PRECIO_GRUPAL = 14000
FECHA_TORNEO = datetime(2026, 4, 24, 9, 0, 0)
CODIGO_VIP = "WKB2026"

CATEGORIAS = [
    "KUMITE -65kg (18+)", "KUMITE -70kg (18+)", "KUMITE -75kg (18+)",
    "KUMITE -80kg (18+)", "KUMITE -90kg (18+)", "KUMITE +90kg (18+)",
    "KUMITE -55kg (18+) Femenino", "KUMITE -60kg (18+) Femenino",
    "KUMITE +65kg (18+) Femenino", "KATA (18+) Mixto"
]

PAISES = ["Chile", "Argentina", "Perú", "Brasil", "Uruguay", "Paraguay", 
          "Bolivia", "Ecuador", "Colombia", "Venezuela", "Otro"]

# === FUNCIONES DE UTILIDAD ===
def generar_id(nombre, email):
    texto = f"{nombre}{email}{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

def generar_id_grupal():
    texto = f"GRUPO_{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

def generar_referencia_pago():
    """Genera una referencia única para el pago"""
    return f"WKB-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

def validar_email(email):
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None

def formatear_peso(valor):
    return f"${valor:,.0f}".replace(",", ".")

def tiempo_restante():
    delta = FECHA_TORNEO - datetime.now()
    dias = delta.days
    horas, resto = divmod(delta.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return dias, horas, minutos, segundos

def verificar_admin(password):
    try:
        return hashlib.sha256(password.encode()).hexdigest() == st.secrets["general"]["admin_token_hash"]
    except:
        return password == "admin123"

# === FUNCIONES DE GOOGLE SHEETS ===
@st.cache_data(ttl=5)
def leer_inscripciones():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Inscripciones", ttl=0)
        df = df.fillna("")
        if df.empty:
            return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo", "Grupo_ID", "Pago_ID", "Pago_Estado"])
        return df
    except Exception as e:
        st.error(f"Error leyendo inscripciones: {e}")
        return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo", "Grupo_ID", "Pago_ID", "Pago_Estado"])

def guardar_inscripcion(datos):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            df_existente = leer_inscripciones()
        except:
            df_existente = pd.DataFrame()
        
        nueva_fila = pd.DataFrame([{
            "ID": datos['id'],
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nombre": datos['nombre'].upper(),
            "Email": datos['email'].lower(),
            "Telefono": datos['telefono'],
            "Edad": datos['edad'],
            "Dojo": datos['dojo'].upper(),
            "Pais": datos['pais'],
            "Categoria": datos['categoria'],
            "Estado": datos['estado'],
            "Metodo": datos['metodo'],
            "Grupo_ID": datos.get('grupo_id', ''),
            "Pago_ID": datos.get('pago_id', ''),
            "Pago_Estado": datos.get('pago_estado', '')
        }])
        
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error guardando inscripción: {e}")
        return False

def guardar_inscripciones_masivas(df_nuevas):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            df_existente = leer_inscripciones()
        except:
            df_existente = pd.DataFrame()
        
        df_final = pd.concat([df_existente, df_nuevas], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except Exception as e:
        st.error(f"Error guardando inscripciones masivas: {e}")
        return False

@st.cache_data(ttl=5)
def leer_brackets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Brackets", ttl=0)
        df = df.fillna("")
        if df.empty:
            return pd.DataFrame(columns=[
                "Categoria", "Ronda", "Partido_ID", "Competidor1_Nombre", 
                "Dojo1", "Competidor2_Nombre", "Dojo2", "Ganador_Nombre", 
                "Posicion", "Total_Rondas", "Estado"
            ])
        return df
    except Exception as e:
        return pd.DataFrame(columns=[
            "Categoria", "Ronda", "Partido_ID", "Competidor1_Nombre", 
            "Dojo1", "Competidor2_Nombre", "Dojo2", "Ganador_Nombre", 
            "Posicion", "Total_Rondas", "Estado"
        ])

def guardar_brackets(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except Exception as e:
        return False

# === FUNCIONES DE MERCADO PAGO ===



def crear_preferencia_pago(nombre, email, monto, descripcion, referencia):
    """
    Crea una preferencia de pago en Mercado Pago
    """
    try:
        # URL BASE ACTUALIZADA
        base_url = "https://wkbchile-br5ucwq5ptkox2fnxasjyp.streamlit.app"

        preference_data = {
            "items": [
                {
                    "title": descripcion,
                    "quantity": 1,
                    "currency_id": "CLP",
                    "unit_price": float(monto)
                }
            ],
            "payer": {
                "name": nombre.split()[0] if nombre.split() else nombre,
                "surname": " ".join(nombre.split()[1:]) if len(nombre.split()) > 1 else "",
                "email": email
            },
            "back_urls": {
                "success": f"{base_url}/?success=true",
                "failure": f"{base_url}/?failure=true",
                "pending": f"{base_url}/?pending=true"
            },
            "auto_return": "approved",
            "external_reference": referencia,
            "statement_descriptor": "WKB CHILE",
            "payment_methods": {
                "excluded_payment_methods": [],
                "excluded_payment_types": [],
                "installments": 1
            }
        }
        
        preference = sdk.preference().create(preference_data)
        
        if preference["status"] == 201:
            return True, preference["response"]
        else:
            return False, None
            
    except Exception as e:
        st.error(f"Error creando preferencia de pago: {e}")
        return False, None



def verificar_pago(external_reference):
    """
    Verifica el estado de un pago por su referencia externa
    """
    try:
        # Buscar pagos por referencia externa
        filters = {
            "external_reference": external_reference
        }
        payments = sdk.payment().search(filters=filters)
        
        if payments["status"] == 200 and payments["response"]["results"]:
            payment = payments["response"]["results"][0]
            return {
                "id": payment["id"],
                "status": payment["status"],
                "status_detail": payment["status_detail"],
                "payment_method": payment["payment_method_id"],
                "date_approved": payment.get("date_approved", "")
            }
    except:
        pass
    
    return None

# === GENERADOR DE BRACKETS ===
def generar_brackets_ordenados():
    """
    Genera brackets con estructura de árbol perfectamente alineada
    """
    df_insc = leer_inscripciones()
    if df_insc.empty:
        return False, "No hay inscripciones registradas"
    
    df_conf = df_insc[df_insc['Estado'] == 'CONFIRMADO'].copy()
    if len(df_conf) < 2:
        return False, "Se necesitan al menos 2 competidores"
    
    todos_partidos = []
    stats = {}
    pid = 1
    
    for categoria in CATEGORIAS:
        df_cat = df_conf[df_conf['Categoria'] == categoria]
        num_competidores = len(df_cat)
        
        if num_competidores >= 2:
            num_rondas = math.ceil(math.log2(num_competidores))
            capacidad_total = 2 ** num_rondas
            
            stats[categoria] = {
                'competidores': num_competidores,
                'rondas': num_rondas,
                'capacidad': capacidad_total
            }
            
            competidores = df_cat.sample(frac=1).reset_index(drop=True)
            
            lista_competidores = []
            for i in range(capacidad_total):
                if i < num_competidores:
                    lista_competidores.append({
                        'nombre': competidores.iloc[i]['Nombre'],
                        'dojo': competidores.iloc[i]['Dojo']
                    })
                else:
                    lista_competidores.append({
                        'nombre': "BYE",
                        'dojo': "-"
                    })
            
            # Ronda 1
            for i in range(0, capacidad_total, 2):
                pos = i // 2
                c1 = lista_competidores[i]
                c2 = lista_competidores[i + 1]
                
                ganador = ""
                if c1['nombre'] == "BYE" and c2['nombre'] != "BYE":
                    ganador = c2['nombre']
                elif c2['nombre'] == "BYE" and c1['nombre'] != "BYE":
                    ganador = c1['nombre']
                
                estado = "AUTOMATICO" if ganador else "PENDIENTE"
                
                partido = {
                    "Categoria": categoria,
                    "Ronda": 1,
                    "Partido_ID": pid,
                    "Competidor1_Nombre": c1['nombre'],
                    "Dojo1": c1['dojo'],
                    "Competidor2_Nombre": c2['nombre'],
                    "Dojo2": c2['dojo'],
                    "Ganador_Nombre": ganador,
                    "Posicion": pos,
                    "Total_Rondas": num_rondas,
                    "Estado": estado
                }
                todos_partidos.append(partido)
                pid += 1
            
            # Rondas siguientes
            partidos_por_ronda = capacidad_total // 2
            for ronda in range(2, num_rondas + 1):
                partidos_por_ronda = partidos_por_ronda // 2
                for j in range(partidos_por_ronda):
                    partido = {
                        "Categoria": categoria,
                        "Ronda": ronda,
                        "Partido_ID": pid,
                        "Competidor1_Nombre": "",
                        "Dojo1": "",
                        "Competidor2_Nombre": "",
                        "Dojo2": "",
                        "Ganador_Nombre": "",
                        "Posicion": j,
                        "Total_Rondas": num_rondas,
                        "Estado": "PENDIENTE"
                    }
                    todos_partidos.append(partido)
                    pid += 1
    
    if todos_partidos:
        df_brackets = pd.DataFrame(todos_partidos)
        if guardar_brackets(df_brackets):
            mensaje = "✅ Brackets generados exitosamente\n\n"
            for cat, s in stats.items():
                mensaje += f"• {cat}: {s['competidores']} competidores\n"
            return True, mensaje
    
    return False, "No se pudieron generar los brackets"

# === VISUALIZADOR DE BRACKETS ===
def mostrar_brackets_ordenados(df_cat, es_admin=False):
    """
    Muestra brackets con alineación perfecta
    """
    if df_cat.empty:
        st.info("No hay partidos para esta categoría")
        return
    
    total_rondas = int(df_cat['Total_Rondas'].iloc[0])
    
    # Organizar partidos por ronda
    partidos_por_ronda = {}
    for ronda in range(1, total_rondas + 1):
        df_ronda = df_cat[df_cat['Ronda'] == ronda].sort_values('Posicion')
        partidos_por_ronda[ronda] = df_ronda.to_dict('records')
    
    # Calcular alturas
    altura_partido = 120
    separacion = 20
    altura_total_por_partido = altura_partido + separacion
    
    num_partidos_ronda1 = len(partidos_por_ronda[1])
    altura_total = num_partidos_ronda1 * altura_total_por_partido + 100
    
    # CSS
    st.markdown(f"""
    <style>
    .bracket-container {{
        position: relative;
        width: 100%;
        height: {altura_total}px;
        overflow-x: auto;
        overflow-y: visible;
        background: rgba(0,0,0,0.2);
        border-radius: 16px;
        padding: 20px 0;
        margin: 20px 0;
    }}
    .ronda-columna {{
        position: absolute;
        top: 0;
        width: 280px;
    }}
    .ronda-titulo {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #ff2b2b;
        text-align: center;
        padding: 10px;
        margin-bottom: 20px;
        border-bottom: 2px solid #ff2b2b;
        background: rgba(10,10,15,0.9);
        border-radius: 8px 8px 0 0;
    }}
    .partido-card {{
        position: absolute;
        width: 260px;
        background: linear-gradient(145deg, #1a1a24, #12121a);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 12px;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    .partido-card:hover {{
        transform: scale(1.02);
        border-color: #ff2b2b;
        z-index: 100;
    }}
    .partido-id {{
        position: absolute;
        top: -8px;
        right: 10px;
        background: #ff2b2b;
        color: white;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
    }}
    .competidor {{
        padding: 8px 10px;
        border-radius: 6px;
        margin: 4px 0;
        background: rgba(0,0,0,0.3);
        font-size: 0.85rem;
    }}
    .competidor.aka {{
        border-left: 4px solid #ff2b2b;
    }}
    .competidor.ao {{
        border-left: 4px solid #1e90ff;
    }}
    .competidor.ganador {{
        background: rgba(255,215,0,0.15);
        border-left-color: gold;
    }}
    .competidor.ganador .nombre {{
        color: gold;
        font-weight: bold;
    }}
    .dojo {{
        font-size: 0.65rem;
        color: rgba(255,255,255,0.4);
        margin-top: 2px;
    }}
    .bye-badge {{
        background: rgba(255,215,0,0.1);
        color: gold;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 4px;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor
    html = f'<div class="bracket-container"><div style="position:relative; height:100%;">'
    
    # Crear columnas
    for ronda in range(1, total_rondas + 1):
        partidos = partidos_por_ronda.get(ronda, [])
        if not partidos:
            continue
        
        x_pos = (ronda - 1) * 320
        
        # Título
        if ronda == total_rondas:
            titulo = "🏆 FINAL"
        elif ronda == total_rondas - 1:
            titulo = "🥈 SEMIFINAL"
        elif ronda == total_rondas - 2:
            titulo = "🥉 CUARTOS"
        else:
            titulo = f"RONDA {ronda}"
        
        html += f'<div class="ronda-columna" style="left: {x_pos}px;">'
        html += f'<div class="ronda-titulo">{titulo}</div>'
        
        for i, partido in enumerate(partidos):
            if ronda == 1:
                y_pos = 50 + i * altura_total_por_partido
            else:
                partidos_anteriores = partidos_por_ronda.get(ronda - 1, [])
                if partidos_anteriores:
                    idx_base = partido['Posicion'] * 2
                    if idx_base < len(partidos_anteriores):
                        y1 = 50 + idx_base * altura_total_por_partido
                        y2 = 50 + (idx_base + 1) * altura_total_por_partido
                        y_pos = (y1 + y2) // 2
                    else:
                        y_pos = 50
                else:
                    y_pos = 50
            
            clases_card = ["partido-card"]
            if partido['Estado'] == "COMPLETADO" or partido['Ganador_Nombre']:
                clases_card.append("completado")
            
            html += f'<div class="{" ".join(clases_card)}" style="top: {y_pos}px;">'
            html += f'<span class="partido-id">#{partido["Partido_ID"]}</span>'
            
            # Competidor 1
            c1_win = partido['Ganador_Nombre'] == partido['Competidor1_Nombre']
            clases_c1 = ["competidor", "aka"]
            if c1_win:
                clases_c1.append("ganador")
            
            html += f'<div class="{" ".join(clases_c1)}">'
            html += f'<div class="nombre">{partido["Competidor1_Nombre"]}</div>'
            if partido['Dojo1'] and partido['Dojo1'] != "-":
                html += f'<div class="dojo">{partido["Dojo1"]}</div>'
            html += '</div>'
            
            # BYE
            if partido['Competidor1_Nombre'] == "BYE" or partido['Competidor2_Nombre'] == "BYE":
                html += '<div class="bye-badge">⭐ BYE</div>'
            
            # Competidor 2
            c2_win = partido['Ganador_Nombre'] == partido['Competidor2_Nombre']
            clases_c2 = ["competidor", "ao"]
            if c2_win:
                clases_c2.append("ganador")
            
            html += f'<div class="{" ".join(clases_c2)}">'
            html += f'<div class="nombre">{partido["Competidor2_Nombre"]}</div>'
            if partido['Dojo2'] and partido['Dojo2'] != "-":
                html += f'<div class="dojo">{partido["Dojo2"]}</div>'
            html += '</div>'
            
            html += '</div>'  # Cierra partido-card
        
        html += '</div>'  # Cierra ronda-columna
    
    html += '</div></div>'
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Leyenda
    st.markdown("""
    <div style="display: flex; gap: 30px; justify-content: center; margin: 20px 0; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 50px;">
        <span><span style="color:#ff2b2b;">█</span> Aka (Rojo)</span>
        <span><span style="color:#1e90ff;">█</span> Ao (Azul)</span>
        <span><span style="color:gold;">🏆</span> Ganador</span>
        <span>⭐ BYE</span>
    </div>
    """, unsafe_allow_html=True)

# === ADMIN: ACTUALIZAR GANADORES ===
def admin_actualizar_ganadores(df_cat, categoria):
    """
    Interfaz para que el admin actualice los ganadores
    """
    st.markdown("### 👑 ACTUALIZAR GANADORES")
    
    rondas = sorted(df_cat['Ronda'].unique())
    
    if 'ronda_seleccionada' not in st.session_state:
        st.session_state.ronda_seleccionada = 1
    
    col1, col2 = st.columns([1, 3])
    with col1:
        ronda_sel = st.selectbox(
            "Ronda",
            rondas,
            index=rondas.index(st.session_state.ronda_seleccionada) if st.session_state.ronda_seleccionada in rondas else 0
        )
        st.session_state.ronda_seleccionada = ronda_sel
    
    df_ronda = df_cat[df_cat['Ronda'] == ronda_sel].sort_values('Posicion')
    
    df_pendientes = df_ronda[
        (df_ronda['Ganador_Nombre'] == "") & 
        (df_ronda['Competidor1_Nombre'] != "BYE") & 
        (df_ronda['Competidor2_Nombre'] != "BYE")
    ]
    
    if not df_pendientes.empty:
        for _, partido in df_pendientes.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.markdown(f"**{partido['Competidor1_Nombre']}**")
                if partido['Dojo1']:
                    st.caption(partido['Dojo1'])
            
            with col2:
                st.markdown(f"**{partido['Competidor2_Nombre']}**")
                if partido['Dojo2']:
                    st.caption(partido['Dojo2'])
            
            with col3:
                ganador = st.radio(
                    "Ganador",
                    [partido['Competidor1_Nombre'], partido['Competidor2_Nombre']],
                    key=f"radio_{partido['Partido_ID']}",
                    label_visibility="collapsed",
                    horizontal=True
                )
            
            with col4:
                if st.button("✓", key=f"btn_{partido['Partido_ID']}"):
                    df_brackets = leer_brackets()
                    
                    # Actualizar partido actual
                    mask_actual = (df_brackets['Categoria'] == categoria) & (df_brackets['Partido_ID'] == partido['Partido_ID'])
                    df_brackets.loc[mask_actual, 'Ganador_Nombre'] = ganador
                    df_brackets.loc[mask_actual, 'Estado'] = "COMPLETADO"
                    
                    # Propagar a siguiente ronda
                    siguiente_ronda = ronda_sel + 1
                    siguiente_posicion = partido['Posicion'] // 2
                    
                    mask_siguiente = (df_brackets['Categoria'] == categoria) & \
                                    (df_brackets['Ronda'] == siguiente_ronda) & \
                                    (df_brackets['Posicion'] == siguiente_posicion)
                    
                    if not df_brackets[mask_siguiente].empty:
                        if partido['Posicion'] % 2 == 0:
                            df_brackets.loc[mask_siguiente, 'Competidor1_Nombre'] = ganador
                            df_brackets.loc[mask_siguiente, 'Dojo1'] = partido['Dojo1'] if ganador == partido['Competidor1_Nombre'] else partido['Dojo2']
                        else:
                            df_brackets.loc[mask_siguiente, 'Competidor2_Nombre'] = ganador
                            df_brackets.loc[mask_siguiente, 'Dojo2'] = partido['Dojo1'] if ganador == partido['Competidor1_Nombre'] else partido['Dojo2']
                    
                    if guardar_brackets(df_brackets):
                        st.success(f"✅ Ganador: {ganador}")
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("✅ No hay partidos pendientes en esta ronda")

# === CSS PRINCIPAL ===
css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=Space+Grotesk:wght@300;400;600;700&display=swap');
    
    .stApp {
        background: #0a0a0f;
        font-family: 'Inter', sans-serif;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1a1a24;
    }
    ::-webkit-scrollbar-thumb {
        background: #ff2b2b;
        border-radius: 4px;
    }
    
    .header-container {
        text-align: center;
        padding: 40px 20px;
        position: relative;
        overflow: hidden;
    }
    
    .logo-img {
        width: min(400px, 80%);
        filter: drop-shadow(0 0 40px rgba(255,43,43,0.3));
        transition: transform 0.5s;
    }
    
    .title-main {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #ff8a8a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 20px 0 10px;
        letter-spacing: 2px;
    }
    
    .subtitle {
        color: rgba(255,255,255,0.5);
        font-size: 0.9rem;
        letter-spacing: 4px;
        text-transform: uppercase;
    }
    
    .countdown-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        max-width: 800px;
        margin: 40px auto;
        padding: 0 20px;
    }
    
    .countdown-item {
        background: linear-gradient(145deg, #12121a, #1a1a24);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s;
    }
    
    .countdown-number {
        font-family: 'Space Grotesk', monospace;
        font-size: clamp(2rem, 5vw, 3rem);
        font-weight: 800;
        color: #ff2b2b;
        line-height: 1;
        margin-bottom: 5px;
    }
    
    .countdown-label {
        color: rgba(255,255,255,0.5);
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .glass-card {
        background: rgba(18, 18, 26, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 24px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    
    .metric-container {
        background: linear-gradient(145deg, #12121a, #0a0a0f);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s;
    }
    
    .metric-container:hover {
        border-color: #ff2b2b;
        transform: translateY(-5px);
    }
    
    .metric-label {
        color: rgba(255,255,255,0.5);
        font-size: 0.8rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        color: #ff2b2b;
        text-shadow: 0 0 30px rgba(255,43,43,0.3);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(18, 18, 26, 0.5);
        backdrop-filter: blur(10px);
        padding: 8px;
        border-radius: 50px;
        border: 1px solid rgba(255,255,255,0.03);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 40px;
        padding: 10px 24px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff2b2b, #ff5555) !important;
        color: white !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #ff2b2b, #ff5555) !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 1px !important;
        padding: 12px 24px !important;
        border: none !important;
        border-radius: 12px !important;
        width: 100%;
        transition: all 0.3s !important;
        text-transform: uppercase !important;
        box-shadow: 0 10px 20px rgba(255,43,43,0.2) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 30px rgba(255,43,43,0.3) !important;
    }
    
    .payment-button > button {
        background: linear-gradient(135deg, #00a650, #00cc66) !important;
    }
    
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,43,43,0.3), transparent);
        margin: 30px 0;
    }
    
    .footer {
        text-align: center;
        color: rgba(255,255,255,0.3);
        padding: 40px 0 20px;
        font-size: 0.8rem;
        letter-spacing: 1px;
        border-top: 1px solid rgba(255,255,255,0.03);
        margin-top: 60px;
    }
    
    .mp-logo {
        height: 30px;
        margin-right: 10px;
        vertical-align: middle;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# === HEADER ===
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" class="logo-img">
        <div class="title-main">WORLD CUP 2026</div>
        <div class="subtitle">SANTIAGO · CHILE</div>
    </div>
    """, unsafe_allow_html=True)

# === COUNTDOWN ===
dias, horas, minutos, segundos = tiempo_restante()
st.markdown(f"""
<div class="countdown-grid">
    <div class="countdown-item">
        <div class="countdown-number">{dias}</div>
        <div class="countdown-label">DÍAS</div>
    </div>
    <div class="countdown-item">
        <div class="countdown-number">{horas}</div>
        <div class="countdown-label">HORAS</div>
    </div>
    <div class="countdown-item">
        <div class="countdown-number">{minutos}</div>
        <div class="countdown-label">MINUTOS</div>
    </div>
    <div class="countdown-item">
        <div class="countdown-number">{segundos}</div>
        <div class="countdown-label">SEGUNDOS</div>
    </div>
</div>
""", unsafe_allow_html=True)

# === TABS ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 DASHBOARD", 
    "📝 INSCRIPCIÓN", 
    "📦 INSCRIPCIÓN GRUPAL", 
    "🏆 BRACKETS", 
    "⚡ ADMIN"
])

# ========== TAB 1: DASHBOARD ==========
with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📊 PANEL DE CONTROL")
    
    df = leer_inscripciones()
    
    if not df.empty:
        df_conf = df[df['Estado'] == 'CONFIRMADO']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">INSCRITOS</div>
                <div class="metric-value">{len(df_conf)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">CATEGORÍAS</div>
                <div class="metric-value">{df_conf['Categoria'].nunique()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">DOJOS</div>
                <div class="metric-value">{df_conf['Dojo'].nunique()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            cupos_restantes = 500 - len(df_conf)
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">CUPOS</div>
                <div class="metric-value">{cupos_restantes}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Estadísticas de pago
        col1, col2, col3 = st.columns(3)
        with col1:
            pagados_mp = len(df_conf[df_conf['Metodo'] == 'MERCADOPAGO'])
            st.metric("Pagos MP", pagados_mp)
        with col2:
            pagados_vip = len(df_conf[df_conf['Metodo'] == 'VIP'])
            st.metric("Códigos VIP", pagados_vip)
        with col3:
            pendientes = len(df_conf[df_conf['Metodo'] == 'PENDIENTE'])
            st.metric("Pendientes", pendientes)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Gráfico
        counts = df_conf['Categoria'].value_counts().sort_values()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=counts.index,
            x=counts.values,
            orientation='h',
            marker=dict(
                color=counts.values,
                colorscale=[[0, '#440000'], [1, '#ff2b2b']],
                showscale=False
            ),
            text=counts.values,
            textposition='outside',
            textfont=dict(color='white')
        ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📌 No hay inscripciones registradas")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 2: INSCRIPCIÓN INDIVIDUAL ==========
with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 INSCRIPCIÓN INDIVIDUAL")
    
    # Procesar retorno de Mercado Pago
    params = st.query_params
    if "success" in params and params["success"] == "true":
        st.balloons()
        st.success("✅ ¡Pago exitoso! Tu inscripción está siendo procesada.")
        st.info("Recibirás un email de confirmación en los próximos minutos.")
        time.sleep(3)
        st.query_params.clear()
        st.rerun()
    elif "failure" in params:
        st.error("❌ El pago no pudo completarse. Por favor intenta nuevamente.")
        st.query_params.clear()
    elif "pending" in params:
        st.warning("⏳ El pago está pendiente. Te notificaremos cuando se confirme.")
        st.query_params.clear()
    
    with st.form("form_inscripcion"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre Completo *")
            email = st.text_input("Email *")
            telefono = st.text_input("Teléfono *")
        
        with col2:
            edad = st.number_input("Edad *", 18, 99, 25)
            dojo = st.text_input("Dojo *")
            pais = st.selectbox("País", PAISES)
        
        categoria = st.selectbox("Categoría *", CATEGORIAS)
        
        st.markdown(f"### Valor: {formatear_peso(PRECIO)} CLP")
        
        metodo_pago = st.radio(
            "Método de pago",
            ["Código VIP", "Mercado Pago"],
            horizontal=True,
            help="VIP: Código especial. Mercado Pago: Pago con tarjeta, transferencia o efectivo"
        )
        
        codigo_vip = ""
        if metodo_pago == "Código VIP":
            codigo_vip = st.text_input("Código VIP", type="password")
        
        terminos = st.checkbox("Acepto los términos y condiciones")
        
        submitted = st.form_submit_button("CONTINUAR")
        
        if submitted:
            errores = []
            if not nombre or len(nombre.split()) < 2:
                errores.append("Nombre completo requerido")
            if not email or not validar_email(email):
                errores.append("Email inválido")
            if not telefono or len(telefono) < 8:
                errores.append("Teléfono inválido")
            if not dojo:
                errores.append("Dojo requerido")
            if not terminos:
                errores.append("Debes aceptar los términos")
            if metodo_pago == "Código VIP" and codigo_vip != CODIGO_VIP:
                errores.append("Código VIP inválido")
            
            if not errores:
                # Guardar en session state para usar después
                st.session_state.inscripcion_temp = {
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono,
                    'edad': edad,
                    'dojo': dojo,
                    'pais': pais,
                    'categoria': categoria,
                    'metodo': metodo_pago
                }
                
                if metodo_pago == "Código VIP":
                    # Pago con código - guardar inmediatamente
                    datos = {
                        'id': generar_id(nombre, email),
                        'nombre': nombre,
                        'email': email,
                        'telefono': telefono,
                        'edad': edad,
                        'dojo': dojo,
                        'pais': pais,
                        'categoria': categoria,
                        'estado': 'CONFIRMADO',
                        'metodo': 'VIP',
                        'grupo_id': '',
                        'pago_id': '',
                        'pago_estado': 'approved'
                    }
                    
                    if guardar_inscripcion(datos):
                        st.balloons()
                        st.success("✅ ¡Inscripción exitosa con código VIP!")
                        time.sleep(2)
                        st.rerun()
                
                elif metodo_pago == "Mercado Pago":
                    # Crear preferencia de pago
                    referencia = generar_referencia_pago()
                    descripcion = f"Inscripción WKB - {categoria} - {nombre}"
                    
                    with st.spinner("Preparando pago con Mercado Pago..."):
                        exito, preferencia = crear_preferencia_pago(
                            nombre, email, PRECIO, descripcion, referencia
                        )
                        
                        if exito and preferencia:
                            # Guardar referencia en session state
                            st.session_state.pago_referencia = referencia
                            st.session_state.pago_data = {
                                'nombre': nombre,
                                'email': email,
                                'telefono': telefono,
                                'edad': edad,
                                'dojo': dojo,
                                'pais': pais,
                                'categoria': categoria
                            }
                            
                            # Mostrar opciones de pago
                            st.info("⏳ Redirigiendo a Mercado Pago...")
                            
                            # Link de pago
                            init_point = preferencia.get('init_point', '')
                            if init_point:
                                st.markdown(f"""
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{init_point}" target="_blank">
                                        <button style="background: linear-gradient(135deg, #00a650, #00cc66); 
                                                     color: white; 
                                                     border: none; 
                                                     padding: 15px 40px; 
                                                     border-radius: 50px; 
                                                     font-size: 1.2rem;
                                                     font-weight: bold;
                                                     cursor: pointer;
                                                     box-shadow: 0 10px 20px rgba(0,166,80,0.3);
                                                     transition: all 0.3s;">
                                            <img src="https://static.wixstatic.com/media/6761e5_2a4f07de0e7a4dbfb804c03cde73b8d3~mv2.png" 
                                                 style="height: 30px; margin-right: 10px; vertical-align: middle;">
                                            PAGAR CON MERCADO PAGO
                                        </button>
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.markdown("""
                                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-top: 20px;">
                                    <h4 style="color: white;">💳 Opciones de pago aceptadas:</h4>
                                    <ul style="color: rgba(255,255,255,0.8);">
                                        <li>Tarjetas de crédito (hasta 12 cuotas)</li>
                                        <li>Tarjetas de débito</li>
                                        <li>Efectivo (RedCompra, Servipag)</li>
                                        <li>Transferencia bancaria</li>
                                    </ul>
                                    <p style="color: #00a650; font-size: 0.9rem;">🔒 Pago 100% seguro procesado por Mercado Pago</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Instrucciones
                                with st.expander("📋 Instrucciones"):
                                    st.markdown("""
                                    1. Haz clic en el botón de Mercado Pago
                                    2. Serás redirigido al sitio seguro de Mercado Pago
                                    3. Elige tu método de pago preferido
                                    4. Completa el pago
                                    5. Serás redirigido automáticamente a esta página
                                    6. Recibirás la confirmación por email
                                    """)
                            else:
                                st.error("Error al generar el link de pago")
                        else:
                            st.error("Error al conectar con Mercado Pago. Por favor intenta más tarde.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 3: INSCRIPCIÓN GRUPAL ==========
with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📦 INSCRIPCIÓN GRUPAL")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Beneficios")
        st.markdown(f"""
        - Precio por persona: **{formatear_peso(PRECIO_GRUPAL)} CLP**
        - Ahorro: **{formatear_peso(PRECIO - PRECIO_GRUPAL)} CLP** por persona
        - Pago único para todo el grupo
        """)
    
    with col2:
        st.markdown("#### 📋 Formato requerido")
        st.markdown("""
        Sube un archivo CSV o Excel con:
        - **Nombre**, **Email**, **Telefono**, **Edad**, **Dojo**, **Pais**, **Categoria**
        """)
        
        template_df = pd.DataFrame({
            'Nombre': ['Juan Pérez', 'María González'],
            'Email': ['juan@email.com', 'maria@email.com'],
            'Telefono': ['+56912345678', '+56987654321'],
            'Edad': [25, 24],
            'Dojo': ['SHOTOKAN', 'SHOTOKAN'],
            'Pais': ['Chile', 'Chile'],
            'Categoria': ['KUMITE -65kg (18+)', 'KUMITE -55kg (18+) Femenino']
        })
        
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            "📥 DESCARGAR TEMPLATE",
            csv_template,
            "template_grupal.csv",
            "text/csv"
        )
    
    st.markdown("---")
    
    archivo = st.file_uploader(
        "Seleccionar archivo CSV/Excel",
        type=['csv', 'xlsx', 'xls']
    )
    
    if archivo is not None:
        try:
            if archivo.name.endswith('.csv'):
                df_carga = pd.read_csv(archivo)
            else:
                df_carga = pd.read_excel(archivo)
            
            st.markdown("#### 📋 Vista previa")
            st.dataframe(df_carga.head(10), use_container_width=True)
            
            if st.button("🔄 PROCESAR INSCRIPCIONES"):
                with st.spinner("Procesando..."):
                    grupo_id = generar_id_grupal()
                    referencia_pago = generar_referencia_pago()
                    
                    registros_validos = []
                    errores = []
                    
                    for idx, row in df_carga.iterrows():
                        try:
                            nombre = str(row.get('Nombre', '')).strip()
                            email = str(row.get('Email', '')).strip()
                            telefono = str(row.get('Telefono', '')).strip()
                            edad = row.get('Edad', 0)
                            dojo = str(row.get('Dojo', '')).strip()
                            pais = str(row.get('Pais', 'Chile')).strip()
                            categoria = str(row.get('Categoria', '')).strip()
                            
                            if not nombre or len(nombre.split()) < 2:
                                errores.append(f"Fila {idx + 2}: Nombre incompleto")
                                continue
                            if not email or not validar_email(email):
                                errores.append(f"Fila {idx + 2}: Email inválido")
                                continue
                            if not telefono or len(telefono) < 8:
                                errores.append(f"Fila {idx + 2}: Teléfono inválido")
                                continue
                            if categoria not in CATEGORIAS:
                                errores.append(f"Fila {idx + 2}: Categoría inválida")
                                continue
                            
                            registros_validos.append({
                                "ID": generar_id(nombre, email),
                                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Nombre": nombre.upper(),
                                "Email": email.lower(),
                                "Telefono": telefono,
                                "Edad": int(edad),
                                "Dojo": dojo.upper(),
                                "Pais": pais,
                                "Categoria": categoria,
                                "Estado": "PENDIENTE",
                                "Metodo": "GRUPAL",
                                "Grupo_ID": grupo_id,
                                "Pago_ID": referencia_pago,
                                "Pago_Estado": "pending"
                            })
                        
                        except Exception as e:
                            errores.append(f"Fila {idx + 2}: Error de formato")
                    
                    if errores:
                        for error in errores[:5]:
                            st.warning(error)
                    
                    if registros_validos:
                        df_nuevas = pd.DataFrame(registros_validos)
                        total_pagar = len(registros_validos) * PRECIO_GRUPAL
                        
                        st.markdown(f"""
                        <div style="background: #00ff8822; padding: 20px; border-radius: 16px; margin: 20px 0; text-align: center;">
                            <h3 style="color: #00ff88;">✅ {len(registros_validos)} inscripciones válidas</h3>
                            <p style="font-size: 1.5rem; font-weight: bold; color: #00ff88;">Total a pagar: {formatear_peso(total_pagar)} CLP</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Guardar en session state
                        st.session_state.grupo_data = {
                            'df': df_nuevas,
                            'total': total_pagar,
                            'referencia': referencia_pago
                        }
                        
                        # Botón de pago
                        descripcion = f"Inscripción grupal WKB - {len(registros_validos)} personas"
                        
                        with st.spinner("Preparando pago..."):
                            exito, preferencia = crear_preferencia_pago(
                                "GRUPO", 
                                registros_validos[0]['Email'], 
                                total_pagar, 
                                descripcion, 
                                referencia_pago
                            )
                            
                            if exito and preferencia:
                                init_point = preferencia.get('init_point', '')
                                if init_point:
                                    st.markdown(f"""
                                    <div style="text-align: center; margin: 20px 0;">
                                        <a href="{init_point}" target="_blank">
                                            <button style="background: linear-gradient(135deg, #00a650, #00cc66); 
                                                         color: white; 
                                                         border: none; 
                                                         padding: 15px 40px; 
                                                         border-radius: 50px; 
                                                         font-size: 1.2rem;
                                                         font-weight: bold;
                                                         cursor: pointer;">
                                                <img src="https://static.wixstatic.com/media/6761e5_2a4f07de0e7a4dbfb804c03cde73b8d3~mv2.png" 
                                                     style="height: 30px; margin-right: 10px; vertical-align: middle;">
                                                PAGAR CON MERCADO PAGO
                                            </button>
                                        </a>
                                    </div>
                                    """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error al leer archivo: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 4: BRACKETS ==========
with tab4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🏆 BRACKETS DEL TORNEO")
    
    is_admin = False
    with st.expander("🔐 Acceso Admin", expanded=False):
        admin_pass = st.text_input("Contraseña Admin", type="password", key="admin_pass_brackets")
        is_admin = verificar_admin(admin_pass)
    
    if is_admin:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚡ GENERAR BRACKETS", use_container_width=True):
                with st.spinner("Generando brackets..."):
                    resultado, mensaje = generar_brackets_ordenados()
                    if resultado:
                        st.success(mensaje)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning(mensaje)
        st.markdown("<hr>", unsafe_allow_html=True)
    
    df_brackets = leer_brackets()
    
    if not df_brackets.empty:
        categorias = df_brackets['Categoria'].unique()
        categoria_sel = st.selectbox("📂 Seleccionar Categoría", categorias)
        
        df_cat = df_brackets[df_brackets['Categoria'] == categoria_sel]
        
        if not df_cat.empty:
            mostrar_brackets_ordenados(df_cat, is_admin)
            
            if is_admin:
                admin_actualizar_ganadores(df_cat, categoria_sel)
    
    else:
        st.info("📌 No hay brackets generados")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 5: ADMIN ==========
with tab5:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ⚡ PANEL DE ADMINISTRACIÓN")
    
    password = st.text_input("Contraseña", type="password", key="admin_pass_main")
    
    if verificar_admin(password):
        tabs_admin = st.tabs(["📋 Inscripciones", "🏆 Brackets", "💰 Pagos", "📊 Estadísticas"])
        
        with tabs_admin[0]:
            df_admin = leer_inscripciones()
            if not df_admin.empty:
                st.dataframe(df_admin, use_container_width=True, hide_index=True)
                csv = df_admin.to_csv(index=False)
                st.download_button(
                    "📥 DESCARGAR CSV",
                    csv,
                    "inscripciones.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with tabs_admin[1]:
            df_b = leer_brackets()
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                if st.button("⚠️ REINICIAR BRACKETS", use_container_width=True):
                    df_vacio = pd.DataFrame(columns=df_b.columns)
                    if guardar_brackets(df_vacio):
                        st.warning("Brackets reiniciados")
                        st.rerun()
        
        with tabs_admin[2]:
            st.markdown("#### 💰 Seguimiento de Pagos")
            df_pagos = leer_inscripciones()
            if not df_pagos.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_mp = len(df_pagos[df_pagos['Metodo'] == 'MERCADOPAGO'])
                    st.metric("Pagos MP", total_mp)
                with col2:
                    monto_mp = len(df_pagos[df_pagos['Metodo'] == 'MERCADOPAGO']) * PRECIO
                    st.metric("Monto MP", formatear_peso(monto_mp))
                with col3:
                    pendientes = len(df_pagos[df_pagos['Pago_Estado'] == 'pending'])
                    st.metric("Pendientes", pendientes)
                
                st.dataframe(
                    df_pagos[df_pagos['Metodo'] == 'MERCADOPAGO'][['Fecha', 'Nombre', 'Email', 'Pago_Estado', 'Pago_ID']],
                    use_container_width=True
                )
        
        with tabs_admin[3]:
            df_stats = leer_inscripciones()
            if not df_stats.empty:
                df_conf = df_stats[df_stats['Estado'] == 'CONFIRMADO']
                
                col1, col2, col3 = st.columns(3)
                
                total_vip = len(df_conf[df_conf['Metodo'] == 'VIP']) * PRECIO
                total_mp = len(df_conf[df_conf['Metodo'] == 'MERCADOPAGO']) * PRECIO
                total_grupal = len(df_conf[df_conf['Metodo'] == 'GRUPAL']) * PRECIO_GRUPAL
                total = total_vip + total_mp + total_grupal
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">INGRESOS TOTALES</div>
                        <div class="metric-value">{formatear_peso(total)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">INSCRIPCIONES</div>
                        <div class="metric-value">{len(df_conf)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    grupos = df_conf[df_conf['Metodo'] == 'GRUPAL']['Grupo_ID'].nunique()
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">GRUPOS</div>
                        <div class="metric-value">{grupos}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    elif password:
        st.error("❌ Contraseña incorrecta")
    
    st.markdown('</div>', unsafe_allow_html=True)

# === FOOTER ===
st.markdown("""
<div class="footer">
    <p>© 2024 World Kyokushin Budokai Chile · Todos los derechos reservados</p>
</div>
""", unsafe_allow_html=True)

