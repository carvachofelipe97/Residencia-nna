"""
Validadores personalizados
"""
import re


def validate_rut_chile(rut: str) -> bool:
    """
    Validar RUT chileno
    Formato: 12345678-9 o 12345678-K
    """
    if not rut:
        return True  # RUT opcional
    
    # Limpiar el RUT
    rut = rut.upper().replace(".", "").replace("-", "")
    
    if len(rut) < 2:
        return False
    
    # Separar cuerpo y dígito verificador
    cuerpo = rut[:-1]
    dv = rut[-1]
    
    if not cuerpo.isdigit():
        return False
    
    # Calcular dígito verificador
    suma = 0
    multiplo = 2
    
    for d in reversed(cuerpo):
        suma += int(d) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    
    dv_calculado = 11 - (suma % 11)
    
    if dv_calculado == 11:
        dv_calculado = "0"
    elif dv_calculado == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(dv_calculado)
    
    return dv == dv_calculado


def format_rut(rut: str) -> str:
    """
    Formatear RUT chileno
    12345678-9 -> 12.345.678-9
    """
    if not rut:
        return ""
    
    # Limpiar
    rut = rut.upper().replace(".", "").replace("-", "")
    
    if len(rut) < 2:
        return rut
    
    cuerpo = rut[:-1]
    dv = rut[-1]
    
    # Formatear cuerpo con puntos
    cuerpo_formateado = ""
    for i, d in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            cuerpo_formateado = "." + cuerpo_formateado
        cuerpo_formateado = d + cuerpo_formateado
    
    return f"{cuerpo_formateado}-{dv}"


def clean_rut(rut: str) -> str:
    """Limpiar RUT dejando solo números y K"""
    if not rut:
        return ""
    return rut.upper().replace(".", "").replace("-", "")
