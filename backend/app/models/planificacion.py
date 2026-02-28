"""
Modelos de Planificación Anual Institucional
Incluye: actividades, talleres, conmemoraciones, indicadores, evidencias
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from bson import ObjectId


class IndicadorCumplimiento(BaseModel):
    """Indicador de cumplimiento de una actividad"""
    nombre: str
    valor_esperado: str
    valor_obtenido: Optional[str] = None
    cumplido: bool = False
    observaciones: Optional[str] = None


class EvidenciaActividad(BaseModel):
    """Evidencia adjunta de una actividad"""
    tipo: Literal["foto", "documento", "video", "audio", "otro"]
    nombre: str
    url: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_subida: datetime = Field(default_factory=datetime.utcnow)
    subido_por: Optional[str] = None


class ParticipanteActividad(BaseModel):
    """Participante de una actividad"""
    nna_id: Optional[str] = None
    usuario_id: Optional[str] = None
    nombre: str
    asistencia: bool = False
    evaluacion: Optional[str] = None
    observaciones: Optional[str] = None


class PlanificacionBase(BaseModel):
    """Base del modelo de planificación anual"""
    # Información básica
    nombre: str = Field(..., min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=2000)
    
    # Tipo de actividad
    tipo: Literal[
        "taller",                    # Taller educativo/capacitación
        "conmemoracion",             # Días conmemorativos (Mujer, Niñez, etc.)
        "intervencion_grupal",       # Intervención grupal
        "actividad_recreativa",      # Actividad recreativa
        "visita_institucional",      # Visita a otra institución
        "reunion_equipo",            # Reunión de equipo
        "capacitacion",              # Capacitación interna
        "evaluacion",                # Evaluación/evaluación
        "otra"
    ]
    
    # Categoría temática
    categoria: Optional[Literal[
        "salud_mental",
        "educacion",
        "derechos_nna",
        "prevencion_violencia",
        "habilidades_sociales",
        "arte_cultura",
        "deporte_recreacion",
        "vida_independiente",
        "otra"
    ]] = None
    
    # Fechas
    fecha_inicio: date
    fecha_termino: Optional[date] = None
    hora_inicio: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    hora_termino: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    
    # Ubicación
    ubicacion: Optional[str] = None
    
    # Responsable
    responsable_id: str  # ID del usuario responsable
    
    # Objetivos
    objetivo_general: Optional[str] = Field(None, max_length=1000)
    objetivos_especificos: Optional[List[str]] = []
    
    # Público objetivo
    dirigido_a: Optional[Literal["nna", "familias", "equipo", "comunidad", "mixto"]] = "nna"
    
    # Participantes
    participantes: List[ParticipanteActividad] = []
    capacidad_maxima: int = Field(default=50, ge=1, le=500)
    
    # Indicadores de cumplimiento
    indicadores: List[IndicadorCumplimiento] = []
    
    # Presupuesto
    presupuesto_estimado: Optional[float] = None
    presupuesto_ejecutado: Optional[float] = None
    
    # Recursos necesarios
    recursos_necesarios: Optional[List[str]] = []
    
    # Estado
    estado: Literal["planificada", "en_preparacion", "en_ejecucion", "realizada", "cancelada", "postergada"] = "planificada"
    
    # Evidencias
    evidencias: List[EvidenciaActividad] = []
    
    # Evaluación
    evaluacion_general: Optional[str] = Field(None, max_length=2000)
    lecciones_aprendidas: Optional[str] = Field(None, max_length=2000)
    recomendaciones: Optional[str] = Field(None, max_length=1000)
    
    # Año de planificación
    anio: int = Field(default_factory=lambda: datetime.now().year)


class PlanificacionCreate(PlanificacionBase):
    """Modelo para crear planificación"""
    pass


class PlanificacionUpdate(BaseModel):
    """Modelo para actualizar planificación"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=2000)
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_termino: Optional[date] = None
    hora_inicio: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    hora_termino: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    ubicacion: Optional[str] = None
    responsable_id: Optional[str] = None
    objetivo_general: Optional[str] = Field(None, max_length=1000)
    objetivos_especificos: Optional[List[str]] = None
    dirigido_a: Optional[str] = None
    participantes: Optional[List[ParticipanteActividad]] = None
    capacidad_maxima: Optional[int] = Field(None, ge=1, le=500)
    indicadores: Optional[List[IndicadorCumplimiento]] = None
    presupuesto_estimado: Optional[float] = None
    presupuesto_ejecutado: Optional[float] = None
    recursos_necesarios: Optional[List[str]] = None
    estado: Optional[str] = None
    evaluacion_general: Optional[str] = Field(None, max_length=2000)
    lecciones_aprendidas: Optional[str] = Field(None, max_length=2000)
    recomendaciones: Optional[str] = Field(None, max_length=1000)


class PlanificacionInDB(PlanificacionBase):
    """Modelo planificación en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None
    creado_por: str
    
    class Config:
        populate_by_name = True


class PlanificacionResponse(PlanificacionInDB):
    """Modelo de respuesta planificación"""
    pass


class Planificacion(BaseModel):
    """Modelo simplificado de planificación"""
    id: str
    nombre: str
    tipo: str
    categoria: Optional[str]
    fecha_inicio: date
    fecha_termino: Optional[date]
    estado: str
    responsable_id: str
    anio: int
    porcentaje_cumplimiento: Optional[float] = None


# Estadísticas de planificación
class PlanificacionStats(BaseModel):
    """Estadísticas de planificación anual"""
    total_actividades: int
    por_estado: dict
    por_tipo: dict
    por_categoria: dict
    por_mes: dict
    porcentaje_cumplimiento_general: float
    presupuesto_total_estimado: float
    presupuesto_total_ejecutado: float
    actividades_proximas: int
    actividades_vencidas: int


# Filtros para búsqueda
class PlanificacionFiltros(BaseModel):
    """Filtros para búsqueda de planificación"""
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    estado: Optional[str] = None
    responsable_id: Optional[str] = None
    anio: Optional[int] = None
    mes: Optional[int] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    search: Optional[str] = None


# Días conmemorativos predefinidos
DIAS_CONMEMORATIVOS = {
    "dia_mujer": {"nombre": "Día Internacional de la Mujer", "fecha": "03-08"},
    "dia_ninez": {"nombre": "Día del Niño", "fecha": "08-09"},
    "dia_nna": {"nombre": "Día del Niño, Niña y Adolescente", "fecha": "09-08"},
    "dia_familia": {"nombre": "Día Internacional de la Familia", "fecha": "15-05"},
    "dia_educacion": {"nombre": "Día de la Educación", "fecha": "11-04"},
    "dia_salud_mental": {"nombre": "Día Mundial de la Salud Mental", "fecha": "10-10"},
    "dia_no_violencia": {"nombre": "Día Internacional de la No Violencia", "fecha": "02-10"},
    "fiestas_patrias": {"nombre": "Fiestas Patrias", "fecha": "09-18"},
    "navidad": {"nombre": "Navidad", "fecha": "12-25"},
    "halloween": {"nombre": "Halloween/Día de las Brujas", "fecha": "10-31"},
    "dia_padre": {"nombre": "Día del Padre", "fecha": "06-16"},
    "dia_madre": {"nombre": "Día de la Madre", "fecha": "05-12"},
}
