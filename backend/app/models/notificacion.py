"""
Modelos de Notificaciones
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from bson import ObjectId


class NotificacionBase(BaseModel):
    """Base del modelo de notificación"""
    usuario_id: str = Field(..., description="ID del usuario destinatario")
    
    # Contenido
    titulo: str = Field(..., min_length=3, max_length=200)
    mensaje: str = Field(..., min_length=5, max_length=1000)
    
    # Tipo y prioridad
    tipo: Literal[
        "sistema", "intervencion", "taller", "seguimiento", 
        "recordatorio", "alerta", "info"
    ] = "info"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    # Enlace relacionado (opcional)
    link: Optional[str] = None
    entidad_tipo: Optional[str] = None  # nna, intervencion, taller, etc.
    entidad_id: Optional[str] = None
    
    # Estado
    leida: bool = False


class NotificacionCreate(NotificacionBase):
    """Modelo para crear notificación"""
    pass


class NotificacionUpdate(BaseModel):
    """Modelo para actualizar notificación"""
    leida: Optional[bool] = None


class NotificacionInDB(NotificacionBase):
    """Modelo notificación en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    leida_en: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class NotificacionResponse(NotificacionInDB):
    """Modelo de respuesta notificación"""
    pass


class Notificacion(BaseModel):
    """Modelo completo de notificación"""
    id: str
    usuario_id: str
    titulo: str
    mensaje: str
    tipo: str
    prioridad: str
    leida: bool
    creado_en: datetime
