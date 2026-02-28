"""
Router de Seguimiento
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone, date
from bson import ObjectId
from app.database import get_db
from app.models.seguimiento import SeguimientoCreate, SeguimientoUpdate, SeguimientoResponse
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/seguimiento", tags=["Seguimiento"])


@router.get("", response_model=List[SeguimientoResponse])
async def list_seguimientos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    nna_id: Optional[str] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar seguimientos
    """
    db = get_db()
    
    query = {}
    if nna_id:
        query["nna_id"] = nna_id
    if tipo:
        query["tipo"] = tipo
    if estado:
        query["estado"] = estado
    
    cursor = db.seguimiento.find(query).skip(skip).limit(limit).sort("fecha", -1)
    seguimientos = await cursor.to_list(length=limit)
    
    return [
        SeguimientoResponse(
            id=str(s["_id"]),
            nna_id=s["nna_id"],
            fecha=s["fecha"],
            tipo=s["tipo"],
            area_salud=s.get("area_salud"),
            area_educativa=s.get("area_educativa"),
            area_social=s.get("area_social"),
            area_familiar=s.get("area_familiar"),
            area_emocional=s.get("area_emocional"),
            evaluacion_general=s["evaluacion_general"],
            fortalezas=s.get("fortalezas"),
            dificultades=s.get("dificultades"),
            objetivos_corto_plazo=s.get("objetivos_corto_plazo"),
            objetivos_medio_plazo=s.get("objetivos_medio_plazo"),
            objetivos_largo_plazo=s.get("objetivos_largo_plazo"),
            recomendaciones=s.get("recomendaciones"),
            estado=s["estado"],
            creado_en=s.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=s.get("actualizado_en"),
            creado_por=s["creado_por"]
        )
        for s in seguimientos
    ]


@router.get("/{seguimiento_id}", response_model=SeguimientoResponse)
async def get_seguimiento(
    seguimiento_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener seguimiento por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(seguimiento_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de seguimiento inválido"
        )
    
    seguimiento = await db.seguimiento.find_one({"_id": ObjectId(seguimiento_id)})
    
    if not seguimiento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seguimiento no encontrado"
        )
    
    return SeguimientoResponse(
        id=str(seguimiento["_id"]),
        nna_id=seguimiento["nna_id"],
        fecha=seguimiento["fecha"],
        tipo=seguimiento["tipo"],
        area_salud=seguimiento.get("area_salud"),
        area_educativa=seguimiento.get("area_educativa"),
        area_social=seguimiento.get("area_social"),
        area_familiar=seguimiento.get("area_familiar"),
        area_emocional=seguimiento.get("area_emocional"),
        evaluacion_general=seguimiento["evaluacion_general"],
        fortalezas=seguimiento.get("fortalezas"),
        dificultades=seguimiento.get("dificultades"),
        objetivos_corto_plazo=seguimiento.get("objetivos_corto_plazo"),
        objetivos_medio_plazo=seguimiento.get("objetivos_medio_plazo"),
        objetivos_largo_plazo=seguimiento.get("objetivos_largo_plazo"),
        recomendaciones=seguimiento.get("recomendaciones"),
        estado=seguimiento["estado"],
        creado_en=seguimiento.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=seguimiento.get("actualizado_en"),
        creado_por=seguimiento["creado_por"]
    )


@router.post("", response_model=SeguimientoResponse, status_code=status.HTTP_201_CREATED)
async def create_seguimiento(
    data: SeguimientoCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nuevo seguimiento
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
    
    new_seguimiento = {
        "nna_id": data.nna_id,
        "fecha": data.fecha,
        "tipo": data.tipo,
        "area_salud": data.area_salud,
        "area_educativa": data.area_educativa,
        "area_social": data.area_social,
        "area_familiar": data.area_familiar,
        "area_emocional": data.area_emocional,
        "evaluacion_general": data.evaluacion_general,
        "fortalezas": data.fortalezas,
        "dificultades": data.dificultades,
        "objetivos_corto_plazo": data.objetivos_corto_plazo,
        "objetivos_medio_plazo": data.objetivos_medio_plazo,
        "objetivos_largo_plazo": data.objetivos_largo_plazo,
        "recomendaciones": data.recomendaciones,
        "estado": data.estado,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.seguimiento.insert_one(new_seguimiento)
    
    logger.info(f"Seguimiento creado para NNA {data.nna_id} por {current_user.email}")
    
    return SeguimientoResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_seguimiento.items() if k not in ["creado_por"]}
    )


@router.put("/{seguimiento_id}", response_model=SeguimientoResponse)
async def update_seguimiento(
    seguimiento_id: str,
    data: SeguimientoUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar seguimiento
    """
    db = get_db()
    
    if not ObjectId.is_valid(seguimiento_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de seguimiento inválido"
        )
    
    existing = await db.seguimiento.find_one({"_id": ObjectId(seguimiento_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seguimiento no encontrado"
        )
    
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    await db.seguimiento.update_one(
        {"_id": ObjectId(seguimiento_id)},
        {"$set": update_data}
    )
    
    updated = await db.seguimiento.find_one({"_id": ObjectId(seguimiento_id)})
    
    logger.info(f"Seguimiento {seguimiento_id} actualizado por {current_user.email}")
    
    return SeguimientoResponse(
        id=str(updated["_id"]),
        nna_id=updated["nna_id"],
        fecha=updated["fecha"],
        tipo=updated["tipo"],
        area_salud=updated.get("area_salud"),
        area_educativa=updated.get("area_educativa"),
        area_social=updated.get("area_social"),
        area_familiar=updated.get("area_familiar"),
        area_emocional=updated.get("area_emocional"),
        evaluacion_general=updated["evaluacion_general"],
        fortalezas=updated.get("fortalezas"),
        dificultades=updated.get("dificultades"),
        objetivos_corto_plazo=updated.get("objetivos_corto_plazo"),
        objetivos_medio_plazo=updated.get("objetivos_medio_plazo"),
        objetivos_largo_plazo=updated.get("objetivos_largo_plazo"),
        recomendaciones=updated.get("recomendaciones"),
        estado=updated["estado"],
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        creado_por=updated["creado_por"]
    )


@router.delete("/{seguimiento_id}")
async def delete_seguimiento(
    seguimiento_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Eliminar seguimiento
    """
    db = get_db()
    
    if not ObjectId.is_valid(seguimiento_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de seguimiento inválido"
        )
    
    existing = await db.seguimiento.find_one({"_id": ObjectId(seguimiento_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seguimiento no encontrado"
        )
    
    await db.seguimiento.delete_one({"_id": ObjectId(seguimiento_id)})
    
    logger.info(f"Seguimiento {seguimiento_id} eliminado por {current_user.email}")
    
    return {"message": "Seguimiento eliminado correctamente"}
