"""
Modelos de Intervenciones
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from bson import ObjectId


class IntervencionBase(BaseModel):
    """Base del modelo de intervención"""
    nna_id: str = Field(..., description="ID del NNA")
    fecha: date
    tipo: Literal[
        "psicologica", "social", "educativa", "medica", 
        "legal", "familiar", "ocupacional", "otra"
    ]
    
    # Descripción
    motivo: str = Field(..., min_length=5, max_length=500)
    descripcion: str = Field(..., min_length=10)
    
    # Resultados
    resultados: Optional[str] = None
    derivacion: Optional[str] = None
    
    # Estado
    estado: Literal["pendiente", "en_proceso", "completada", "cancelada"] = "pendiente"
    
    # Prioridad
    prioridad: Literal["baja", "media", "alta", "urgente"] = "media"
    
    # Fechas de seguimiento
    fecha_proximo_seguimiento: Optional[date] = None


class IntervencionCreate(IntervencionBase):
    """Modelo para crear intervención"""
    pass


class IntervencionUpdate(BaseModel):
    """Modelo para actualizar intervención"""
    fecha: Optional[date] = None
    tipo: Optional[Literal[
        "psicologica", "social", "educativa", "medica", 
        "legal", "familiar", "ocupacional", "otra"
    ]] = None
    motivo: Optional[str] = Field(None, min_length=5, max_length=500)
    descripcion: Optional[str] = Field(None, min_length=10)
    resultados: Optional[str] = None
    derivacion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_proceso", "completada", "cancelada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta", "urgente"]] = None
    fecha_proximo_seguimiento: Optional[date] = None


class IntervencionInDB(IntervencionBase):
    """Modelo intervención en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: str
    actualizado_por: Optional[str] = None
    
    class Config:
        populate_by_name = True


class IntervencionResponse(IntervencionInDB):
    """Modelo de respuesta intervención"""
    pass


class Intervencion(BaseModel):
    """Modelo completo de intervención"""
    id: str
    nna_id: str
    fecha: date
    tipo: str
    motivo: str
    estado: str
    prioridad: str
    creado_en: datetime
    creado_por: str
