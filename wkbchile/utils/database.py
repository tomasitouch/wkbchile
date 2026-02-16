import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import logging

logger = logging.getLogger(__name__)

# Constantes
PRECIO_INSCRIPCION = 15000
SHEET_URL = st.secrets["connections.gsheets"]["spreadsheet"]

@st.cache_resource
def get_connection():
    """Obtiene la conexión a Google Sheets"""
    return st.connection("gsheets", type=GSheetsConnection)

def cargar_inscripciones():
    """Carga las inscripciones existentes"""
    try:
        conn = get_connection()
        return conn.read(worksheet="Inscripciones")
    except Exception as e:
        logger.error(f"Error cargando inscripciones: {e}")
        return pd.DataFrame()

def guardar_inscripcion(datos):
    """Guarda una nueva inscripción en sheets"""
    try:
        conn = get_connection()
        df_existente = cargar_inscripciones()
        
        nueva_fila = pd.DataFrame([datos])
        df_final = pd.concat([df_existente, nueva_fila], ignore_index=True) if not df_existente.empty else nueva_fila
        
        conn.update(worksheet="Inscripciones", data=df_final)
        
        # Backup
        try:
            conn.update(worksheet="Backup", data=df_final)
        except:
            pass
            
        return True
    except Exception as e:
        logger.error(f"Error guardando inscripción: {e}")
        return False

def guardar_pago(datos_pago):
    """Guarda información del pago"""
    try:
        conn = get_connection()
        df_pagos = conn.read(worksheet="Pagos")
        
        nueva_fila = pd.DataFrame([datos_pago])
        df_final = pd.concat([df_pagos, nueva_fila], ignore_index=True) if not df_pagos.empty else nueva_fila
        
        conn.update(worksheet="Pagos", data=df_final)
        return True
    except Exception as e:
        logger.error(f"Error guardando pago: {e}")
        return False

def obtener_estadisticas():
    """Obtiene estadísticas del torneo"""
    df = cargar_inscripciones()
    if df.empty:
        return {
            "total": 0,
            "confirmados": 0,
            "pendientes": 0,
            "categorias": 0,
            "dojos": 0,
            "recaudado": 0
        }
    
    confirmados = df[df['Estado_Pago'] == 'Confirmado']
    
    return {
        "total": len(df),
        "confirmados": len(confirmados),
        "pendientes": len(df[df['Estado_Pago'] != 'Confirmado']),
        "categorias": len(confirmados['Categoria'].unique()) if not confirmados.empty else 0,
        "dojos": len(confirmados['Dojo'].unique()) if not confirmados.empty else 0,
        "recaudado": len(confirmados) * PRECIO_INSCRIPCION
    }