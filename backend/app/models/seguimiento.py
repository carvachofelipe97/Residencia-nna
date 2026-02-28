"""
Modelos de Seguimiento
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from bson import ObjectId


class SeguimientoBase(BaseModel):
    """Base del modelo de seguimiento"""
    nna_id: str = Field(..., description="ID del NNA")
    fecha: date
    
    # Tipo de seguimiento
    tipo: Literal["semanal", "mensual", "trimestral", "anual", "especial"] = "mensual"
    
    # Áreas de evaluación
    area_salud: Optional[str] = None
    area_educativa: Optional[str] = None
    area_social: Optional[str] = None
    area_familiar: Optional[str] = None
    area_emocional: Optional[str] = None
    
    # Evaluación general
    evaluacion_general: str = Field(..., min_length=10)
    fortalezas: Optional[str] = None
    dificultades: Optional[str] = None
    
    # Objetivos
    objetivos_corto_plazo: Optional[str] = None
    objetivos_medio_plazo: Optional[str] = None
    objetivos_largo_plazo: Optional[str] = None
    
    # Recomendaciones
    recomendaciones: Optional[str] = None
    
    # Estado del seguimiento
    estado: Literal["pendiente", "en_proceso", "completado"] = "pendiente"


class SeguimientoCreate(SeguimientoBase):
    """Modelo para crear seguimiento"""
    pass


class SeguimientoUpdate(BaseModel):
    """Modelo para actualizar seguimiento"""
    fecha: Optional[date] = None
    tipo: Optional[Literal["semanal", "mensual", "trimestral", "anual", "especial"]] = None
    area_salud: Optional[str] = None
    area_educativa: Optional[str] = None
    area_social: Optional[str] = None
    area_familiar: Optional[str] = None
    area_emocional: Optional[str] = None
    evaluacion_general: Optional[str] = Field(None, min_length=10)
    fortalezas: Optional[str] = None
    dificultades: Optional[str] = None
    objetivos_corto_plazo: Optional[str] = None
    objetivos_medio_plazo: Optional[str] = None
    objetivos_largo_plazo: Optional[str] = None
    recomendaciones: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_proceso", "completado"]] = None


class SeguimientoInDB(SeguimientoBase):
    """Modelo seguimiento en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: str
    
    class Config:
        populate_by_name = True


class SeguimientoResponse(SeguimientoInDB):
    """Modelo de respuesta seguimiento"""
    pass


class Seguimiento(BaseModel):
    """Modelo completo de seguimiento"""
    id: str
    nna_id: str
    fecha: date
    tipo: str
    evaluacion_general: str
    estado: str
    creado_en: datetime
    creado_por: str
