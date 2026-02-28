"""
Router de Planificación Anual Institucional
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone, date
from bson import ObjectId
from app.database import get_db
from app.models.planificacion import (
    PlanificacionCreate, PlanificacionUpdate, PlanificacionResponse, 
    PlanificacionStats, DIAS_CONMEMORATIVOS, IndicadorCumplimiento,
    ParticipanteActividad, EvidenciaActividad
)
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/planificacion", tags=["Planificación Anual"])


@router.get("", response_model=List[PlanificacionResponse])
async def list_planificacion(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tipo: Optional[str] = None,
    categoria: Optional[str] = None,
    estado: Optional[str] = None,
    responsable_id: Optional[str] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar actividades de planificación anual
    """
    db = get_db()
    
    query = {}
    if tipo:
        query["tipo"] = tipo
    if categoria:
        query["categoria"] = categoria
    if estado:
        query["estado"] = estado
    if responsable_id:
        query["responsable_id"] = responsable_id
    if anio:
        query["anio"] = anio
    if mes:
        query["$expr"] = {"$eq": [{"$month": "$fecha_inicio"}, mes]}
    if fecha_desde or fecha_hasta:
        query["fecha_inicio"] = {}
        if fecha_desde:
            query["fecha_inicio"]["$gte"] = fecha_desde.isoformat()
        if fecha_hasta:
            query["fecha_inicio"]["$lte"] = fecha_hasta.isoformat()
    if search:
        query["$or"] = [
            {"nombre": {"$regex": search, "$options": "i"}},
            {"descripcion": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = db.planificacion.find(query).skip(skip).limit(limit).sort("fecha_inicio", 1)
    actividades = await cursor.to_list(length=limit)
    
    return [
        PlanificacionResponse(
            id=str(p["_id"]),
            nombre=p["nombre"],
            descripcion=p.get("descripcion"),
            tipo=p["tipo"],
            categoria=p.get("categoria"),
            fecha_inicio=p["fecha_inicio"],
            fecha_termino=p.get("fecha_termino"),
            hora_inicio=p.get("hora_inicio"),
            hora_termino=p.get("hora_termino"),
            ubicacion=p.get("ubicacion"),
            responsable_id=p["responsable_id"],
            objetivo_general=p.get("objetivo_general"),
            objetivos_especificos=p.get("objetivos_especificos", []),
            dirigido_a=p.get("dirigido_a", "nna"),
            participantes=p.get("participantes", []),
            capacidad_maxima=p.get("capacidad_maxima", 50),
            indicadores=p.get("indicadores", []),
            presupuesto_estimado=p.get("presupuesto_estimado"),
            presupuesto_ejecutado=p.get("presupuesto_ejecutado"),
            recursos_necesarios=p.get("recursos_necesarios", []),
            estado=p["estado"],
            evidencias=p.get("evidencias", []),
            evaluacion_general=p.get("evaluacion_general"),
            lecciones_aprendidas=p.get("lecciones_aprendidas"),
            recomendaciones=p.get("recomendaciones"),
            anio=p.get("anio", datetime.now().year),
            creado_en=p.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=p.get("actualizado_en"),
            creado_por=p["creado_por"]
        )
        for p in actividades
    ]


@router.get("/stats", response_model=PlanificacionStats)
async def get_planificacion_stats(
    anio: Optional[int] = Query(None),
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Estadísticas de planificación anual
    """
    db = get_db()
    
    query = {}
    if anio:
        query["anio"] = anio
    else:
        query["anio"] = datetime.now().year
    
    total = await db.planificacion.count_documents(query)
    
    # Por estado
    pipeline_estado = [
        {"$match": query},
        {"$group": {"_id": "$estado", "count": {"$sum": 1}}}
    ]
    estado_cursor = db.planificacion.aggregate(pipeline_estado)
    por_estado = {e["_id"]: e["count"] async for e in estado_cursor}
    
    # Por tipo
    pipeline_tipo = [
        {"$match": query},
        {"$group": {"_id": "$tipo", "count": {"$sum": 1}}}
    ]
    tipo_cursor = db.planificacion.aggregate(pipeline_tipo)
    por_tipo = {t["_id"]: t["count"] async for t in tipo_cursor}
    
    # Por categoría
    pipeline_categoria = [
        {"$match": query},
        {"$group": {"_id": "$categoria", "count": {"$sum": 1}}}
    ]
    categoria_cursor = db.planificacion.aggregate(pipeline_categoria)
    por_categoria = {c["_id"]: c["count"] async for c in categoria_cursor if c["_id"]}
    
    # Por mes
    pipeline_mes = [
        {"$match": query},
        {"$group": {"_id": {"$month": "$fecha_inicio"}, "count": {"$sum": 1}}}
    ]
    mes_cursor = db.planificacion.aggregate(pipeline_mes)
    por_mes = {m["_id"]: m["count"] async for m in mes_cursor}
    
    # Presupuesto
    pipeline_presupuesto = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_estimado": {"$sum": "$presupuesto_estimado"},
            "total_ejecutado": {"$sum": "$presupuesto_ejecutado"}
        }}
    ]
    presupuesto_result = await db.planificacion.aggregate(pipeline_presupuesto).to_list(1)
    presupuesto = presupuesto_result[0] if presupuesto_result else {"total_estimado": 0, "total_ejecutado": 0}
    
    # Actividades próximas (próximos 30 días)
    fecha_limite = date.today() + __import__('datetime').timedelta(days=30)
    actividades_proximas = await db.planificacion.count_documents({
        **query,
        "fecha_inicio": {"$gte": date.today().isoformat(), "$lte": fecha_limite.isoformat()},
        "estado": {"$in": ["planificada", "en_preparacion"]}
    })
    
    # Actividades vencidas
    actividades_vencidas = await db.planificacion.count_documents({
        **query,
        "fecha_inicio": {"$lt": date.today().isoformat()},
        "estado": {"$in": ["planificada", "en_preparacion"]}
    })
    
    # Calcular porcentaje de cumplimiento
    actividades_realizadas = por_estado.get("realizada", 0)
    porcentaje_cumplimiento = (actividades_realizadas / total * 100) if total > 0 else 0
    
    return PlanificacionStats(
        total_actividades=total,
        por_estado=por_estado,
        por_tipo=por_tipo,
        por_categoria=por_categoria,
        por_mes=por_mes,
        porcentaje_cumplimiento_general=round(porcentaje_cumplimiento, 2),
        presupuesto_total_estimado=presupuesto.get("total_estimado", 0) or 0,
        presupuesto_total_ejecutado=presupuesto.get("total_ejecutado", 0) or 0,
        actividades_proximas=actividades_proximas,
        actividades_vencidas=actividades_vencidas
    )


@router.get("/proximas", response_model=List[PlanificacionResponse])
async def get_actividades_proximas(
    dias: int = Query(30, ge=1, le=365),
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener actividades próximas
    """
    db = get_db()
    
    fecha_limite = date.today() + __import__('datetime').timedelta(days=dias)
    
    query = {
        "fecha_inicio": {"$gte": date.today().isoformat(), "$lte": fecha_limite.isoformat()},
        "estado": {"$in": ["planificada", "en_preparacion", "en_ejecucion"]}
    }
    
    cursor = db.planificacion.find(query).sort("fecha_inicio", 1).limit(20)
    actividades = await cursor.to_list(length=20)
    
    return [
        PlanificacionResponse(
            id=str(p["_id"]),
            nombre=p["nombre"],
            descripcion=p.get("descripcion"),
            tipo=p["tipo"],
            categoria=p.get("categoria"),
            fecha_inicio=p["fecha_inicio"],
            fecha_termino=p.get("fecha_termino"),
            hora_inicio=p.get("hora_inicio"),
            hora_termino=p.get("hora_termino"),
            ubicacion=p.get("ubicacion"),
            responsable_id=p["responsable_id"],
            objetivo_general=p.get("objetivo_general"),
            objetivos_especificos=p.get("objetivos_especificos", []),
            dirigido_a=p.get("dirigido_a", "nna"),
            participantes=p.get("participantes", []),
            capacidad_maxima=p.get("capacidad_maxima", 50),
            indicadores=p.get("indicadores", []),
            presupuesto_estimado=p.get("presupuesto_estimado"),
            presupuesto_ejecutado=p.get("presupuesto_ejecutado"),
            recursos_necesarios=p.get("recursos_necesarios", []),
            estado=p["estado"],
            evidencias=p.get("evidencias", []),
            evaluacion_general=p.get("evaluacion_general"),
            lecciones_aprendidas=p.get("lecciones_aprendidas"),
            recomendaciones=p.get("recomendaciones"),
            anio=p.get("anio", datetime.now().year),
            creado_en=p.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=p.get("actualizado_en"),
            creado_por=p["creado_por"]
        )
        for p in actividades
    ]


@router.get("/dias-conmemorativos")
async def get_dias_conmemorativos(
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener lista de días conmemorativos predefinidos
    """
    return DIAS_CONMEMORATIVOS


@router.get("/{planificacion_id}", response_model=PlanificacionResponse)
async def get_planificacion(
    planificacion_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener actividad de planificación por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(planificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    actividad = await db.planificacion.find_one({"_id": ObjectId(planificacion_id)})
    
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )
    
    return PlanificacionResponse(
        id=str(actividad["_id"]),
        nombre=actividad["nombre"],
        descripcion=actividad.get("descripcion"),
        tipo=actividad["tipo"],
        categoria=actividad.get("categoria"),
        fecha_inicio=actividad["fecha_inicio"],
        fecha_termino=actividad.get("fecha_termino"),
        hora_inicio=actividad.get("hora_inicio"),
        hora_termino=actividad.get("hora_termino"),
        ubicacion=actividad.get("ubicacion"),
        responsable_id=actividad["responsable_id"],
        objetivo_general=actividad.get("objetivo_general"),
        objetivos_especificos=actividad.get("objetivos_especificos", []),
        dirigido_a=actividad.get("dirigido_a", "nna"),
        participantes=actividad.get("participantes", []),
        capacidad_maxima=actividad.get("capacidad_maxima", 50),
        indicadores=actividad.get("indicadores", []),
        presupuesto_estimado=actividad.get("presupuesto_estimado"),
        presupuesto_ejecutado=actividad.get("presupuesto_ejecutado"),
        recursos_necesarios=actividad.get("recursos_necesarios", []),
        estado=actividad["estado"],
        evidencias=actividad.get("evidencias", []),
        evaluacion_general=actividad.get("evaluacion_general"),
        lecciones_aprendidas=actividad.get("lecciones_aprendidas"),
        recomendaciones=actividad.get("recomendaciones"),
        anio=actividad.get("anio", datetime.now().year),
        creado_en=actividad.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=actividad.get("actualizado_en"),
        creado_por=actividad["creado_por"]
    )


@router.post("", response_model=PlanificacionResponse, status_code=status.HTTP_201_CREATED)
async def create_planificacion(
    data: PlanificacionCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nueva actividad de planificación
    """
    db = get_db()
    
    # Verificar que el responsable existe
    responsable = await db.usuarios.find_one({"_id": ObjectId(data.responsable_id)})
    if not responsable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsable no encontrado"
        )
    
    new_actividad = {
        "nombre": data.nombre,
        "descripcion": data.descripcion,
        "tipo": data.tipo,
        "categoria": data.categoria,
        "fecha_inicio": data.fecha_inicio.isoformat(),
        "fecha_termino": data.fecha_termino.isoformat() if data.fecha_termino else None,
        "hora_inicio": data.hora_inicio,
        "hora_termino": data.hora_termino,
        "ubicacion": data.ubicacion,
        "responsable_id": data.responsable_id,
        "objetivo_general": data.objetivo_general,
        "objetivos_especificos": data.objetivos_especificos,
        "dirigido_a": data.dirigido_a,
        "participantes": [p.dict() for p in data.participantes],
        "capacidad_maxima": data.capacidad_maxima,
        "indicadores": [i.dict() for i in data.indicadores],
        "presupuesto_estimado": data.presupuesto_estimado,
        "presupuesto_ejecutado": data.presupuesto_ejecutado,
        "recursos_necesarios": data.recursos_necesarios,
        "estado": data.estado,
        "evidencias": [e.dict() for e in data.evidencias],
        "evaluacion_general": data.evaluacion_general,
        "lecciones_aprendidas": data.lecciones_aprendidas,
        "recomendaciones": data.recomendaciones,
        "anio": data.anio,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.planificacion.insert_one(new_actividad)
    
    logger.info(f"Actividad de planificación creada: {data.nombre} por {current_user.email}")
    
    return PlanificacionResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_actividad.items() if k not in ["creado_por"]}
    )


@router.put("/{planificacion_id}", response_model=PlanificacionResponse)
async def update_planificacion(
    planificacion_id: str,
    data: PlanificacionUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar actividad de planificación
    """
    db = get_db()
    
    if not ObjectId.is_valid(planificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    existing = await db.planificacion.find_one({"_id": ObjectId(planificacion_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )
    
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            if field in ["participantes", "indicadores", "evidencias"] and value:
                update_data[field] = [v.dict() for v in value]
            elif field in ["fecha_inicio", "fecha_termino"] and value:
                update_data[field] = value.isoformat()
            else:
                update_data[field] = value
    
    await db.planificacion.update_one(
        {"_id": ObjectId(planificacion_id)},
        {"$set": update_data}
    )
    
    updated = await db.planificacion.find_one({"_id": ObjectId(planificacion_id)})
    
    logger.info(f"Planificación {planificacion_id} actualizada por {current_user.email}")
    
    return PlanificacionResponse(
        id=str(updated["_id"]),
        nombre=updated["nombre"],
        descripcion=updated.get("descripcion"),
        tipo=updated["tipo"],
        categoria=updated.get("categoria"),
        fecha_inicio=updated["fecha_inicio"],
        fecha_termino=updated.get("fecha_termino"),
        hora_inicio=updated.get("hora_inicio"),
        hora_termino=updated.get("hora_termino"),
        ubicacion=updated.get("ubicacion"),
        responsable_id=updated["responsable_id"],
        objetivo_general=updated.get("objetivo_general"),
        objetivos_especificos=updated.get("objetivos_especificos", []),
        dirigido_a=updated.get("dirigido_a", "nna"),
        participantes=updated.get("participantes", []),
        capacidad_maxima=updated.get("capacidad_maxima", 50),
        indicadores=updated.get("indicadores", []),
        presupuesto_estimado=updated.get("presupuesto_estimado"),
        presupuesto_ejecutado=updated.get("presupuesto_ejecutado"),
        recursos_necesarios=updated.get("recursos_necesarios", []),
        estado=updated["estado"],
        evidencias=updated.get("evidencias", []),
        evaluacion_general=updated.get("evaluacion_general"),
        lecciones_aprendidas=updated.get("lecciones_aprendidas"),
        recomendaciones=updated.get("recomendaciones"),
        anio=updated.get("anio", datetime.now().year),
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        creado_por=updated["creado_por"]
    )


@router.post("/{planificacion_id}/cambiar-estado")
async def cambiar_estado_planificacion(
    planificacion_id: str,
    nuevo_estado: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Cambiar estado de una actividad de planificación
    """
    db = get_db()
    
    if not ObjectId.is_valid(planificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    estados_validos = ["planificada", "en_preparacion", "en_ejecucion", "realizada", "cancelada", "postergada"]
    if nuevo_estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Estados válidos: {', '.join(estados_validos)}"
        )
    
    await db.planificacion.update_one(
        {"_id": ObjectId(planificacion_id)},
        {
            "$set": {
                "estado": nuevo_estado,
                "actualizado_en": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"Planificación {planificacion_id} cambiada a estado: {nuevo_estado} por {current_user.email}")
    
    return {"message": f"Estado actualizado a: {nuevo_estado}"}


@router.post("/{planificacion_id}/agregar-participante")
async def agregar_participante(
    planificacion_id: str,
    participante: ParticipanteActividad,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Agregar participante a una actividad
    """
    db = get_db()
    
    if not ObjectId.is_valid(planificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    actividad = await db.planificacion.find_one({"_id": ObjectId(planificacion_id)})
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )
    
    await db.planificacion.update_one(
        {"_id": ObjectId(planificacion_id)},
        {
            "$push": {"participantes": participante.dict()},
            "$set": {"actualizado_en": datetime.now(timezone.utc)}
        }
    )
    
    return {"message": "Participante agregado correctamente"}


@router.post("/{planificacion_id}/registrar-evidencia")
async def registrar_evidencia(
    planificacion_id: str,
    evidencia: EvidenciaActividad,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Registrar evidencia de una actividad
    """
    db = get_db()
    
    if not ObjectId.is_valid(planificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    actividad = await db.planificacion.find_one({"_id": ObjectId(planificacion_id)})
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )
    
    evidencia_data = evidencia.dict()
    evidencia_data["subido_por"] = current_user.user_id
    
    await db.planificacion.update_one(
        {"_id": ObjectId(planificacion_id)},
        {
            "$push": {"evidencias": evidencia_data},
            "$set": {"actualizado_en": datetime.now(timezone.utc)}
        }
    )
    
    return {"message": "Evidencia registrada correctamente"}


@router.delete("/{planificacion_id}")
async def delete_planificacion(
    planificacion_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Eliminar actividad de planificación (solo coordinador o admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(planificacion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    existing = await db.planificacion.find_one({"_id": ObjectId(planificacion_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )
    
    await db.planificacion.delete_one({"_id": ObjectId(planificacion_id)})
    
    logger.info(f"Planificación {planificacion_id} eliminada por {current_user.email}")
    
    return {"message": "Actividad eliminada correctamente"}
