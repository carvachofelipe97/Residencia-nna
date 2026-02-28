"""
Router de Alertas - Sistema de notificaciones y vencimientos
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timezone, date, timedelta
from bson import ObjectId
from app.database import get_db
from app.models.alerta import AlertaCreate, AlertaUpdate, AlertaResponse, AlertaStats
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("", response_model=List[AlertaResponse])
async def list_alertas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    nna_id: Optional[str] = None,
    tipo: Optional[str] = None,
    prioridad: Optional[str] = None,
    estado: Optional[str] = None,
    asignado_a: Optional[str] = None,
    solo_activas: bool = Query(False, description="Solo alertas activas"),
    vencidas: bool = Query(False, description="Solo alertas vencidas"),
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar alertas del sistema
    """
    db = get_db()
    
    query = {}
    
    if nna_id:
        query["nna_id"] = nna_id
    if tipo:
        query["tipo"] = tipo
    if prioridad:
        query["prioridad"] = prioridad
    if estado:
        query["estado"] = estado
    if asignado_a:
        query["asignado_a"] = asignado_a
    
    if solo_activas:
        query["estado"] = {"$in": ["activa", "en_proceso"]}
    
    if vencidas:
        query["$and"] = [
            {"fecha_vencimiento": {"$lt": date.today()}},
            {"estado": {"$in": ["activa", "en_proceso"]}}
        ]
    
    # Si es técnico, solo ver alertas asignadas a él o sin asignar
    if current_user.rol == "tecnico":
        query["$or"] = [
            {"asignado_a": current_user.user_id},
            {"asignado_a": None},
            {"creado_por": current_user.user_id}
        ]
    
    cursor = db.alertas.find(query).skip(skip).limit(limit).sort([
        ("prioridad", -1),  # Críticas primero
        ("fecha_vencimiento", 1),  # Las que vencen antes
        ("creado_en", -1)
    ])
    alertas = await cursor.to_list(length=limit)
    
    return [
        AlertaResponse(
            id=str(a["_id"]),
            nna_id=a.get("nna_id"),
            usuario_id=a.get("usuario_id"),
            titulo=a["titulo"],
            mensaje=a["mensaje"],
            tipo=a["tipo"],
            prioridad=a["prioridad"],
            fecha_vencimiento=a.get("fecha_vencimiento"),
            fecha_recordatorio=a.get("fecha_recordatorio"),
            estado=a["estado"],
            entidad_tipo=a.get("entidad_tipo"),
            entidad_id=a.get("entidad_id"),
            url_redirect=a.get("url_redirect"),
            asignado_a=a.get("asignado_a"),
            creado_en=a.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=a.get("actualizado_en"),
            resuelta_en=a.get("resuelta_en"),
            resuelta_por=a.get("resuelta_por"),
            creado_por=a["creado_por"]
        )
        for a in alertas
    ]


@router.get("/stats", response_model=AlertaStats)
async def get_alertas_stats(
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Estadísticas de alertas
    """
    db = get_db()
    
    total = await db.alertas.count_documents({})
    activas = await db.alertas.count_documents({"estado": {"$in": ["activa", "en_proceso"]}})
    criticas = await db.alertas.count_documents({"prioridad": "critica", "estado": {"$in": ["activa", "en_proceso"]}})
    vencidas = await db.alertas.count_documents({
        "fecha_vencimiento": {"$lt": date.today()},
        "estado": {"$in": ["activa", "en_proceso"]}
    })
    
    # Por tipo
    pipeline_tipo = [
        {"$match": {"estado": {"$in": ["activa", "en_proceso"]}}},
        {"$group": {"_id": "$tipo", "count": {"$sum": 1}}}
    ]
    tipo_cursor = db.alertas.aggregate(pipeline_tipo)
    por_tipo = {t["_id"]: t["count"] async for t in tipo_cursor}
    
    # Por prioridad
    pipeline_prioridad = [
        {"$match": {"estado": {"$in": ["activa", "en_proceso"]}}},
        {"$group": {"_id": "$prioridad", "count": {"$sum": 1}}}
    ]
    prioridad_cursor = db.alertas.aggregate(pipeline_prioridad)
    por_prioridad = {p["_id"]: p["count"] async for p in prioridad_cursor}
    
    return AlertaStats(
        total=total,
        activas=activas,
        criticas=criticas,
        vencidas=vencidas,
        por_tipo=por_tipo,
        por_prioridad=por_prioridad
    )


@router.get("/mis-alertas", response_model=List[AlertaResponse])
async def get_mis_alertas(
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener alertas asignadas al usuario actual
    """
    db = get_db()
    
    query = {
        "$and": [
            {"estado": {"$in": ["activa", "en_proceso"]}},
            {"$or": [
                {"asignado_a": current_user.user_id},
                {"usuario_id": current_user.user_id}
            ]}
        ]
    }
    
    cursor = db.alertas.find(query).sort([
        ("prioridad", -1),
        ("fecha_vencimiento", 1)
    ]).limit(20)
    
    alertas = await cursor.to_list(length=20)
    
    return [
        AlertaResponse(
            id=str(a["_id"]),
            nna_id=a.get("nna_id"),
            usuario_id=a.get("usuario_id"),
            titulo=a["titulo"],
            mensaje=a["mensaje"],
            tipo=a["tipo"],
            prioridad=a["prioridad"],
            fecha_vencimiento=a.get("fecha_vencimiento"),
            fecha_recordatorio=a.get("fecha_recordatorio"),
            estado=a["estado"],
            entidad_tipo=a.get("entidad_tipo"),
            entidad_id=a.get("entidad_id"),
            url_redirect=a.get("url_redirect"),
            asignado_a=a.get("asignado_a"),
            creado_en=a.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=a.get("actualizado_en"),
            resuelta_en=a.get("resuelta_en"),
            resuelta_por=a.get("resuelta_por"),
            creado_por=a["creado_por"]
        )
        for a in alertas
    ]


@router.get("/{alerta_id}", response_model=AlertaResponse)
async def get_alerta(
    alerta_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener alerta por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(alerta_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de alerta inválido"
        )
    
    alerta = await db.alertas.find_one({"_id": ObjectId(alerta_id)})
    
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    return AlertaResponse(
        id=str(alerta["_id"]),
        nna_id=alerta.get("nna_id"),
        usuario_id=alerta.get("usuario_id"),
        titulo=alerta["titulo"],
        mensaje=alerta["mensaje"],
        tipo=alerta["tipo"],
        prioridad=alerta["prioridad"],
        fecha_vencimiento=alerta.get("fecha_vencimiento"),
        fecha_recordatorio=alerta.get("fecha_recordatorio"),
        estado=alerta["estado"],
        entidad_tipo=alerta.get("entidad_tipo"),
        entidad_id=alerta.get("entidad_id"),
        url_redirect=alerta.get("url_redirect"),
        asignado_a=alerta.get("asignado_a"),
        creado_en=alerta.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=alerta.get("actualizado_en"),
        resuelta_en=alerta.get("resuelta_en"),
        resuelta_por=alerta.get("resuelta_por"),
        creado_por=alerta["creado_por"]
    )


@router.post("", response_model=AlertaResponse, status_code=status.HTTP_201_CREATED)
async def create_alerta(
    data: AlertaCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nueva alerta
    """
    db = get_db()
    
    # Validar que el NNA existe si se proporciona
    if data.nna_id:
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
    
    new_alerta = {
        "nna_id": data.nna_id,
        "usuario_id": data.usuario_id,
        "titulo": data.titulo,
        "mensaje": data.mensaje,
        "tipo": data.tipo,
        "prioridad": data.prioridad,
        "fecha_vencimiento": data.fecha_vencimiento,
        "fecha_recordatorio": data.fecha_recordatorio,
        "estado": data.estado,
        "entidad_tipo": data.entidad_tipo,
        "entidad_id": data.entidad_id,
        "url_redirect": data.url_redirect,
        "asignado_a": data.asignado_a,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.alertas.insert_one(new_alerta)
    
    logger.info(f"Alerta creada: {data.titulo} por {current_user.email}")
    
    return AlertaResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_alerta.items() if k not in ["creado_por"]}
    )


@router.put("/{alerta_id}", response_model=AlertaResponse)
async def update_alerta(
    alerta_id: str,
    data: AlertaUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar alerta
    """
    db = get_db()
    
    if not ObjectId.is_valid(alerta_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de alerta inválido"
        )
    
    existing = await db.alertas.find_one({"_id": ObjectId(alerta_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    await db.alertas.update_one(
        {"_id": ObjectId(alerta_id)},
        {"$set": update_data}
    )
    
    updated = await db.alertas.find_one({"_id": ObjectId(alerta_id)})
    
    logger.info(f"Alerta {alerta_id} actualizada por {current_user.email}")
    
    return AlertaResponse(
        id=str(updated["_id"]),
        nna_id=updated.get("nna_id"),
        usuario_id=updated.get("usuario_id"),
        titulo=updated["titulo"],
        mensaje=updated["mensaje"],
        tipo=updated["tipo"],
        prioridad=updated["prioridad"],
        fecha_vencimiento=updated.get("fecha_vencimiento"),
        fecha_recordatorio=updated.get("fecha_recordatorio"),
        estado=updated["estado"],
        entidad_tipo=updated.get("entidad_tipo"),
        entidad_id=updated.get("entidad_id"),
        url_redirect=updated.get("url_redirect"),
        asignado_a=updated.get("asignado_a"),
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        resuelta_en=updated.get("resuelta_en"),
        resuelta_por=updated.get("resuelta_por"),
        creado_por=updated["creado_por"]
    )


@router.post("/{alerta_id}/resolver")
async def resolver_alerta(
    alerta_id: str,
    comentario: Optional[str] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Marcar alerta como resuelta
    """
    db = get_db()
    
    if not ObjectId.is_valid(alerta_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de alerta inválido"
        )
    
    existing = await db.alertas.find_one({"_id": ObjectId(alerta_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    await db.alertas.update_one(
        {"_id": ObjectId(alerta_id)},
        {
            "$set": {
                "estado": "resuelta",
                "resuelta_en": datetime.now(timezone.utc),
                "resuelta_por": current_user.user_id,
                "actualizado_en": datetime.now(timezone.utc),
                "comentario_resolucion": comentario
            }
        }
    )
    
    logger.info(f"Alerta {alerta_id} resuelta por {current_user.email}")
    
    return {"message": "Alerta resuelta correctamente"}


@router.post("/{alerta_id}/asignar")
async def asignar_alerta(
    alerta_id: str,
    usuario_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Asignar alerta a un usuario (solo coordinador o admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(alerta_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de alerta inválido"
        )
    
    # Verificar que el usuario existe
    usuario = await db.usuarios.find_one({"_id": ObjectId(usuario_id)})
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    await db.alertas.update_one(
        {"_id": ObjectId(alerta_id)},
        {
            "$set": {
                "asignado_a": usuario_id,
                "actualizado_en": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"Alerta {alerta_id} asignada a {usuario_id} por {current_user.email}")
    
    return {"message": f"Alerta asignada a {usuario['nombre']}"}


@router.delete("/{alerta_id}")
async def delete_alerta(
    alerta_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Eliminar alerta (solo coordinador o admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(alerta_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de alerta inválido"
        )
    
    existing = await db.alertas.find_one({"_id": ObjectId(alerta_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    await db.alertas.delete_one({"_id": ObjectId(alerta_id)})
    
    logger.info(f"Alerta {alerta_id} eliminada por {current_user.email}")
    
    return {"message": "Alerta eliminada correctamente"}


# ============================================================================
# ALERTAS AUTOMÁTICAS
# ============================================================================

@router.post("/generar/vencimientos")
async def generar_alertas_vencimientos(
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Generar alertas automáticas para vencimientos próximos
    """
    db = get_db()
    alertas_creadas = 0
    
    # Fecha límite: 7 días desde hoy
    fecha_limite = date.today() + timedelta(days=7)
    
    # 1. Buscar intervenciones con seguimiento pendiente
    intervenciones = await db.intervenciones.find({
        "fecha_proximo_seguimiento": {"$lte": fecha_limite.isoformat(), "$gte": date.today().isoformat()},
        "estado": {"$in": ["pendiente", "en_proceso"]}
    }).to_list(100)
    
    for interv in intervenciones:
        # Verificar si ya existe alerta
        existing = await db.alertas.find_one({
            "entidad_tipo": "intervencion",
            "entidad_id": str(interv["_id"]),
            "tipo": "seguimiento_pendiente",
            "estado": {"$in": ["activa", "en_proceso"]}
        })
        
        if not existing:
            nna = await db.nna.find_one({"_id": ObjectId(interv["nna_id"])})
            nna_nombre = f"{nna['nombre']} {nna['apellido']}" if nna else "NNA"
            
            await db.alertas.insert_one({
                "nna_id": interv["nna_id"],
                "titulo": f"Seguimiento pendiente: {nna_nombre}",
                "mensaje": f"La intervención del {interv['fecha']} requiere seguimiento antes del {interv.get('fecha_proximo_seguimiento', 'N/A')}",
                "tipo": "seguimiento_pendiente",
                "prioridad": "alta" if interv.get("prioridad") == "urgente" else "media",
                "fecha_vencimiento": interv.get("fecha_proximo_seguimiento"),
                "estado": "activa",
                "entidad_tipo": "intervencion",
                "entidad_id": str(interv["_id"]),
                "creado_en": datetime.now(timezone.utc),
                "creado_por": current_user.user_id
            })
            alertas_creadas += 1
    
    # 2. Buscar talleres próximos
    talleres = await db.talleres.find({
        "fecha": {"$lte": fecha_limite.isoformat(), "$gte": date.today().isoformat()},
        "estado": {"$in": ["programado"]}
    }).to_list(100)
    
    for taller in talleres:
        existing = await db.alertas.find_one({
            "entidad_tipo": "taller",
            "entidad_id": str(taller["_id"]),
            "tipo": "taller_proximo",
            "estado": {"$in": ["activa", "en_proceso"]}
        })
        
        if not existing:
            await db.alertas.insert_one({
                "titulo": f"Taller próximo: {taller['nombre']}",
                "mensaje": f"El taller '{taller['nombre']}' está programado para el {taller['fecha']} a las {taller.get('hora_inicio', 'N/A')}",
                "tipo": "taller_proximo",
                "prioridad": "media",
                "fecha_vencimiento": taller["fecha"],
                "estado": "activa",
                "entidad_tipo": "taller",
                "entidad_id": str(taller["_id"]),
                "creado_en": datetime.now(timezone.utc),
                "creado_por": current_user.user_id
            })
            alertas_creadas += 1
    
    logger.info(f"{alertas_creadas} alertas automáticas generadas por {current_user.email}")
    
    return {
        "message": f"Se generaron {alertas_creadas} alertas automáticas",
        "alertas_creadas": alertas_creadas
    }
