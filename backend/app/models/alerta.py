"""
Modelos de Alertas - Sistema de notificaciones y vencimientos
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from bson import ObjectId


class AlertaBase(BaseModel):
    """Base del modelo de alerta"""
    # Referencia
    nna_id: Optional[str] = Field(None, description="ID del NNA relacionado")
    usuario_id: Optional[str] = Field(None, description="ID del usuario destinatario")
    
    # Contenido
    titulo: str = Field(..., min_length=3, max_length=200)
    mensaje: str = Field(..., min_length=5, max_length=1000)
    
    # Tipo de alerta
    tipo: Literal[
        "vencimiento_plazo",      # Vencimiento de plazo legal
        "audiencia_proxima",       # Audiencia próxima
        "revision_medida",         # Revisión de medida
        "seguimiento_pendiente",   # Seguimiento pendiente
        "riesgo_alto",             # Nivel de riesgo alto
        "restriccion_activa",      # Restricción judicial activa
        "taller_proximo",          # Taller próximo
        "documento_faltante",      # Documento faltante
        "intervencion_urgente",    # Intervención urgente
        "sistema",                 # Alerta del sistema
        "otra"
    ]
    
    # Prioridad
    prioridad: Literal["baja", "media", "alta", "critica"] = "media"
    
    # Fechas importantes
    fecha_vencimiento: Optional[date] = None  # Fecha límite para resolver
    fecha_recordatorio: Optional[date] = None  # Cuándo recordar
    
    # Estado
    estado: Literal["activa", "en_proceso", "resuelta", "descartada"] = "activa"
    
    # Enlace relacionado
    entidad_tipo: Optional[str] = None  # nna, intervencion, taller, etc.
    entidad_id: Optional[str] = None
    url_redirect: Optional[str] = None
    
    # Asignación
    asignado_a: Optional[str] = None  # ID del usuario asignado


class AlertaCreate(AlertaBase):
    """Modelo para crear alerta"""
    pass


class AlertaUpdate(BaseModel):
    """Modelo para actualizar alerta"""
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    mensaje: Optional[str] = Field(None, min_length=5, max_length=1000)
    prioridad: Optional[Literal["baja", "media", "alta", "critica"]] = None
    fecha_vencimiento: Optional[date] = None
    fecha_recordatorio: Optional[date] = None
    estado: Optional[Literal["activa", "en_proceso", "resuelta", "descartada"]] = None
    asignado_a: Optional[str] = None


class AlertaInDB(AlertaBase):
    """Modelo alerta en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    resuelta_en: Optional[datetime] = None
    resuelta_por: Optional[str] = None
    creado_por: str
    
    class Config:
        populate_by_name = True


class AlertaResponse(AlertaInDB):
    """Modelo de respuesta alerta"""
    pass


class Alerta(BaseModel):
    """Modelo completo de alerta"""
    id: str
    nna_id: Optional[str]
    titulo: str
    mensaje: str
    tipo: str
    prioridad: str
    estado: str
    fecha_vencimiento: Optional[date]
    creado_en: datetime
    dias_restantes: Optional[int] = None  # Calculado


# Modelos para configuración de alertas automáticas
class ConfigAlertaAutomatica(BaseModel):
    """Configuración para alertas automáticas"""
    tipo: str
    dias_anticipacion: int
    activo: bool = True
    prioridad_default: str = "media"


class AlertaStats(BaseModel):
    """Estadísticas de alertas"""
    total: int
    activas: int
    criticas: int
    vencidas: int
    por_tipo: dict
    por_prioridad: dict
