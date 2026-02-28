"""
Router de Talleres
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone, date
from bson import ObjectId
from app.database import get_db
from app.models.taller import TallerCreate, TallerUpdate, TallerResponse, ParticipanteTaller
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/talleres", tags=["Talleres"])


@router.get("", response_model=List[TallerResponse])
async def list_talleres(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    estado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar talleres
    """
    db = get_db()
    
    query = {}
    if estado:
        query["estado"] = estado
    if fecha_desde or fecha_hasta:
        query["fecha"] = {}
        if fecha_desde:
            query["fecha"]["$gte"] = fecha_desde
        if fecha_hasta:
            query["fecha"]["$lte"] = fecha_hasta
    
    cursor = db.talleres.find(query).skip(skip).limit(limit).sort("fecha", -1)
    talleres = await cursor.to_list(length=limit)
    
    return [
        TallerResponse(
            id=str(t["_id"]),
            nombre=t["nombre"],
            descripcion=t.get("descripcion"),
            fecha=t["fecha"],
            hora_inicio=t["hora_inicio"],
            hora_termino=t["hora_termino"],
            ubicacion=t.get("ubicacion"),
            objetivos=t.get("objetivos"),
            materiales=t.get("materiales"),
            responsable_id=t["responsable_id"],
            participantes=t.get("participantes", []),
            capacidad_maxima=t.get("capacidad_maxima", 20),
            estado=t["estado"],
            creado_en=t.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=t.get("actualizado_en"),
            creado_por=t.get("creado_por")
        )
        for t in talleres
    ]


@router.get("/stats", response_model=dict)
async def get_talleres_stats(
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Estadísticas de talleres
    """
    db = get_db()
    
    total = await db.talleres.count_documents({})
    
    # Por estado
    pipeline_estado = [
        {"$group": {"_id": "$estado", "count": {"$sum": 1}}}
    ]
    estado_cursor = db.talleres.aggregate(pipeline_estado)
    por_estado = {e["_id"]: e["count"] async for e in estado_cursor}
    
    # Total de participantes
    pipeline_participantes = [
        {"$unwind": "$participantes"},
        {"$group": {"_id": None, "total": {"$sum": 1}}}
    ]
    participantes_result = await db.talleres.aggregate(pipeline_participantes).to_list(1)
    total_participantes = participantes_result[0]["total"] if participantes_result else 0
    
    return {
        "total_talleres": total,
        "por_estado": por_estado,
        "total_participantes": total_participantes
    }


@router.get("/{taller_id}", response_model=TallerResponse)
async def get_taller(
    taller_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener taller por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(taller_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de taller inválido"
        )
    
    taller = await db.talleres.find_one({"_id": ObjectId(taller_id)})
    
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    
    return TallerResponse(
        id=str(taller["_id"]),
        nombre=taller["nombre"],
        descripcion=taller.get("descripcion"),
        fecha=taller["fecha"],
        hora_inicio=taller["hora_inicio"],
        hora_termino=taller["hora_termino"],
        ubicacion=taller.get("ubicacion"),
        objetivos=taller.get("objetivos"),
        materiales=taller.get("materiales"),
        responsable_id=taller["responsable_id"],
        participantes=taller.get("participantes", []),
        capacidad_maxima=taller.get("capacidad_maxima", 20),
        estado=taller["estado"],
        creado_en=taller.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=taller.get("actualizado_en"),
        creado_por=taller.get("creado_por")
    )


@router.post("", response_model=TallerResponse, status_code=status.HTTP_201_CREATED)
async def create_taller(
    data: TallerCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nuevo taller
    """
    db = get_db()
    
    new_taller = {
        "nombre": data.nombre,
        "descripcion": data.descripcion,
        "fecha": data.fecha,
        "hora_inicio": data.hora_inicio,
        "hora_termino": data.hora_termino,
        "ubicacion": data.ubicacion,
        "objetivos": data.objetivos,
        "materiales": data.materiales,
        "responsable_id": data.responsable_id,
        "participantes": [p.dict() for p in data.participantes],
        "capacidad_maxima": data.capacidad_maxima,
        "estado": data.estado,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.talleres.insert_one(new_taller)
    
    logger.info(f"Taller creado: {data.nombre} por {current_user.email}")
    
    return TallerResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_taller.items() if k not in ["creado_por"]}
    )


@router.put("/{taller_id}", response_model=TallerResponse)
async def update_taller(
    taller_id: str,
    data: TallerUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar taller
    """
    db = get_db()
    
    if not ObjectId.is_valid(taller_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de taller inválido"
        )
    
    existing = await db.talleres.find_one({"_id": ObjectId(taller_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            if field == "participantes" and value:
                update_data[field] = [p.dict() for p in value]
            else:
                update_data[field] = value
    
    await db.talleres.update_one(
        {"_id": ObjectId(taller_id)},
        {"$set": update_data}
    )
    
    updated = await db.talleres.find_one({"_id": ObjectId(taller_id)})
    
    logger.info(f"Taller {taller_id} actualizado por {current_user.email}")
    
    return TallerResponse(
        id=str(updated["_id"]),
        nombre=updated["nombre"],
        descripcion=updated.get("descripcion"),
        fecha=updated["fecha"],
        hora_inicio=updated["hora_inicio"],
        hora_termino=updated["hora_termino"],
        ubicacion=updated.get("ubicacion"),
        objetivos=updated.get("objetivos"),
        materiales=updated.get("materiales"),
        responsable_id=updated["responsable_id"],
        participantes=updated.get("participantes", []),
        capacidad_maxima=updated.get("capacidad_maxima", 20),
        estado=updated["estado"],
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        creado_por=updated.get("creado_por")
    )


@router.delete("/{taller_id}")
async def delete_taller(
    taller_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Eliminar taller
    """
    db = get_db()
    
    if not ObjectId.is_valid(taller_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de taller inválido"
        )
    
    existing = await db.talleres.find_one({"_id": ObjectId(taller_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    
    await db.talleres.delete_one({"_id": ObjectId(taller_id)})
    
    logger.info(f"Taller {taller_id} eliminado por {current_user.email}")
    
    return {"message": "Taller eliminado correctamente"}


@router.post("/{taller_id}/participantes")
async def add_participante(
    taller_id: str,
    participante: ParticipanteTaller,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Agregar participante a taller
    """
    db = get_db()
    
    if not ObjectId.is_valid(taller_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de taller inválido"
        )
    
    if not ObjectId.is_valid(participante.nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    # Verificar que el NNA existe
    nna = await db.nna.find_one({"_id": ObjectId(participante.nna_id)})
    if not nna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    # Verificar capacidad
    taller = await db.talleres.find_one({"_id": ObjectId(taller_id)})
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    
    participantes_actuales = len(taller.get("participantes", []))
    capacidad = taller.get("capacidad_maxima", 20)
    
    if participantes_actuales >= capacidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Taller ha alcanzado su capacidad máxima"
        )
    
    # Verificar que no esté ya inscrito
    ya_inscrito = any(
        p["nna_id"] == participante.nna_id 
        for p in taller.get("participantes", [])
    )
    
    if ya_inscrito:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NNA ya está inscrito en este taller"
        )
    
    await db.talleres.update_one(
        {"_id": ObjectId(taller_id)},
        {"$push": {"participantes": participante.dict()}}
    )
    
    logger.info(f"NNA {participante.nna_id} agregado a taller {taller_id}")
    
    return {"message": "Participante agregado correctamente"}


@router.delete("/{taller_id}/participantes/{nna_id}")
async def remove_participante(
    taller_id: str,
    nna_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Eliminar participante de taller
    """
    db = get_db()
    
    if not ObjectId.is_valid(taller_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de taller inválido"
        )
    
    await db.talleres.update_one(
        {"_id": ObjectId(taller_id)},
        {"$pull": {"participantes": {"nna_id": nna_id}}}
    )
    
    logger.info(f"NNA {nna_id} removido de taller {taller_id}")
    
    return {"message": "Participante removido correctamente"}
