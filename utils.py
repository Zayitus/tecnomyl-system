# utils.py - Utilidades del sistema experto
import uuid
from datetime import datetime

def generate_registration_code(legajo, validated=False):
    """Genera un código único de registro"""
    prefix = "REG-" if validated else "PROV-"
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    unique_part = uuid.uuid4().hex[:4].upper()
    return f"{prefix}{legajo}-{timestamp}-{unique_part}"

def format_employee_name(nombre_completo):
    """Formatea el nombre del empleado separando apellido y nombre"""
    if ',' in nombre_completo:
        return nombre_completo  # Ya tiene formato "Apellido, Nombre"
    
    # Asume que el último espacio separa apellido de nombre
    parts = nombre_completo.strip().split()
    if len(parts) >= 2:
        apellido = parts[-1]
        nombre = ' '.join(parts[:-1])
        return f"{apellido}, {nombre}"
    
    return nombre_completo

def validate_legajo_format(legajo):
    """Valida que el legajo tenga el formato correcto"""
    return legajo.isdigit() and len(legajo) >= 4

def get_sector_display_name(sector):
    """Devuelve el nombre completo del sector"""
    sectores = {
        'linea1': 'Línea de Producción 1',
        'linea2': 'Línea de Producción 2', 
        'Mantenimiento': 'Mantenimiento',
        'RH': 'Recursos Humanos'
    }
    return sectores.get(sector, sector)