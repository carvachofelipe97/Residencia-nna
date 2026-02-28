"""
Router de Intervenciones
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone, date
from bson import ObjectId
from app.database import get_db
from app.models.intervencion import IntervencionCreate, IntervencionUpdate, IntervencionResponse
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intervenciones", tags=["Intervenciones"])


@router.get("", response_model=List[IntervencionResponse])
async def list_intervenciones(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    nna_id: Optional[str] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar intervenciones
    """
    db = get_db()
    
    query = {}
    if nna_id:
        query["nna_id"] = nna_id
    if tipo:
        query["tipo"] = tipo
    if estado:
        query["estado"] = estado
    if prioridad:
        query["prioridad"] = prioridad
    if fecha_desde or fecha_hasta:
        query["fecha"] = {}
        if fecha_desde:
            query["fecha"]["$gte"] = fecha_desde
        if fecha_hasta:
            query["fecha"]["$lte"] = fecha_hasta
    
    cursor = db.intervenciones.find(query).skip(skip).limit(limit).sort("fecha", -1)
    intervenciones = await cursor.to_list(length=limit)
    
    return [
        IntervencionResponse(
            id=str(i["_id"]),
            nna_id=i["nna_id"],
            fecha=i["fecha"],
            tipo=i["tipo"],
            motivo=i["motivo"],
            descripcion=i["descripcion"],
            resultados=i.get("resultados"),
            derivacion=i.get("derivacion"),
            estado=i["estado"],
            prioridad=i["prioridad"],
            fecha_proximo_seguimiento=i.get("fecha_proximo_seguimiento"),
            creado_en=i.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=i.get("actualizado_en"),
            creado_por=i["creado_por"],
            actualizado_por=i.get("actualizado_por")
        )
        for i in intervenciones
    ]


@router.get("/stats", response_model=dict)
async def get_intervenciones_stats(
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Estadísticas de intervenciones
    """
    db = get_db()
    
    total = await db.intervenciones.count_documents({})
    
    # Por estado
    pipeline_estado = [
        {"$group": {"_id": "$estado", "count": {"$sum": 1}}}
    ]
    estado_cursor = db.intervenciones.aggregate(pipeline_estado)
    por_estado = {e["_id"]: e["count"] async for e in estado_cursor}
    
    # Por tipo
    pipeline_tipo = [
        {"$group": {"_id": "$tipo", "count": {"$sum": 1}}}
    ]
    tipo_cursor = db.intervenciones.aggregate(pipeline_tipo)
    por_tipo = {t["_id"]: t["count"] async for t in tipo_cursor}
    
    # Por prioridad
    pipeline_prioridad = [
        {"$group": {"_id": "$prioridad", "count": {"$sum": 1}}}
    ]
    prioridad_cursor = db.intervenciones.aggregate(pipeline_prioridad)
    por_prioridad = {p["_id"]: p["count"] async for p in prioridad_cursor}
    
    return {
        "total": total,
        "por_estado": por_estado,
        "por_tipo": por_tipo,
        "por_prioridad": por_prioridad
    }


@router.get("/{intervencion_id}", response_model=IntervencionResponse)
async def get_intervencion(
    intervencion_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener intervención por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(intervencion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de intervención inválido"
        )
    
    intervencion = await db.intervenciones.find_one({"_id": ObjectId(intervencion_id)})
    
    if not intervencion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervención no encontrada"
        )
    
    return IntervencionResponse(
        id=str(intervencion["_id"]),
        nna_id=intervencion["nna_id"],
        fecha=intervencion["fecha"],
        tipo=intervencion["tipo"],
        motivo=intervencion["motivo"],
        descripcion=intervencion["descripcion"],
        resultados=intervencion.get("resultados"),
        derivacion=intervencion.get("derivacion"),
        estado=intervencion["estado"],
        prioridad=intervencion["prioridad"],
        fecha_proximo_seguimiento=intervencion.get("fecha_proximo_seguimiento"),
        creado_en=intervencion.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=intervencion.get("actualizado_en"),
        creado_por=intervencion["creado_por"],
        actualizado_por=intervencion.get("actualizado_por")
    )


@router.post("", response_model=IntervencionResponse, status_code=status.HTTP_201_CREATED)
async def create_intervencion(
    data: IntervencionCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nueva intervención
    """
    db = get_db()
    
    # Verificar que el NNA existe
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
    
    new_intervencion = {
        "nna_id": data.nna_id,
        "fecha": data.fecha,
        "tipo": data.tipo,
        "motivo": data.motivo,
        "descripcion": data.descripcion,
        "resultados": data.resultados,
        "derivacion": data.derivacion,
        "estado": data.estado,
        "prioridad": data.prioridad,
        "fecha_proximo_seguimiento": data.fecha_proximo_seguimiento,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.intervenciones.insert_one(new_intervencion)
    
    logger.info(f"Intervención creada para NNA {data.nna_id} por {current_user.email}")
    
    return IntervencionResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_intervencion.items() if k not in ["creado_por"]}
    )


@router.put("/{intervencion_id}", response_model=IntervencionResponse)
async def update_intervencion(
    intervencion_id: str,
    data: IntervencionUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar intervención
    """
    db = get_db()
    
    if not ObjectId.is_valid(intervencion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de intervención inválido"
        )
    
    existing = await db.intervenciones.find_one({"_id": ObjectId(intervencion_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervención no encontrada"
        )
    
    update_data = {
        "actualizado_en": datetime.now(timezone.utc),
        "actualizado_por": current_user.user_id
    }
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    await db.intervenciones.update_one(
        {"_id": ObjectId(intervencion_id)},
        {"$set": update_data}
    )
    
    updated = await db.intervenciones.find_one({"_id": ObjectId(intervencion_id)})
    
    logger.info(f"Intervención {intervencion_id} actualizada por {current_user.email}")
    
    return IntervencionResponse(
        id=str(updated["_id"]),
        nna_id=updated["nna_id"],
        fecha=updated["fecha"],
        tipo=updated["tipo"],
        motivo=updated["motivo"],
        descripcion=updated["descripcion"],
        resultados=updated.get("resultados"),
        derivacion=updated.get("derivacion"),
        estado=updated["estado"],
        prioridad=updated["prioridad"],
        fecha_proximo_seguimiento=updated.get("fecha_proximo_seguimiento"),
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        creado_por=updated["creado_por"],
        actualizado_por=updated.get("actualizado_por")
    )


@router.delete("/{intervencion_id}")
async def delete_intervencion(
    intervencion_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Eliminar intervención
    """
    db = get_db()
    
    if not ObjectId.is_valid(intervencion_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de intervención inválido"
        )
    
    existing = await db.intervenciones.find_one({"_id": ObjectId(intervencion_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervención no encontrada"
        )
    
    await db.intervenciones.delete_one({"_id": ObjectId(intervencion_id)})
    
    logger.info(f"Intervención {intervencion_id} eliminada por {current_user.email}")
    
    return {"message": "Intervención eliminada correctamente"}
