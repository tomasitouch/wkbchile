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
import io

# === CONFIGURACIÓN DE PÁGINA ===
st.set_page_config(
    page_title="WKB WORLD CUP 2026",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === CONSTANTES ===
LOGO_URL = "https://www.worldkyokushinbudokai.com/assets/custom/img/logo.png"
PRECIO = 15000
PRECIO_GRUPAL = 14000  # Precio por persona para inscripciones grupales
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

def generar_id_grupal(dojo):
    texto = f"{dojo}{datetime.now()}"
    return hashlib.md5(texto.encode()).hexdigest()[:8].upper()

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
            return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo", "Grupo_ID"])
        return df
    except:
        return pd.DataFrame(columns=["ID", "Fecha", "Nombre", "Email", "Telefono", "Edad", "Dojo", "Pais", "Categoria", "Estado", "Metodo", "Grupo_ID"])

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
            "Estado": "CONFIRMADO",
            "Metodo": datos['metodo'],
            "Grupo_ID": datos.get('grupo_id', '')
        }])
        
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True)
        conn.update(worksheet="Inscripciones", data=df_final)
        return True
    except:
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
    except:
        return False

@st.cache_data(ttl=5)
def leer_brackets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Brackets", ttl=0)
        df = df.fillna("")
        if df.empty:
            return pd.DataFrame(columns=[
                "Categoria", "Ronda", "Partido_ID", "Competidor1_ID", "Competidor1_Nombre", 
                "Dojo1", "Competidor2_ID", "Competidor2_Nombre", "Dojo2", 
                "Ganador_ID", "Ganador_Nombre", "Siguiente_Partido_ID", "Posicion", 
                "Total_Rondas", "Estado_Partido", "Tipo_Emparejamiento"
            ])
        return df
    except:
        return pd.DataFrame(columns=[
            "Categoria", "Ronda", "Partido_ID", "Competidor1_ID", "Competidor1_Nombre", 
            "Dojo1", "Competidor2_ID", "Competidor2_Nombre", "Dojo2", 
            "Ganador_ID", "Ganador_Nombre", "Siguiente_Partido_ID", "Posicion", 
            "Total_Rondas", "Estado_Partido", "Tipo_Emparejamiento"
        ])

def guardar_brackets(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="Brackets", data=df)
        return True
    except:
        return False

# === NUEVA FUNCIÓN PARA BRACKETS ORDENADOS ===
def generar_brackets_ordenados(df_competidores, categoria):
    """
    Genera brackets con estructura de árbol horizontal perfectamente alineada
    """
    num_competidores = len(df_competidores)
    if num_competidores < 2:
        return []
    
    # Calcular estructura del torneo
    num_rondas = math.ceil(math.log2(num_competidores))
    capacidad_total = 2 ** num_rondas
    
    # Ordenar competidores (aleatorio pero guardamos el orden)
    competidores = df_competidores.sample(frac=1).reset_index(drop=True)
    
    partidos = []
    pid = 1
    
    # Mapa para tracking de posiciones
    posiciones_siguiente_ronda = {}
    
    # Ronda 1 - Crear todos los slots
    for i in range(0, capacidad_total, 2):
        pos = i // 2
        
        # Asignar competidores disponibles o BYE
        c1 = competidores.iloc[i] if i < num_competidores else None
        c2 = competidores.iloc[i + 1] if (i + 1) < num_competidores else None
        
        # Calcular posición en siguiente ronda
        siguiente_pos = pos // 2
        siguiente_partido_id = None
        
        partido = {
            "Categoria": categoria,
            "Ronda": 1,
            "Partido_ID": pid,
            "Competidor1_ID": c1['ID'] if c1 is not None else "BYE",
            "Competidor1_Nombre": c1['Nombre'] if c1 is not None else "BYE",
            "Dojo1": c1['Dojo'] if c1 is not None else "-",
            "Competidor2_ID": c2['ID'] if c2 is not None else "BYE",
            "Competidor2_Nombre": c2['Nombre'] if c2 is not None else "BYE",
            "Dojo2": c2['Dojo'] if c2 is not None else "-",
            "Ganador_ID": "",
            "Ganador_Nombre": "",
            "Siguiente_Partido_ID": siguiente_partido_id,
            "Posicion": pos,
            "Total_Rondas": num_rondas,
            "Estado_Partido": "PENDIENTE",
            "Tipo_Emparejamiento": "AUTOMATICO"
        }
        
        # Si hay BYE, el ganador es automático
        if partido["Competidor1_Nombre"] == "BYE" and partido["Competidor2_Nombre"] != "BYE":
            partido["Ganador_ID"] = partido["Competidor2_ID"]
            partido["Ganador_Nombre"] = partido["Competidor2_Nombre"]
            partido["Estado_Partido"] = "AUTOMATICO"
        elif partido["Competidor2_Nombre"] == "BYE" and partido["Competidor1_Nombre"] != "BYE":
            partido["Ganador_ID"] = partido["Competidor1_ID"]
            partido["Ganador_Nombre"] = partido["Competidor1_Nombre"]
            partido["Estado_Partido"] = "AUTOMATICO"
        elif partido["Competidor1_Nombre"] == "BYE" and partido["Competidor2_Nombre"] == "BYE":
            partido["Estado_Partido"] = "VACIO"
        
        partidos.append(partido)
        pid += 1
    
    # Crear rondas siguientes con conexiones
    for ronda in range(2, num_rondas + 1):
        partidos_por_ronda = capacidad_total // (2 ** ronda)
        
        for j in range(partidos_por_ronda):
            # Calcular IDs de los partidos anteriores que alimentan este
            partido_anterior1 = (j * 2) + 1 + sum([capacidad_total // (2 ** r) for r in range(1, ronda)])
            partido_anterior2 = (j * 2) + 2 + sum([capacidad_total // (2 ** r) for r in range(1, ronda)])
            
            partido = {
                "Categoria": categoria,
                "Ronda": ronda,
                "Partido_ID": pid,
                "Competidor1_ID": "",
                "Competidor1_Nombre": "",
                "Dojo1": "",
                "Competidor2_ID": "",
                "Competidor2_Nombre": "",
                "Dojo2": "",
                "Ganador_ID": "",
                "Ganador_Nombre": "",
                "Siguiente_Partido_ID": None,
                "Posicion": j,
                "Total_Rondas": num_rondas,
                "Estado_Partido": "PENDIENTE",
                "Tipo_Emparejamiento": "AUTOMATICO"
            }
            
            # Actualizar los partidos anteriores con el siguiente partido ID
            for p in partidos:
                if p['Partido_ID'] == partido_anterior1 or p['Partido_ID'] == partido_anterior2:
                    p['Siguiente_Partido_ID'] = pid
            
            partidos.append(partido)
            pid += 1
    
    return partidos

# === FUNCIÓN PARA VISUALIZAR BRACKETS ORDENADOS ===
def visualizar_brackets_ordenados(df_cat):
    """
    Crea una visualización de brackets perfectamente alineados
    """
    if df_cat.empty:
        return ""
    
    total_rondas = int(df_cat['Total_Rondas'].iloc[0])
    
    # Organizar partidos por ronda
    partidos_por_ronda = {}
    for ronda in range(1, total_rondas + 1):
        df_ronda = df_cat[df_cat['Ronda'] == ronda].sort_values('Posicion')
        partidos_por_ronda[ronda] = df_ronda.to_dict('records')
    
    # Calcular espaciado para alineación perfecta
    espaciado_base = 80  # píxeles entre partidos
    
    html = '<div class="bracket-tree">'
    html += '<div class="bracket-tree-container">'
    
    # Crear estructura de árbol horizontal
    for ronda in range(1, total_rondas + 1):
        partidos = partidos_por_ronda.get(ronda, [])
        num_partidos = len(partidos)
        
        # Calcular posición vertical para alineación perfecta
        if ronda == 1:
            # Primera ronda: todos los partidos visibles
            espaciado = espaciado_base
            offset = 0
        else:
            # Rondas superiores: conectar con partidos anteriores
            espaciado = espaciado_base * (2 ** (ronda - 1))
            offset = espaciado // 2
        
        html += f'<div class="bracket-round-column" style="width: 300px;">'
        html += f'<div class="bracket-round-title">'
        if ronda == total_rondas:
            html += '🏆 FINAL'
        elif ronda == total_rondas - 1:
            html += '🥈 SEMIFINAL'
        elif ronda == total_rondas - 2:
            html += '🥉 CUARTOS'
        else:
            html += f'RONDA {ronda}'
        html += '</div>'
        
        for i, partido in enumerate(partidos):
            # Calcular posición vertical
            top_position = offset + (i * espaciado)
            
            html += f'<div class="bracket-match" style="top: {top_position}px; position: absolute;">'
            
            # ID del partido
            html += f'<span class="bracket-id">#{partido["Partido_ID"]}</span>'
            
            # Estado
            if partido['Estado_Partido'] == 'COMPLETADO':
                html += '<span class="status-badge completed">✓</span>'
            elif partido['Estado_Partido'] == 'AUTOMATICO':
                html += '<span class="status-badge auto">⚡</span>'
            
            # Competidor 1
            c1_win = partido['Ganador_Nombre'] == partido['Competidor1_Nombre']
            html += f'<div class="bracket-competitor red{" winner" if c1_win else ""}">'
            html += f'<div class="competitor-name">{partido["Competidor1_Nombre"]}</div>'
            if partido['Dojo1']:
                html += f'<div class="bracket-dojo">{partido["Dojo1"]}</div>'
            html += '</div>'
            
            # VS (opcional)
            if partido['Competidor1_Nombre'] != "BYE" and partido['Competidor2_Nombre'] != "BYE":
                html += '<div class="bracket-vs">VS</div>'
            
            # Competidor 2
            c2_win = partido['Ganador_Nombre'] == partido['Competidor2_Nombre']
            html += f'<div class="bracket-competitor blue{" winner" if c2_win else ""}">'
            html += f'<div class="competitor-name">{partido["Competidor2_Nombre"]}</div>'
            if partido['Dojo2']:
                html += f'<div class="bracket-dojo">{partido["Dojo2"]}</div>'
            html += '</div>'
            
            # Línea de conexión si no es la última ronda
            if ronda < total_rondas and partido['Siguiente_Partido_ID']:
                siguiente_partido = next(
                    (p for p in partidos_por_ronda.get(ronda + 1, []) 
                     if p['Partido_ID'] == partido['Siguiente_Partido_ID']), 
                    None
                )
                if siguiente_partido:
                    siguiente_pos = partido['Posicion'] // 2
                    if partido['Posicion'] % 2 == 0:  # Es el primer partido que alimenta
                        html += '<div class="connector-line left"></div>'
                    else:
                        html += '<div class="connector-line right"></div>'
            
            html += '</div>'  # Cierra bracket-match
        
        html += '</div>'  # Cierra bracket-round-column
    
    html += '</div></div>'  # Cierra bracket-tree-container y bracket-tree
    
    return html

# === FUNCIÓN PARA INSCRIPCIONES MASIVAS ===
def procesar_inscripciones_masivas(df_carga, grupo_id):
    """
    Procesa un DataFrame con múltiples inscripciones
    """
    inscripciones_validas = []
    errores = []
    
    for idx, row in df_carga.iterrows():
        try:
            # Validar datos requeridos
            nombre = str(row.get('Nombre', '')).strip()
            email = str(row.get('Email', '')).strip()
            telefono = str(row.get('Telefono', '')).strip()
            edad = row.get('Edad', 0)
            dojo = str(row.get('Dojo', '')).strip()
            pais = str(row.get('Pais', 'Chile')).strip()
            categoria = str(row.get('Categoria', '')).strip()
            
            # Validaciones
            if not nombre or len(nombre.split()) < 2:
                errores.append(f"Fila {idx + 2}: Nombre incompleto")
                continue
                
            if not email or not validar_email(email):
                errores.append(f"Fila {idx + 2}: Email inválido")
                continue
                
            if not telefono or len(telefono) < 8:
                errores.append(f"Fila {idx + 2}: Teléfono inválido")
                continue
                
            if not dojo:
                errores.append(f"Fila {idx + 2}: Dojo requerido")
                continue
                
            if categoria not in CATEGORIAS:
                errores.append(f"Fila {idx + 2}: Categoría inválida")
                continue
            
            # Generar ID individual
            id_individual = generar_id(nombre, email)
            
            # Crear registro
            nueva_inscripcion = {
                "ID": id_individual,
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Nombre": nombre.upper(),
                "Email": email.lower(),
                "Telefono": telefono,
                "Edad": int(edad),
                "Dojo": dojo.upper(),
                "Pais": pais,
                "Categoria": categoria,
                "Estado": "CONFIRMADO",
                "Metodo": "GRUPAL",
                "Grupo_ID": grupo_id
            }
            
            inscripciones_validas.append(nueva_inscripcion)
            
        except Exception as e:
            errores.append(f"Fila {idx + 2}: Error de formato - {str(e)}")
    
    df_nuevas = pd.DataFrame(inscripciones_validas) if inscripciones_validas else pd.DataFrame()
    
    return df_nuevas, errores

# === CSS MEJORADO PARA BRACKETS ORDENADOS ===
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
    }
    
    .glass-card {
        background: rgba(18, 18, 26, 0.7);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.03);
        border-radius: 24px;
        padding: 30px;
        margin: 20px 0;
    }
    
    /* NUEVO CSS PARA BRACKETS ORDENADOS */
    .bracket-tree {
        position: relative;
        width: 100%;
        overflow-x: auto;
        overflow-y: visible;
        min-height: 800px;
        padding: 40px 0;
        background: rgba(0,0,0,0.3);
        border-radius: 16px;
    }
    
    .bracket-tree-container {
        position: relative;
        display: flex;
        flex-direction: row;
        gap: 100px;
        min-width: max-content;
        padding: 20px;
    }
    
    .bracket-round-column {
        position: relative;
        width: 300px;
        min-height: 800px;
    }
    
    .bracket-round-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #ff2b2b;
        text-align: center;
        padding: 10px;
        margin-bottom: 30px;
        border-bottom: 2px solid #ff2b2b;
        position: sticky;
        top: 0;
        background: rgba(10,10,15,0.9);
        z-index: 10;
        border-radius: 8px 8px 0 0;
    }
    
    .bracket-match {
        position: absolute;
        width: 280px;
        background: linear-gradient(145deg, #1a1a24, #12121a);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 15px;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        left: 10px;
    }
    
    .bracket-match:hover {
        transform: scale(1.02);
        border-color: #ff2b2b;
        z-index: 100;
        box-shadow: 0 8px 25px rgba(255,43,43,0.2);
    }
    
    .bracket-match.completed {
        border-color: gold;
        opacity: 0.9;
    }
    
    .bracket-match.ready {
        border-color: #00ff88;
        box-shadow: 0 0 20px rgba(0,255,136,0.2);
    }
    
    .bracket-competitor {
        padding: 8px 12px;
        border-radius: 6px;
        margin: 5px 0;
        background: rgba(0,0,0,0.3);
    }
    
    .bracket-competitor.red {
        border-left: 4px solid #ff2b2b;
    }
    
    .bracket-competitor.blue {
        border-left: 4px solid #1e90ff;
    }
    
    .bracket-competitor.winner {
        background: rgba(255,215,0,0.15);
        border-left-color: gold;
    }
    
    .competitor-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: white;
    }
    
    .bracket-dojo {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.4);
        margin-top: 2px;
    }
    
    .bracket-id {
        position: absolute;
        top: -8px;
        right: 10px;
        background: #ff2b2b;
        color: white;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
        z-index: 5;
    }
    
    .bracket-vs {
        text-align: center;
        font-size: 0.7rem;
        color: rgba(255,255,255,0.3);
        margin: 2px 0;
        font-weight: 600;
    }
    
    .bracket-bye {
        background: rgba(255,215,0,0.1);
        color: gold;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 20px;
        display: inline-block;
        margin: 5px 0;
    }
    
    .status-badge {
        position: absolute;
        top: -8px;
        left: 10px;
        font-size: 0.6rem;
        padding: 2px 8px;
        border-radius: 20px;
        background: #666;
        color: white;
        z-index: 5;
    }
    
    .status-badge.completed {
        background: gold;
        color: black;
    }
    
    .status-badge.ready {
        background: #00ff88;
        color: black;
    }
    
    .status-badge.auto {
        background: #ff2b2b;
        color: white;
    }
    
    /* Líneas conectoras */
    .connector-line {
        position: absolute;
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, #ff2b2b, transparent);
        top: 50%;
        right: -100px;
    }
    
    .connector-line.left {
        background: linear-gradient(90deg, transparent, #ff2b2b);
        left: -100px;
    }
    
    .connector-line.right {
        background: linear-gradient(90deg, #ff2b2b, transparent);
        right: -100px;
    }
    
    /* Leyenda mejorada */
    .legend {
        display: flex;
        gap: 30px;
        justify-content: center;
        flex-wrap: wrap;
        margin: 30px 0;
        padding: 20px;
        background: rgba(18, 18, 26, 0.5);
        border-radius: 50px;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        color: rgba(255,255,255,0.8);
        font-size: 0.8rem;
    }
    
    .legend-color {
        width: 16px;
        height: 16px;
        border-radius: 4px;
    }
    
    .legend-color.red { background: #ff2b2b; }
    .legend-color.blue { background: #1e90ff; }
    .legend-color.gold { background: gold; }
    .legend-color.green { background: #00ff88; }
    
    /* Estilo para carga masiva */
    .upload-area {
        border: 2px dashed #ff2b2b;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        background: rgba(255,43,43,0.05);
        margin: 20px 0;
    }
    
    .total-grupal {
        font-size: 1.5rem;
        font-weight: 800;
        color: #00ff88;
        text-align: center;
        padding: 20px;
        background: linear-gradient(145deg, #12121a, #1a1a24);
        border-radius: 16px;
        margin: 20px 0;
    }
    
    .metric-container {
        background: linear-gradient(145deg, #12121a, #0a0a0f);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #ff2b2b, #ff5555) !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        transition: all 0.3s !important;
    }
    
    .admin-button > button {
        background: linear-gradient(135deg, #ff8c00, #ff2b2b) !important;
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 DASHBOARD", "📝 INSCRIPCIÓN", "📦 INSCRIPCIÓN GRUPAL", "🏆 BRACKETS", "⚡ ADMIN"])

# ========== TAB 1: DASHBOARD (igual) ==========
with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
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
        
        # Inscripciones grupales
        grupos = df_conf[df_conf['Metodo'] == 'GRUPAL']['Grupo_ID'].nunique()
        st.markdown(f"**Inscripciones grupales:** {grupos} grupos")
        
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
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 2: INSCRIPCIÓN INDIVIDUAL (igual) ==========
with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Inscripción Individual")
    
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
            ["Código VIP", "Transferencia", "Pagar después"],
            horizontal=True
        )
        
        codigo_vip = ""
        if metodo_pago == "Código VIP":
            codigo_vip = st.text_input("Código VIP", type="password")
        
        terminos = st.checkbox("Acepto los términos y condiciones")
        
        submitted = st.form_submit_button("INSCRIBIRSE")
        
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
                datos = {
                    'id': generar_id(nombre, email),
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono,
                    'edad': edad,
                    'dojo': dojo,
                    'pais': pais,
                    'categoria': categoria,
                    'metodo': 'VIP' if metodo_pago == "Código VIP" else 'Individual',
                    'grupo_id': ''
                }
                
                if guardar_inscripcion(datos):
                    st.balloons()
                    st.success("✅ ¡Inscripción exitosa!")
                    time.sleep(2)
                    st.rerun()
            else:
                for error in errores:
                    st.error(error)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 3: INSCRIPCIÓN GRUPAL (NUEVO) ==========
with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📦 Inscripción Grupal")
    st.markdown("Carga múltiples participantes con un solo pago")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Beneficios")
        st.markdown(f"""
        - Precio por persona: **{formatear_peso(PRECIO_GRUPAL)} CLP**
        - Ahorro: **{formatear_peso(PRECIO - PRECIO_GRUPAL)} CLP** por persona
        - Pago único para todo el grupo
        - Ideal para dojos y equipos
        """)
    
    with col2:
        st.markdown("#### 📋 Formato requerido")
        st.markdown("""
        Sube un archivo CSV o Excel con las columnas:
        - **Nombre** (completo)
        - **Email** (válido)
        - **Telefono** (con código país)
        - **Edad** (18-99)
        - **Dojo** (nombre del dojo)
        - **Pais** (opcional, default Chile)
        - **Categoria** (de la lista)
        """)
        
        # Template de descarga
        template_df = pd.DataFrame({
            'Nombre': ['Juan Pérez', 'María González'],
            'Email': ['juan@email.com', 'maria@email.com'],
            'Telefono': ['+56912345678', '+56987654321'],
            'Edad': [25, 24],
            'Dojo': ['SHOTOKAN CENTRAL', 'SHOTOKAN CENTRAL'],
            'Pais': ['Chile', 'Chile'],
            'Categoria': ['KUMITE -65kg (18+)', 'KUMITE -55kg (18+) Femenino']
        })
        
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            "📥 DESCARGAR TEMPLATE",
            csv_template,
            "template_inscripcion_grupal.csv",
            "text/csv"
        )
    
    st.markdown("---")
    
    # Área de carga
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    archivo = st.file_uploader(
        "Arrastra o selecciona archivo CSV/Excel",
        type=['csv', 'xlsx', 'xls']
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if archivo is not None:
        try:
            # Leer archivo
            if archivo.name.endswith('.csv'):
                df_carga = pd.read_csv(archivo)
            else:
                df_carga = pd.read_excel(archivo)
            
            st.markdown("#### 📋 Vista previa de datos")
            st.dataframe(df_carga.head(10), use_container_width=True)
            
            # Generar ID de grupo
            if st.button("🔄 PROCESAR INSCRIPCIÓN GRUPAL"):
                with st.spinner("Procesando inscripciones..."):
                    grupo_id = generar_id_grupal(f"GRUPO_{datetime.now()}")
                    
                    # Procesar datos
                    df_nuevas, errores = procesar_inscripciones_masivas(df_carga, grupo_id)
                    
                    if errores:
                        st.error("❌ Errores encontrados:")
                        for error in errores[:10]:  # Mostrar primeros 10 errores
                            st.warning(error)
                    
                    if not df_nuevas.empty:
                        # Calcular total
                        total_personas = len(df_nuevas)
                        total_pagar = total_personas * PRECIO_GRUPAL
                        
                        st.markdown(f"""
                        <div class="total-grupal">
                            ✅ {total_personas} inscripciones válidas<br>
                            Total a pagar: {formatear_peso(total_pagar)} CLP
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Confirmar pago
                        if st.button("💳 CONFIRMAR PAGO Y GUARDAR", type="primary"):
                            if guardar_inscripciones_masivas(df_nuevas):
                                st.balloons()
                                st.success(f"✅ {total_personas} inscripciones guardadas exitosamente!")
                                st.info(f"💰 Total a pagar: {formatear_peso(total_pagar)} CLP")
                                time.sleep(2)
                                st.rerun()
        
        except Exception as e:
            st.error(f"Error al leer archivo: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 4: BRACKETS (MEJORADO) ==========
with tab4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🏆 Brackets del Torneo")
    
    # Verificar admin
    is_admin = False
    with st.expander("🔐 Acceso Admin", expanded=False):
        admin_pass = st.text_input("Contraseña Admin", type="password", key="admin_pass_brackets")
        is_admin = verificar_admin(admin_pass)
    
    # Panel de generación (solo admin)
    if is_admin:
        st.markdown("#### ⚙️ Generar Brackets")
        
        df_insc = leer_inscripciones()
        df_conf = df_insc[df_insc['Estado'] == 'CONFIRMADO']
        
        # Mostrar resumen por categoría
        st.markdown("**Competidores por categoría:**")
        for cat in CATEGORIAS:
            count = len(df_conf[df_conf['Categoria'] == cat])
            if count >= 2:
                st.markdown(f"✅ {cat}: {count} competidores")
            else:
                st.markdown(f"❌ {cat}: {count} competidores (mínimo 2)")
        
        if st.button("⚡ GENERAR BRACKETS ORDENADOS", use_container_width=True):
            with st.spinner("Generando brackets..."):
                todos_partidos = []
                
                for categoria in CATEGORIAS:
                    df_cat = df_conf[df_conf['Categoria'] == categoria]
                    if len(df_cat) >= 2:
                        partidos_cat = generar_brackets_ordenados(df_cat, categoria)
                        todos_partidos.extend(partidos_cat)
                
                if todos_partidos:
                    df_brackets = pd.DataFrame(todos_partidos)
                    if guardar_brackets(df_brackets):
                        st.success("✅ Brackets generados exitosamente!")
                        st.rerun()
                else:
                    st.warning("No hay suficientes competidores")
    
    # Mostrar brackets
    df_brackets = leer_brackets()
    
    if not df_brackets.empty:
        categorias = df_brackets['Categoria'].unique()
        categoria_sel = st.selectbox("📂 Seleccionar Categoría", categorias)
        
        df_cat = df_brackets[df_brackets['Categoria'] == categoria_sel]
        
        if not df_cat.empty:
            # Mostrar brackets ordenados
            html_brackets = visualizar_brackets_ordenados(df_cat)
            st.markdown(html_brackets, unsafe_allow_html=True)
            
            # Leyenda
            st.markdown("""
            <div class="legend">
                <div class="legend-item"><div class="legend-color red"></div> Aka (Rojo)</div>
                <div class="legend-item"><div class="legend-color blue"></div> Ao (Azul)</div>
                <div class="legend-item"><div class="legend-color gold"></div> Ganador</div>
                <div class="legend-item"><div class="legend-color green"></div> Listo</div>
                <div class="legend-item">⚡ Automático</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Partidos listos (solo admin)
            if is_admin:
                partidos_listos = df_cat[
                    (df_cat['Competidor1_Nombre'] != "BYE") &
                    (df_cat['Competidor2_Nombre'] != "BYE") &
                    (df_cat['Ganador_Nombre'] == "")
                ].sort_values(['Ronda', 'Posicion'])
                
                if not partidos_listos.empty:
                    st.markdown("#### ⚔️ Partidos Listos")
                    for _, p in partidos_listos.iterrows():
                        col1, col2, col3 = st.columns([2, 2, 1])
                        with col1:
                            st.markdown(f"**{p['Competidor1_Nombre']}**")
                        with col2:
                            st.markdown(f"**{p['Competidor2_Nombre']}**")
                        with col3:
                            if st.button(f"✓ #{p['Partido_ID']}", key=f"win_{p['Partido_ID']}"):
                                # Implementar selector de ganador
                                st.session_state['edit_partido'] = p['Partido_ID']
                        
                        if 'edit_partido' in st.session_state and st.session_state['edit_partido'] == p['Partido_ID']:
                            ganador = st.radio(
                                "Ganador",
                                [p['Competidor1_Nombre'], p['Competidor2_Nombre']],
                                key=f"radio_{p['Partido_ID']}"
                            )
                            if st.button("Confirmar", key=f"conf_{p['Partido_ID']}"):
                                # Actualizar ganador
                                df_brackets.loc[
                                    (df_brackets['Categoria'] == categoria_sel) & 
                                    (df_brackets['Partido_ID'] == p['Partido_ID']), 
                                    ['Ganador_Nombre', 'Estado_Partido']
                                ] = [ganador, 'COMPLETADO']
                                guardar_brackets(df_brackets)
                                st.rerun()
    
    else:
        st.info("📌 No hay brackets generados")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== TAB 5: ADMIN (MEJORADO) ==========
with tab5:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ⚡ Panel de Administración")
    
    password = st.text_input("Contraseña", type="password", key="admin_pass_main")
    
    if verificar_admin(password):
        tabs_admin = st.tabs(["📋 Inscripciones", "🏆 Gestión de Brackets", "📊 Estadísticas", "📦 Inscripciones Grupales"])
        
        with tabs_admin[0]:
            df_admin = leer_inscripciones()
            if not df_admin.empty:
                st.dataframe(df_admin, use_container_width=True, hide_index=True)
                csv = df_admin.to_csv(index=False)
                st.download_button("📥 DESCARGAR CSV", csv, "inscripciones.csv")
        
        with tabs_admin[1]:
            df_b = leer_brackets()
            if not df_b.empty:
                st.dataframe(df_b, use_container_width=True, hide_index=True)
                
                # Editor rápido
                with st.expander("Editar partido"):
                    col1, col2 = st.columns(2)
                    with col1:
                        cat_edit = st.selectbox("Categoría", df_b['Categoria'].unique())
                    with col2:
                        df_cat_edit = df_b[df_b['Categoria'] == cat_edit]
                        partido_edit = st.selectbox("ID Partido", df_cat_edit['Partido_ID'].unique())
                    
                    if partido_edit:
                        partido = df_cat_edit[df_cat_edit['Partido_ID'] == partido_edit].iloc[0]
                        
                        with st.form("edit_partido"):
                            c1 = st.text_input("Competidor 1", partido['Competidor1_Nombre'])
                            c2 = st.text_input("Competidor 2", partido['Competidor2_Nombre'])
                            ganador = st.text_input("Ganador", partido['Ganador_Nombre'])
                            
                            if st.form_submit_button("Actualizar"):
                                df_b.loc[
                                    (df_b['Categoria'] == cat_edit) & 
                                    (df_b['Partido_ID'] == partido_edit),
                                    ['Competidor1_Nombre', 'Competidor2_Nombre', 'Ganador_Nombre']
                                ] = [c1, c2, ganador]
                                guardar_brackets(df_b)
                                st.rerun()
                
                if st.button("⚠️ REINICIAR BRACKETS"):
                    df_vacio = pd.DataFrame(columns=df_b.columns)
                    guardar_brackets(df_vacio)
                    st.rerun()
        
        with tabs_admin[2]:
            df_stats = leer_inscripciones()
            if not df_stats.empty:
                df_conf = df_stats[df_stats['Estado'] == 'CONFIRMADO']
                
                col1, col2, col3 = st.columns(3)
                total_individual = len(df_conf[df_conf['Metodo'] == 'Individual']) * PRECIO
                total_grupal = len(df_conf[df_conf['Metodo'] == 'GRUPAL']) * PRECIO_GRUPAL
                total = total_individual + total_grupal
                
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
        
        with tabs_admin[3]:
            st.markdown("#### 📦 Inscripciones Grupales")
            df_grupos = leer_inscripciones()
            df_grupos = df_grupos[df_grupos['Metodo'] == 'GRUPAL']
            
            if not df_grupos.empty:
                for grupo in df_grupos['Grupo_ID'].unique():
                    df_grupo = df_grupos[df_grupos['Grupo_ID'] == grupo]
                    with st.expander(f"Grupo: {grupo} ({len(df_grupo)} personas)"):
                        st.dataframe(df_grupo[['Nombre', 'Categoria', 'Dojo']])
    
    elif password:
        st.error("❌ Contraseña incorrecta")
    
    st.markdown('</div>', unsafe_allow_html=True)

# === FOOTER ===
st.markdown("""
<div class="footer">
    <p>© 2024 World Kyokushin Budokai Chile · Todos los derechos reservados</p>
</div>
""", unsafe_allow_html=True)
