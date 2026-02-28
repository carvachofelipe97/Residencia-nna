"""
Router de Módulo Jurídico
Medidas judiciales, audiencias, restricciones, alertas de vencimiento
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timezone, date, timedelta
from bson import ObjectId
from app.database import get_db
from app.models.juridico import (
    MedidaJudicialCreate, MedidaJudicialUpdate, MedidaJudicialResponse,
    RestriccionCreate, RestriccionUpdate, RestriccionResponse,
    JuridicoStats, AlertaVencimiento, Audiencia
)
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/juridico", tags=["Módulo Jurídico"])


@router.get("/medidas", response_model=List[MedidaJudicialResponse])
async def list_medidas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    nna_id: Optional[str] = None,
    estado: Optional[str] = None,
    tipo_solicitud: Optional[str] = None,
    tipo_medida: Optional[str] = None,
    proximas_vencer: bool = Query(False, description="Solo medidas próximas a vencer"),
    vencidas: bool = Query(False, description="Solo medidas vencidas"),
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar medidas judiciales
    """
    db = get_db()
    
    query = {}
    if nna_id:
        query["nna_id"] = nna_id
    if estado:
        query["estado"] = estado
    if tipo_solicitud:
        query["tipo_solicitud"] = tipo_solicitud
    if tipo_medida:
        query["tipo_medida"] = tipo_medida
    
    if proximas_vencer:
        fecha_limite = date.today() + timedelta(days=30)
        query["$and"] = [
            {"fecha_termino": {"$gte": date.today().isoformat(), "$lte": fecha_limite.isoformat()}},
            {"estado": {"$in": ["vigente", "dictada"]}}
        ]
    
    if vencidas:
        query["$and"] = [
            {"fecha_termino": {"$lt": date.today().isoformat()}},
            {"estado": {"$in": ["vigente", "dictada"]}}
        ]
    
    cursor = db.medidas_judiciales.find(query).skip(skip).limit(limit).sort("fecha_solicitud", -1)
    medidas = await cursor.to_list(length=limit)
    
    return [
        MedidaJudicialResponse(
            id=str(m["_id"]),
            nna_id=m["nna_id"],
            numero_ingreso=m.get("numero_ingreso"),
            fecha_solicitud=m["fecha_solicitud"],
            tipo_solicitud=m["tipo_solicitud"],
            solicitante=m.get("solicitante"),
            rol_solicitante=m.get("rol_solicitante"),
            audiencias=m.get("audiencias", []),
            fecha_resolucion=m.get("fecha_resolucion"),
            numero_resolucion=m.get("numero_resolucion"),
            tipo_medida=m.get("tipo_medida"),
            fecha_inicio=m.get("fecha_inicio"),
            fecha_termino=m.get("fecha_termino"),
            plazo_meses=m.get("plazo_meses"),
            estado=m["estado"],
            restriccion_contacto=m.get("restriccion_contacto", False),
            restriccion_acercamiento=m.get("restriccion_acercamiento", False),
            restriccion_salida_territorio=m.get("restriccion_salida_territorio", False),
            otras_restricciones=m.get("otras_restricciones"),
            medidas_complementarias=m.get("medidas_complementarias", []),
            observaciones=m.get("observaciones"),
            requiere_seguimiento=m.get("requiere_seguimiento", False),
            frecuencia_seguimiento=m.get("frecuencia_seguimiento"),
            alerta_dias_anticipacion=m.get("alerta_dias_anticipacion", 30),
            creado_en=m.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=m.get("actualizado_en"),
            creado_por=m["creado_por"]
        )
        for m in medidas
    ]


@router.get("/medidas/stats", response_model=JuridicoStats)
async def get_medidas_stats(
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Estadísticas de medidas judiciales
    """
    db = get_db()
    
    total = await db.medidas_judiciales.count_documents({})
    
    # Por estado
    pipeline_estado = [
        {"$group": {"_id": "$estado", "count": {"$sum": 1}}}
    ]
    estado_cursor = db.medidas_judiciales.aggregate(pipeline_estado)
    por_estado = {e["_id"]: e["count"] async for e in estado_cursor}
    
    # Por tipo de solicitud
    pipeline_tipo_sol = [
        {"$group": {"_id": "$tipo_solicitud", "count": {"$sum": 1}}}
    ]
    tipo_sol_cursor = db.medidas_judiciales.aggregate(pipeline_tipo_sol)
    por_tipo_solicitud = {t["_id"]: t["count"] async for t in tipo_sol_cursor if t["_id"]}
    
    # Por tipo de medida
    pipeline_tipo_med = [
        {"$group": {"_id": "$tipo_medida", "count": {"$sum": 1}}}
    ]
    tipo_med_cursor = db.medidas_judiciales.aggregate(pipeline_tipo_med)
    por_tipo_medida = {t["_id"]: t["count"] async for t in tipo_med_cursor if t["_id"]}
    
    # Vigentes
    vigentes = await db.medidas_judiciales.count_documents({"estado": "vigente"})
    
    # Con restricciones
    con_restricciones = await db.medidas_judiciales.count_documents({
        "$or": [
            {"restriccion_contacto": True},
            {"restriccion_acercamiento": True},
            {"restriccion_salida_territorio": True}
        ]
    })
    
    # Próximas a vencer (30 días)
    fecha_limite = date.today() + timedelta(days=30)
    proximas_a_vencer = await db.medidas_judiciales.count_documents({
        "fecha_termino": {"$gte": date.today().isoformat(), "$lte": fecha_limite.isoformat()},
        "estado": {"$in": ["vigente", "dictada"]}
    })
    
    # Vencidas
    vencidas = await db.medidas_judiciales.count_documents({
        "fecha_termino": {"$lt": date.today().isoformat()},
        "estado": {"$in": ["vigente", "dictada"]}
    })
    
    # Restricciones
    total_restricciones = await db.restricciones.count_documents({})
    restricciones_activas = await db.restricciones.count_documents({"estado": "activa"})
    
    return JuridicoStats(
        total_medidas=total,
        por_estado=por_estado,
        por_tipo_solicitud=por_tipo_solicitud,
        por_tipo_medida=por_tipo_medida,
        vigentes=vigentes,
        con_restricciones=con_restricciones,
        proximas_a_vencer=proximas_a_vencer,
        vencidas=vencidas,
        total_restricciones=total_restricciones,
        restricciones_activas=restricciones_activas
    )


@router.get("/medidas/{medida_id}", response_model=MedidaJudicialResponse)
async def get_medida(
    medida_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener medida judicial por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(medida_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    medida = await db.medidas_judiciales.find_one({"_id": ObjectId(medida_id)})
    
    if not medida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medida no encontrada"
        )
    
    return MedidaJudicialResponse(
        id=str(medida["_id"]),
        nna_id=medida["nna_id"],
        numero_ingreso=medida.get("numero_ingreso"),
        fecha_solicitud=medida["fecha_solicitud"],
        tipo_solicitud=medida["tipo_solicitud"],
        solicitante=medida.get("solicitante"),
        rol_solicitante=medida.get("rol_solicitante"),
        audiencias=medida.get("audiencias", []),
        fecha_resolucion=medida.get("fecha_resolucion"),
        numero_resolucion=medida.get("numero_resolucion"),
        tipo_medida=medida.get("tipo_medida"),
        fecha_inicio=medida.get("fecha_inicio"),
        fecha_termino=medida.get("fecha_termino"),
        plazo_meses=medida.get("plazo_meses"),
        estado=medida["estado"],
        restriccion_contacto=medida.get("restriccion_contacto", False),
        restriccion_acercamiento=medida.get("restriccion_acercamiento", False),
        restriccion_salida_territorio=medida.get("restriccion_salida_territorio", False),
        otras_restricciones=medida.get("otras_restricciones"),
        medidas_complementarias=medida.get("medidas_complementarias", []),
        observaciones=medida.get("observaciones"),
        requiere_seguimiento=medida.get("requiere_seguimiento", False),
        frecuencia_seguimiento=medida.get("frecuencia_seguimiento"),
        alerta_dias_anticipacion=medida.get("alerta_dias_anticipacion", 30),
        creado_en=medida.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=medida.get("actualizado_en"),
        creado_por=medida["creado_por"]
    )


@router.post("/medidas", response_model=MedidaJudicialResponse, status_code=status.HTTP_201_CREATED)
async def create_medida(
    data: MedidaJudicialCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nueva medida judicial
    """
    db = get_db()
    
    # Validar NNA
    if not ObjectId.is_valid(data.nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    nna = await db.nna.find_one({"_id": ObjectId(data.nna_id)})
    if not nna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    new_medida = {
        "nna_id": data.nna_id,
        "numero_ingreso": data.numero_ingreso,
        "fecha_solicitud": data.fecha_solicitud.isoformat(),
        "tipo_solicitud": data.tipo_solicitud,
        "solicitante": data.solicitante,
        "rol_solicitante": data.rol_solicitante,
        "audiencias": [a.dict() for a in data.audiencias],
        "fecha_resolucion": data.fecha_resolucion.isoformat() if data.fecha_resolucion else None,
        "numero_resolucion": data.numero_resolucion,
        "tipo_medida": data.tipo_medida,
        "fecha_inicio": data.fecha_inicio.isoformat() if data.fecha_inicio else None,
        "fecha_termino": data.fecha_termino.isoformat() if data.fecha_termino else None,
        "plazo_meses": data.plazo_meses,
        "estado": data.estado,
        "restriccion_contacto": data.restriccion_contacto,
        "restriccion_acercamiento": data.restriccion_acercamiento,
        "restriccion_salida_territorio": data.restriccion_salida_territorio,
        "otras_restricciones": data.otras_restricciones,
        "medidas_complementarias": data.medidas_complementarias,
        "observaciones": data.observaciones,
        "requiere_seguimiento": data.requiere_seguimiento,
        "frecuencia_seguimiento": data.frecuencia_seguimiento,
        "alerta_dias_anticipacion": data.alerta_dias_anticipacion,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.medidas_judiciales.insert_one(new_medida)
    
    logger.info(f"Medida judicial creada para NNA {data.nna_id} por {current_user.email}")
    
    return MedidaJudicialResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_medida.items() if k not in ["creado_por"]}
    )


@router.put("/medidas/{medida_id}", response_model=MedidaJudicialResponse)
async def update_medida(
    medida_id: str,
    data: MedidaJudicialUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar medida judicial
    """
    db = get_db()
    
    if not ObjectId.is_valid(medida_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    existing = await db.medidas_judiciales.find_one({"_id": ObjectId(medida_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medida no encontrada"
        )
    
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            if field == "audiencias" and value:
                update_data[field] = [a.dict() for a in value]
            elif field in ["fecha_solicitud", "fecha_resolucion", "fecha_inicio", "fecha_termino"] and value:
                update_data[field] = value.isoformat()
            else:
                update_data[field] = value
    
    await db.medidas_judiciales.update_one(
        {"_id": ObjectId(medida_id)},
        {"$set": update_data}
    )
    
    updated = await db.medidas_judiciales.find_one({"_id": ObjectId(medida_id)})
    
    logger.info(f"Medida {medida_id} actualizada por {current_user.email}")
    
    return MedidaJudicialResponse(
        id=str(updated["_id"]),
        nna_id=updated["nna_id"],
        numero_ingreso=updated.get("numero_ingreso"),
        fecha_solicitud=updated["fecha_solicitud"],
        tipo_solicitud=updated["tipo_solicitud"],
        solicitante=updated.get("solicitante"),
        rol_solicitante=updated.get("rol_solicitante"),
        audiencias=updated.get("audiencias", []),
        fecha_resolucion=updated.get("fecha_resolucion"),
        numero_resolucion=updated.get("numero_resolucion"),
        tipo_medida=updated.get("tipo_medida"),
        fecha_inicio=updated.get("fecha_inicio"),
        fecha_termino=updated.get("fecha_termino"),
        plazo_meses=updated.get("plazo_meses"),
        estado=updated["estado"],
        restriccion_contacto=updated.get("restriccion_contacto", False),
        restriccion_acercamiento=updated.get("restriccion_acercamiento", False),
        restriccion_salida_territorio=updated.get("restriccion_salida_territorio", False),
        otras_restricciones=updated.get("otras_restricciones"),
        medidas_complementarias=updated.get("medidas_complementarias", []),
        observaciones=updated.get("observaciones"),
        requiere_seguimiento=updated.get("requiere_seguimiento", False),
        frecuencia_seguimiento=updated.get("frecuencia_seguimiento"),
        alerta_dias_anticipacion=updated.get("alerta_dias_anticipacion", 30),
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        creado_por=updated["creado_por"]
    )


@router.post("/medidas/{medida_id}/agregar-audiencia")
async def agregar_audiencia(
    medida_id: str,
    audiencia: Audiencia,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Agregar audiencia a una medida judicial
    """
    db = get_db()
    
    if not ObjectId.is_valid(medida_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    medida = await db.medidas_judiciales.find_one({"_id": ObjectId(medida_id)})
    if not medida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medida no encontrada"
        )
    
    await db.medidas_judiciales.update_one(
        {"_id": ObjectId(medida_id)},
        {
            "$push": {"audiencias": audiencia.dict()},
            "$set": {"actualizado_en": datetime.now(timezone.utc)}
        }
    )
    
    return {"message": "Audiencia agregada correctamente"}


@router.get("/restricciones", response_model=List[RestriccionResponse])
async def list_restricciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    nna_id: Optional[str] = None,
    estado: Optional[str] = None,
    tipo: Optional[str] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar restricciones
    """
    db = get_db()
    
    query = {}
    if nna_id:
        query["nna_id"] = nna_id
    if estado:
        query["estado"] = estado
    if tipo:
        query["tipo"] = tipo
    
    cursor = db.restricciones.find(query).skip(skip).limit(limit).sort("fecha_inicio", -1)
    restricciones = await cursor.to_list(length=limit)
    
    return [
        RestriccionResponse(
            id=str(r["_id"]),
            nna_id=r["nna_id"],
            medida_id=r.get("medida_id"),
            tipo=r["tipo"],
            descripcion=r["descripcion"],
            persona_restringida_nombre=r.get("persona_restringida_nombre"),
            persona_restringida_rut=r.get("persona_restringida_rut"),
            relacion_con_nna=r.get("relacion_con_nna"),
            fecha_inicio=r["fecha_inicio"],
            fecha_termino=r.get("fecha_termino"),
            indefinida=r.get("indefinida", False),
            estado=r["estado"],
            motivo=r.get("motivo"),
            observaciones=r.get("observaciones"),
            creado_en=r.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=r.get("actualizado_en"),
            creado_por=r["creado_por"]
        )
        for r in restricciones
    ]


@router.post("/restricciones", response_model=RestriccionResponse, status_code=status.HTTP_201_CREATED)
async def create_restriccion(
    data: RestriccionCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nueva restricción
    """
    db = get_db()
    
    # Validar NNA
    if not ObjectId.is_valid(data.nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    nna = await db.nna.find_one({"_id": ObjectId(data.nna_id)})
    if not nna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    new_restriccion = {
        "nna_id": data.nna_id,
        "medida_id": data.medida_id,
        "tipo": data.tipo,
        "descripcion": data.descripcion,
        "persona_restringida_nombre": data.persona_restringida_nombre,
        "persona_restringida_rut": data.persona_restringida_rut,
        "relacion_con_nna": data.relacion_con_nna,
        "fecha_inicio": data.fecha_inicio.isoformat(),
        "fecha_termino": data.fecha_termino.isoformat() if data.fecha_termino else None,
        "indefinida": data.indefinida,
        "estado": data.estado,
        "motivo": data.motivo,
        "observaciones": data.observaciones,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.restricciones.insert_one(new_restriccion)
    
    logger.info(f"Restricción creada para NNA {data.nna_id} por {current_user.email}")
    
    return RestriccionResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_restriccion.items() if k not in ["creado_por"]}
    )


@router.get("/alertas-vencimiento", response_model=List[AlertaVencimiento])
async def get_alertas_vencimiento(
    dias_anticipacion: int = Query(30, ge=1, le=365),
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener alertas de medidas próximas a vencer
    """
    db = get_db()
    
    fecha_limite = date.today() + timedelta(days=dias_anticipacion)
    
    pipeline = [
        {
            "$match": {
                "fecha_termino": {"$gte": date.today().isoformat(), "$lte": fecha_limite.isoformat()},
                "estado": {"$in": ["vigente", "dictada"]}
            }
        },
        {
            "$lookup": {
                "from": "nna",
                "localField": "nna_id",
                "foreignField": "_id",
                "as": "nna"
            }
        },
        {"$unwind": "$nna"}
    ]
    
    cursor = db.medidas_judiciales.aggregate(pipeline)
    medidas = await cursor.to_list(length=100)
    
    alertas = []
    for m in medidas:
        fecha_termino = datetime.strptime(m["fecha_termino"], "%Y-%m-%d").date()
        dias_restantes = (fecha_termino - date.today()).days
        
        # Determinar prioridad
        if dias_restantes <= 7:
            prioridad = "alta"
        elif dias_restantes <= 15:
            prioridad = "media"
        else:
            prioridad = "baja"
        
        alertas.append(AlertaVencimiento(
            medida_id=str(m["_id"]),
            nna_id=m["nna_id"],
            nna_nombre=f"{m['nna']['nombre']} {m['nna']['apellido']}",
            tipo_medida=m.get("tipo_medida", "No especificada"),
            fecha_vencimiento=fecha_termino,
            dias_restantes=dias_restantes,
            prioridad=prioridad
        ))
    
    # Ordenar por días restantes
    alertas.sort(key=lambda x: x.dias_restantes)
    
    return alertas


@router.post("/generar-alertas-vencimiento")
async def generar_alertas_vencimiento(
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Generar alertas automáticas para medidas próximas a vencer
    """
    db = get_db()
    alertas_creadas = 0
    
    fecha_limite = date.today() + timedelta(days=30)
    
    # Buscar medidas próximas a vencer
    medidas = await db.medidas_judiciales.find({
        "fecha_termino": {"$gte": date.today().isoformat(), "$lte": fecha_limite.isoformat()},
        "estado": {"$in": ["vigente", "dictada"]}
    }).to_list(100)
    
    for medida in medidas:
        # Verificar si ya existe alerta
        existing = await db.alertas.find_one({
            "entidad_tipo": "medida_judicial",
            "entidad_id": str(medida["_id"]),
            "tipo": "vencimiento_plazo",
            "estado": {"$in": ["activa", "en_proceso"]}
        })
        
        if not existing:
            nna = await db.nna.find_one({"_id": ObjectId(medida["nna_id"])})
            nna_nombre = f"{nna['nombre']} {nna['apellido']}" if nna else "NNA"
            
            fecha_termino = datetime.strptime(medida["fecha_termino"], "%Y-%m-%d").date()
            dias_restantes = (fecha_termino - date.today()).days
            
            prioridad = "critica" if dias_restantes <= 7 else "alta" if dias_restantes <= 15 else "media"
            
            await db.alertas.insert_one({
                "nna_id": medida["nna_id"],
                "titulo": f"Medida próxima a vencer: {nna_nombre}",
                "mensaje": f"La medida judicial vence el {medida['fecha_termino']}. Quedan {dias_restantes} días.",
                "tipo": "vencimiento_plazo",
                "prioridad": prioridad,
                "fecha_vencimiento": medida["fecha_termino"],
                "estado": "activa",
                "entidad_tipo": "medida_judicial",
                "entidad_id": str(medida["_id"]),
                "creado_en": datetime.now(timezone.utc),
                "creado_por": current_user.user_id
            })
            alertas_creadas += 1
    
    logger.info(f"{alertas_creadas} alertas de vencimiento generadas por {current_user.email}")
    
    return {
        "message": f"Se generaron {alertas_creadas} alertas de vencimiento",
        "alertas_creadas": alertas_creadas
    }
