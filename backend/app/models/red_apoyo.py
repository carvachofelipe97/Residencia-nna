"""
Modelos de Red de Apoyo Avanzada
Incluye: familia extensa, cuidadores temporales, PPF, referentes, contactos emergencia
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime, date
from bson import ObjectId


class Direccion(BaseModel):
    """Dirección completa"""
    calle: Optional[str] = None
    numero: Optional[str] = None
    departamento: Optional[str] = None
    comuna: Optional[str] = None
    region: Optional[str] = None
    codigo_postal: Optional[str] = None
    
    def __str__(self):
        parts = [p for p in [self.calle, self.numero, self.departamento, self.comuna, self.region] if p]
        return ", ".join(parts) if parts else ""


class RedApoyoBase(BaseModel):
    """Base del modelo de red de apoyo"""
    nna_id: str = Field(..., description="ID del NNA asociado")
    
    # Datos personales
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    rut: Optional[str] = Field(None, description="RUT chileno")
    fecha_nacimiento: Optional[date] = None
    
    # Contacto
    telefono_principal: str = Field(..., min_length=8, max_length=20)
    telefono_secundario: Optional[str] = None
    email: Optional[str] = None
    
    # Dirección
    direccion: Optional[Direccion] = None
    
    # Tipo de vínculo
    tipo_vinculo: Literal[
        "madre", "padre", "hermano", "hermana",
        "abuela", "abuelo", "tia", "tio",
        "primo", "prima", "padrastro", "madrastra",
        "tutor_legal", "cuidador_temporal",
        "ppf",  # Programa de Protección Familiar
        "referente_significativo", "vecino", "otro"
    ]
    
    # Detalle del vínculo
    descripcion_vinculo: Optional[str] = Field(None, max_length=500)
    
    # Rol específico
    es_cuidador_temporal: bool = False
    es_ppf: bool = False  # Programa de Protección Familiar
    es_contacto_emergencia: bool = False
    es_referente_significativo: bool = False
    
    # Disponibilidad
    disponibilidad: Literal[
        "24_horas", "diurna", "vespertina", "fines_semana", 
        "horario_especifico", "limitada", "no_disponible"
    ] = "limitada"
    horario_especifico: Optional[str] = None
    
    # Nivel de confiabilidad (evaluación institucional)
    nivel_confiabilidad: Literal["alto", "medio", "bajo", "no_evaluado"] = "no_evaluado"
    
    # Motivo de confiabilidad
    evaluacion_confiabilidad: Optional[str] = Field(None, max_length=1000)
    
    # Estado
    estado: Literal["activo", "inactivo", "pendiente_evaluacion", "rechazado"] = "activo"
    
    # Observaciones
    observaciones: Optional[str] = Field(None, max_length=2000)
    
    # Documentos asociados
    tiene_antecedentes: Optional[bool] = None
    autorizado_para_retiro: bool = False
    autorizado_para_informacion: bool = False
    
    # Fechas importantes
    fecha_inicio_vinculo: Optional[date] = None
    fecha_fin_vinculo: Optional[date] = None
    fecha_ultima_evaluacion: Optional[date] = None
    
    # Profesional que evaluó
    evaluado_por: Optional[str] = None


class RedApoyoCreate(RedApoyoBase):
    """Modelo para crear red de apoyo"""
    pass


class RedApoyoUpdate(BaseModel):
    """Modelo para actualizar red de apoyo"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido: Optional[str] = Field(None, min_length=2, max_length=100)
    rut: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    telefono_principal: Optional[str] = Field(None, min_length=8, max_length=20)
    telefono_secundario: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[Direccion] = None
    tipo_vinculo: Optional[str] = None
    descripcion_vinculo: Optional[str] = Field(None, max_length=500)
    es_cuidador_temporal: Optional[bool] = None
    es_ppf: Optional[bool] = None
    es_contacto_emergencia: Optional[bool] = None
    es_referente_significativo: Optional[bool] = None
    disponibilidad: Optional[str] = None
    horario_especifico: Optional[str] = None
    nivel_confiabilidad: Optional[str] = None
    evaluacion_confiabilidad: Optional[str] = Field(None, max_length=1000)
    estado: Optional[str] = None
    observaciones: Optional[str] = Field(None, max_length=2000)
    tiene_antecedentes: Optional[bool] = None
    autorizado_para_retiro: Optional[bool] = None
    autorizado_para_informacion: Optional[bool] = None
    fecha_inicio_vinculo: Optional[date] = None
    fecha_fin_vinculo: Optional[date] = None
    fecha_ultima_evaluacion: Optional[date] = None
    evaluado_por: Optional[str] = None


class RedApoyoInDB(RedApoyoBase):
    """Modelo red de apoyo en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: str
    
    class Config:
        populate_by_name = True


class RedApoyoResponse(RedApoyoInDB):
    """Modelo de respuesta red de apoyo"""
    pass


class RedApoyo(BaseModel):
    """Modelo simplificado de red de apoyo"""
    id: str
    nna_id: str
    nombre_completo: str
    tipo_vinculo: str
    telefono_principal: str
    es_cuidador_temporal: bool
    es_ppf: bool
    es_contacto_emergencia: bool
    nivel_confiabilidad: str
    estado: str


# Modelos para búsqueda y filtros
class RedApoyoFiltros(BaseModel):
    """Filtros para búsqueda de red de apoyo"""
    nna_id: Optional[str] = None
    tipo_vinculo: Optional[str] = None
    es_cuidador_temporal: Optional[bool] = None
    es_ppf: Optional[bool] = None
    es_contacto_emergencia: Optional[bool] = None
    nivel_confiabilidad: Optional[str] = None
    estado: Optional[str] = None
    search: Optional[str] = None


# Estadísticas de red de apoyo
class RedApoyoStats(BaseModel):
    """Estadísticas de red de apoyo"""
    total: int
    por_tipo_vinculo: dict
    cuidadores_temporales: int
    ppf: int
    contactos_emergencia: int
    por_nivel_confiabilidad: dict
    por_estado: dict
