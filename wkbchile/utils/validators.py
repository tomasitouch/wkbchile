import re
import uuid

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

def formatear_peso(valor):
    """Formatea un número como pesos chilenos"""
    return f"${valor:,.0f}".replace(",", ".")