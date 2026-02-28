"""
Modelos de Módulo Jurídico
Incluye: medidas judiciales, audiencias, restricciones, plazos legales
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from bson import ObjectId


class Audiencia(BaseModel):
    """Audiencia relacionada a una medida"""
    fecha: date
    hora: Optional[str] = None
    tribunal: Optional[str] = None
    juez: Optional[str] = None
    resultado: Optional[str] = None
    observaciones: Optional[str] = None
    asistio_nna: Optional[bool] = None
    asistio_representante: Optional[bool] = None


class MedidaJudicialBase(BaseModel):
    """Base del modelo de medida judicial"""
    nna_id: str = Field(..., description="ID del NNA")
    
    # Información de la solicitud
    numero_ingreso: Optional[str] = None  # Número de ingreso al tribunal
    fecha_solicitud: date
    tipo_solicitud: Literal[
        "ingreso_residencia",
        "proteccion_simple",
        "proteccion_compleja",
        "restitucion_derechos",
        "adopcion",
        "tutela",
        "otra"
    ]
    
    # Solicitante
    solicitante: Optional[str] = None
    rol_solicitante: Optional[Literal["sename", "juzgado", "familia", "otro"]] = None
    
    # Audiencias
    audiencias: List[Audiencia] = []
    
    # Resolución
    fecha_resolucion: Optional[date] = None
    numero_resolucion: Optional[str] = None
    
    # Tipo de medida dictada
    tipo_medida: Optional[Literal[
        "proteccion_simple",
        "proteccion_compleja",
        "restitucion_derechos",
        "adopcion_nacional",
        "adopcion_internacional",
        "tutela",
        "acogimiento_familiar",
        "acogimiento_residencial",
        "otra"
    ]] = None
    
    # Vigencia
    fecha_inicio: Optional[date] = None
    fecha_termino: Optional[date] = None
    plazo_meses: Optional[int] = None
    
    # Estado
    estado: Literal["solicitada", "en_tramite", "dictada", "vigente", "cumplida", "revocada", "apelada"] = "solicitada"
    
    # Restricciones
    restriccion_contacto: bool = False
    restriccion_acercamiento: bool = False
    restriccion_salida_territorio: bool = False
    otras_restricciones: Optional[str] = None
    
    # Medidas complementarias
    medidas_complementarias: Optional[List[str]] = []
    
    # Observaciones
    observaciones: Optional[str] = Field(None, max_length=2000)
    
    # Seguimiento
    requiere_seguimiento: bool = False
    frecuencia_seguimiento: Optional[Literal["semanal", "quincenal", "mensual", "trimestral", "semestral"]] = None
    
    # Alerta de vencimiento
    alerta_dias_anticipacion: int = 30


class MedidaJudicialCreate(MedidaJudicialBase):
    """Modelo para crear medida judicial"""
    pass


class MedidaJudicialUpdate(BaseModel):
    """Modelo para actualizar medida judicial"""
    numero_ingreso: Optional[str] = None
    fecha_solicitud: Optional[date] = None
    tipo_solicitud: Optional[str] = None
    solicitante: Optional[str] = None
    rol_solicitante: Optional[str] = None
    audiencias: Optional[List[Audiencia]] = None
    fecha_resolucion: Optional[date] = None
    numero_resolucion: Optional[str] = None
    tipo_medida: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_termino: Optional[date] = None
    plazo_meses: Optional[int] = None
    estado: Optional[str] = None
    restriccion_contacto: Optional[bool] = None
    restriccion_acercamiento: Optional[bool] = None
    restriccion_salida_territorio: Optional[bool] = None
    otras_restricciones: Optional[str] = None
    medidas_complementarias: Optional[List[str]] = None
    observaciones: Optional[str] = Field(None, max_length=2000)
    requiere_seguimiento: Optional[bool] = None
    frecuencia_seguimiento: Optional[str] = None
    alerta_dias_anticipacion: Optional[int] = None


class MedidaJudicialInDB(MedidaJudicialBase):
    """Modelo medida judicial en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: str
    
    class Config:
        populate_by_name = True


class MedidaJudicialResponse(MedidaJudicialInDB):
    """Modelo de respuesta medida judicial"""
    pass


class MedidaJudicial(BaseModel):
    """Modelo simplificado de medida judicial"""
    id: str
    nna_id: str
    tipo_solicitud: str
    tipo_medida: Optional[str]
    estado: str
    fecha_solicitud: date
    fecha_inicio: Optional[date]
    fecha_termino: Optional[date]
    dias_para_vencimiento: Optional[int] = None
    tiene_restricciones: bool


# Restricción específica (para seguimiento detallado)
class RestriccionBase(BaseModel):
    """Base del modelo de restricción"""
    nna_id: str
    medida_id: Optional[str] = None
    
    tipo: Literal[
        "contacto_familia",
        "acercamiento_persona",
        "salida_pais",
        "salida_region",
        "contacto_menores",
        "acceso_redes_sociales",
        "otra"
    ]
    
    descripcion: str = Field(..., min_length=5, max_length=1000)
    
    # Personas involucradas (si aplica)
    persona_restringida_nombre: Optional[str] = None
    persona_restringida_rut: Optional[str] = None
    relacion_con_nna: Optional[str] = None
    
    # Vigencia
    fecha_inicio: date
    fecha_termino: Optional[date] = None
    indefinida: bool = False
    
    # Estado
    estado: Literal["activa", "suspendida", "cumplida", "revocada"] = "activa"
    
    # Motivo
    motivo: Optional[str] = Field(None, max_length=1000)
    
    # Observaciones
    observaciones: Optional[str] = Field(None, max_length=2000)


class RestriccionCreate(RestriccionBase):
    """Modelo para crear restricción"""
    pass


class RestriccionUpdate(BaseModel):
    """Modelo para actualizar restricción"""
    tipo: Optional[str] = None
    descripcion: Optional[str] = Field(None, min_length=5, max_length=1000)
    persona_restringida_nombre: Optional[str] = None
    persona_restringida_rut: Optional[str] = None
    relacion_con_nna: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_termino: Optional[date] = None
    indefinida: Optional[bool] = None
    estado: Optional[str] = None
    motivo: Optional[str] = Field(None, max_length=1000)
    observaciones: Optional[str] = Field(None, max_length=2000)


class RestriccionInDB(RestriccionBase):
    """Modelo restricción en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: str
    
    class Config:
        populate_by_name = True


class RestriccionResponse(RestriccionInDB):
    """Modelo de respuesta restricción"""
    pass


# Estadísticas jurídicas
class JuridicoStats(BaseModel):
    """Estadísticas del módulo jurídico"""
    total_medidas: int
    por_estado: dict
    por_tipo_solicitud: dict
    por_tipo_medida: dict
    vigentes: int
    con_restricciones: int
    proximas_a_vencer: int
    vencidas: int
    total_restricciones: int
    restricciones_activas: int


# Alerta de vencimiento
class AlertaVencimiento(BaseModel):
    """Alerta de vencimiento de medida"""
    medida_id: str
    nna_id: str
    nna_nombre: str
    tipo_medida: str
    fecha_vencimiento: date
    dias_restantes: int
    prioridad: str  # alta, media, baja
