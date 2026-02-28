"""
Modelos de Talleres
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from bson import ObjectId


class ParticipanteTaller(BaseModel):
    """Participante de un taller"""
    nna_id: str
    asistencia: bool = False
    evaluacion: Optional[str] = None
    observaciones: Optional[str] = None


class TallerBase(BaseModel):
    """Base del modelo de taller"""
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = None
    
    # Fechas
    fecha: date
    hora_inicio: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    hora_termino: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    
    # Ubicación
    ubicacion: Optional[str] = None
    
    # Información
    objetivos: Optional[str] = None
    materiales: Optional[str] = None
    
    # Responsable
    responsable_id: str
    
    # Participantes
    participantes: List[ParticipanteTaller] = []
    capacidad_maxima: int = Field(default=20, ge=1, le=100)
    
    # Estado
    estado: str = "programado"  # programado, en_curso, completado, cancelado


class TallerCreate(TallerBase):
    """Modelo para crear taller"""
    pass


class TallerUpdate(BaseModel):
    """Modelo para actualizar taller"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = None
    fecha: Optional[date] = None
    hora_inicio: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    hora_termino: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    ubicacion: Optional[str] = None
    objetivos: Optional[str] = None
    materiales: Optional[str] = None
    responsable_id: Optional[str] = None
    participantes: Optional[List[ParticipanteTaller]] = None
    capacidad_maxima: Optional[int] = Field(None, ge=1, le=100)
    estado: Optional[str] = None


class TallerInDB(TallerBase):
    """Modelo taller en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: str
    
    class Config:
        populate_by_name = True


class TallerResponse(TallerInDB):
    """Modelo de respuesta taller"""
    pass


class Taller(BaseModel):
    """Modelo completo de taller"""
    id: str
    nombre: str
    fecha: date
    hora_inicio: str
    hora_termino: str
    estado: str
    participantes_count: int
    creado_en: datetime
