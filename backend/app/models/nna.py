"""
Modelos de NNA (Niños, Niñas y Adolescentes)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from bson import ObjectId


class NNAContacto(BaseModel):
    """Información de contacto"""
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    relacion: Optional[str] = None


class NNABase(BaseModel):
    """Base del modelo NNA"""
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    rut: Optional[str] = Field(None, pattern=r"^\d{1,8}-[\dkK]$")
    fecha_nacimiento: Optional[date] = None
    edad: Optional[int] = Field(None, ge=0, le=21)
    genero: Literal["M", "F", "Otro", "No especifica"] = "No especifica"
    
    # Información de residencia
    fecha_ingreso: date
    fecha_egreso: Optional[date] = None
    estado: Literal["activo", "egresado", "trasladado", "temporal"] = "activo"
    
    # Contacto
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    comuna: Optional[str] = None
    region: Optional[str] = None
    
    # Contacto de emergencia
    contacto_emergencia: Optional[NNAContacto] = None
    
    # Información médica
    alergias: Optional[str] = None
    medicamentos: Optional[str] = None
    condiciones_medicas: Optional[str] = None
    
    # Información educativa
    establecimiento_educacional: Optional[str] = None
    curso: Optional[str] = None
    
    # Observaciones
    observaciones: Optional[str] = None


class NNACreate(NNABase):
    """Modelo para crear NNA"""
    pass


class NNAUpdate(BaseModel):
    """Modelo para actualizar NNA"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    rut: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    edad: Optional[int] = Field(None, ge=0, le=21)
    genero: Optional[Literal["M", "F", "Otro", "No especifica"]] = None
    fecha_egreso: Optional[date] = None
    estado: Optional[Literal["activo", "egresado", "trasladado", "temporal"]] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    comuna: Optional[str] = None
    region: Optional[str] = None
    contacto_emergencia: Optional[NNAContacto] = None
    alergias: Optional[str] = None
    medicamentos: Optional[str] = None
    condiciones_medicas: Optional[str] = None
    establecimiento_educacional: Optional[str] = None
    curso: Optional[str] = None
    observaciones: Optional[str] = None


class NNAInDB(NNABase):
    """Modelo NNA en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: Optional[str] = None
    
    class Config:
        populate_by_name = True


class NNAResponse(NNAInDB):
    """Modelo de respuesta NNA"""
    pass


class NNA(BaseModel):
    """Modelo completo NNA"""
    id: str
    nombre: str
    apellido: str
    rut: Optional[str]
    edad: Optional[int]
    estado: str
    fecha_ingreso: date
    fecha_egreso: Optional[date]
    creado_en: datetime
