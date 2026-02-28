"""
Router de NNA - Gestión de Niños, Niñas y Adolescentes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.models.nna import NNACreate, NNAUpdate, NNAResponse
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador, can_edit_any_record
from app.utils.validators import validate_rut_chile, format_rut
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nna", tags=["NNA"])


@router.get("", response_model=List[NNAResponse])
async def list_nna(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    estado: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar NNA registrados
    """
    db = get_db()
    
    query = {}
    if estado:
        query["estado"] = estado
    if search:
        query["$or"] = [
            {"nombre": {"$regex": search, "$options": "i"}},
            {"apellido": {"$regex": search, "$options": "i"}},
            {"rut": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = db.nna.find(query).skip(skip).limit(limit).sort("creado_en", -1)
    nna_list = await cursor.to_list(length=limit)
    
    return [
        NNAResponse(
            id=str(n["_id"]),
            nombre=n["nombre"],
            apellido=n["apellido"],
            rut=n.get("rut"),
            fecha_nacimiento=n.get("fecha_nacimiento"),
            edad=n.get("edad"),
            genero=n.get("genero", "No especifica"),
            fecha_ingreso=n["fecha_ingreso"],
            fecha_egreso=n.get("fecha_egreso"),
            estado=n["estado"],
            telefono=n.get("telefono"),
            direccion=n.get("direccion"),
            comuna=n.get("comuna"),
            region=n.get("region"),
            contacto_emergencia=n.get("contacto_emergencia"),
            alergias=n.get("alergias"),
            medicamentos=n.get("medicamentos"),
            condiciones_medicas=n.get("condiciones_medicas"),
            establecimiento_educacional=n.get("establecimiento_educacional"),
            curso=n.get("curso"),
            observaciones=n.get("observaciones"),
            creado_en=n.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=n.get("actualizado_en"),
            creado_por=n.get("creado_por")
        )
        for n in nna_list
    ]


@router.get("/stats", response_model=dict)
async def get_nna_stats(
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener estadísticas de NNA
    """
    db = get_db()
    
    total = await db.nna.count_documents({})
    activos = await db.nna.count_documents({"estado": "activo"})
    egresados = await db.nna.count_documents({"estado": "egresado"})
    trasladados = await db.nna.count_documents({"estado": "trasladado"})
    temporal = await db.nna.count_documents({"estado": "temporal"})
    
    # Por género
    pipeline_genero = [
        {"$group": {"_id": "$genero", "count": {"$sum": 1}}}
    ]
    genero_cursor = db.nna.aggregate(pipeline_genero)
    por_genero = {g["_id"]: g["count"] async for g in genero_cursor}
    
    return {
        "total": total,
        "activos": activos,
        "egresados": egresados,
        "trasladados": trasladados,
        "temporal": temporal,
        "por_genero": por_genero
    }


@router.get("/{nna_id}", response_model=NNAResponse)
async def get_nna(
    nna_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener un NNA por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    nna = await db.nna.find_one({"_id": ObjectId(nna_id)})
    
    if not nna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    return NNAResponse(
        id=str(nna["_id"]),
        nombre=nna["nombre"],
        apellido=nna["apellido"],
        rut=nna.get("rut"),
        fecha_nacimiento=nna.get("fecha_nacimiento"),
        edad=nna.get("edad"),
        genero=nna.get("genero", "No especifica"),
        fecha_ingreso=nna["fecha_ingreso"],
        fecha_egreso=nna.get("fecha_egreso"),
        estado=nna["estado"],
        telefono=nna.get("telefono"),
        direccion=nna.get("direccion"),
        comuna=nna.get("comuna"),
        region=nna.get("region"),
        contacto_emergencia=nna.get("contacto_emergencia"),
        alergias=nna.get("alergias"),
        medicamentos=nna.get("medicamentos"),
        condiciones_medicas=nna.get("condiciones_medicas"),
        establecimiento_educacional=nna.get("establecimiento_educacional"),
        curso=nna.get("curso"),
        observaciones=nna.get("observaciones"),
        creado_en=nna.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=nna.get("actualizado_en"),
        creado_por=nna.get("creado_por")
    )


@router.post("", response_model=NNAResponse, status_code=status.HTTP_201_CREATED)
async def create_nna(
    nna_data: NNACreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nuevo NNA
    """
    db = get_db()
    
    # Validar RUT si se proporciona
    if nna_data.rut and not validate_rut_chile(nna_data.rut):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RUT inválido"
        )
    
    # Verificar RUT único
    if nna_data.rut:
        existing = await db.nna.find_one({"rut": nna_data.rut})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un NNA con este RUT"
            )
    
    # Formatear RUT
    rut_formateado = format_rut(nna_data.rut) if nna_data.rut else None
    
    # Crear NNA
    new_nna = {
        "nombre": nna_data.nombre,
        "apellido": nna_data.apellido,
        "rut": rut_formateado,
        "fecha_nacimiento": nna_data.fecha_nacimiento,
        "edad": nna_data.edad,
        "genero": nna_data.genero,
        "fecha_ingreso": nna_data.fecha_ingreso,
        "fecha_egreso": nna_data.fecha_egreso,
        "estado": nna_data.estado,
        "telefono": nna_data.telefono,
        "direccion": nna_data.direccion,
        "comuna": nna_data.comuna,
        "region": nna_data.region,
        "contacto_emergencia": nna_data.contacto_emergencia.dict() if nna_data.contacto_emergencia else None,
        "alergias": nna_data.alergias,
        "medicamentos": nna_data.medicamentos,
        "condiciones_medicas": nna_data.condiciones_medicas,
        "establecimiento_educacional": nna_data.establecimiento_educacional,
        "curso": nna_data.curso,
        "observaciones": nna_data.observaciones,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.nna.insert_one(new_nna)
    
    logger.info(f"NNA creado: {nna_data.nombre} {nna_data.apellido} por {current_user.email}")
    
    return NNAResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_nna.items() if k not in ["creado_por"]}
    )


@router.put("/{nna_id}", response_model=NNAResponse)
async def update_nna(
    nna_id: str,
    nna_data: NNAUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar NNA
    """
    db = get_db()
    
    if not ObjectId.is_valid(nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    # Verificar que existe
    existing = await db.nna.find_one({"_id": ObjectId(nna_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    # Validar RUT si se actualiza
    if nna_data.rut and not validate_rut_chile(nna_data.rut):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RUT inválido"
        )
    
    # Construir update
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    for field, value in nna_data.dict(exclude_unset=True).items():
        if value is not None:
            if field == "contacto_emergencia" and value:
                update_data[field] = value
            elif field == "rut" and value:
                update_data[field] = format_rut(value)
            else:
                update_data[field] = value
    
    await db.nna.update_one(
        {"_id": ObjectId(nna_id)},
        {"$set": update_data}
    )
    
    # Obtener actualizado
    updated = await db.nna.find_one({"_id": ObjectId(nna_id)})
    
    logger.info(f"NNA actualizado: {updated['nombre']} {updated['apellido']} por {current_user.email}")
    
    return NNAResponse(
        id=str(updated["_id"]),
        nombre=updated["nombre"],
        apellido=updated["apellido"],
        rut=updated.get("rut"),
        fecha_nacimiento=updated.get("fecha_nacimiento"),
        edad=updated.get("edad"),
        genero=updated.get("genero", "No especifica"),
        fecha_ingreso=updated["fecha_ingreso"],
        fecha_egreso=updated.get("fecha_egreso"),
        estado=updated["estado"],
        telefono=updated.get("telefono"),
        direccion=updated.get("direccion"),
        comuna=updated.get("comuna"),
        region=updated.get("region"),
        contacto_emergencia=updated.get("contacto_emergencia"),
        alergias=updated.get("alergias"),
        medicamentos=updated.get("medicamentos"),
        condiciones_medicas=updated.get("condiciones_medicas"),
        establecimiento_educacional=updated.get("establecimiento_educacional"),
        curso=updated.get("curso"),
        observaciones=updated.get("observaciones"),
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        creado_por=updated.get("creado_por")
    )


@router.delete("/{nna_id}")
async def delete_nna(
    nna_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Eliminar NNA (Solo Coordinador y Admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    existing = await db.nna.find_one({"_id": ObjectId(nna_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    # Eliminar NNA y registros relacionados
    await db.nna.delete_one({"_id": ObjectId(nna_id)})
    await db.intervenciones.delete_many({"nna_id": nna_id})
    await db.seguimiento.delete_many({"nna_id": nna_id})
    
    # Actualizar talleres
    await db.talleres.update_many(
        {"participantes.nna_id": nna_id},
        {"$pull": {"participantes": {"nna_id": nna_id}}}
    )
    
    logger.info(f"NNA eliminado: {existing['nombre']} {existing['apellido']} por {current_user.email}")
    
    return {"message": "NNA eliminado correctamente"}
