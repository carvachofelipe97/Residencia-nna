"""
Router de Red de Apoyo Avanzada
Incluye: familia extensa, cuidadores temporales, PPF, referentes, contactos emergencia
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone, date
from bson import ObjectId
from app.database import get_db
from app.models.red_apoyo import RedApoyoCreate, RedApoyoUpdate, RedApoyoResponse, RedApoyoStats
from app.models.user import TokenData
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_tecnico, require_coordinador
from app.utils.validators import validate_rut_chile, format_rut
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/red-apoyo", tags=["Red de Apoyo"])


@router.get("", response_model=List[RedApoyoResponse])
async def list_red_apoyo(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    nna_id: Optional[str] = None,
    tipo_vinculo: Optional[str] = None,
    es_cuidador_temporal: Optional[bool] = None,
    es_ppf: Optional[bool] = None,
    es_contacto_emergencia: Optional[bool] = None,
    nivel_confiabilidad: Optional[str] = None,
    estado: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar red de apoyo
    """
    db = get_db()
    
    query = {}
    if nna_id:
        query["nna_id"] = nna_id
    if tipo_vinculo:
        query["tipo_vinculo"] = tipo_vinculo
    if es_cuidador_temporal is not None:
        query["es_cuidador_temporal"] = es_cuidador_temporal
    if es_ppf is not None:
        query["es_ppf"] = es_ppf
    if es_contacto_emergencia is not None:
        query["es_contacto_emergencia"] = es_contacto_emergencia
    if nivel_confiabilidad:
        query["nivel_confiabilidad"] = nivel_confiabilidad
    if estado:
        query["estado"] = estado
    if search:
        query["$or"] = [
            {"nombre": {"$regex": search, "$options": "i"}},
            {"apellido": {"$regex": search, "$options": "i"}},
            {"telefono_principal": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = db.red_apoyo.find(query).skip(skip).limit(limit).sort("nombre", 1)
    red_list = await cursor.to_list(length=limit)
    
    return [
        RedApoyoResponse(
            id=str(r["_id"]),
            nna_id=r["nna_id"],
            nombre=r["nombre"],
            apellido=r["apellido"],
            rut=r.get("rut"),
            fecha_nacimiento=r.get("fecha_nacimiento"),
            telefono_principal=r["telefono_principal"],
            telefono_secundario=r.get("telefono_secundario"),
            email=r.get("email"),
            direccion=r.get("direccion"),
            tipo_vinculo=r["tipo_vinculo"],
            descripcion_vinculo=r.get("descripcion_vinculo"),
            es_cuidador_temporal=r.get("es_cuidador_temporal", False),
            es_ppf=r.get("es_ppf", False),
            es_contacto_emergencia=r.get("es_contacto_emergencia", False),
            es_referente_significativo=r.get("es_referente_significativo", False),
            disponibilidad=r.get("disponibilidad", "limitada"),
            horario_especifico=r.get("horario_especifico"),
            nivel_confiabilidad=r.get("nivel_confiabilidad", "no_evaluado"),
            evaluacion_confiabilidad=r.get("evaluacion_confiabilidad"),
            estado=r.get("estado", "activo"),
            observaciones=r.get("observaciones"),
            tiene_antecedentes=r.get("tiene_antecedentes"),
            autorizado_para_retiro=r.get("autorizado_para_retiro", False),
            autorizado_para_informacion=r.get("autorizado_para_informacion", False),
            fecha_inicio_vinculo=r.get("fecha_inicio_vinculo"),
            fecha_fin_vinculo=r.get("fecha_fin_vinculo"),
            fecha_ultima_evaluacion=r.get("fecha_ultima_evaluacion"),
            evaluado_por=r.get("evaluado_por"),
            creado_en=r.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=r.get("actualizado_en"),
            creado_por=r["creado_por"]
        )
        for r in red_list
    ]


@router.get("/stats", response_model=RedApoyoStats)
async def get_red_apoyo_stats(
    nna_id: Optional[str] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Estadísticas de red de apoyo
    """
    db = get_db()
    
    query = {}
    if nna_id:
        query["nna_id"] = nna_id
    
    total = await db.red_apoyo.count_documents(query)
    
    # Por tipo de vínculo
    pipeline_tipo = [
        {"$match": query},
        {"$group": {"_id": "$tipo_vinculo", "count": {"$sum": 1}}}
    ]
    tipo_cursor = db.red_apoyo.aggregate(pipeline_tipo)
    por_tipo_vinculo = {t["_id"]: t["count"] async for t in tipo_cursor}
    
    # Cuidadores temporales
    cuidadores_temporales = await db.red_apoyo.count_documents({**query, "es_cuidador_temporal": True})
    
    # PPF
    ppf = await db.red_apoyo.count_documents({**query, "es_ppf": True})
    
    # Contactos de emergencia
    contactos_emergencia = await db.red_apoyo.count_documents({**query, "es_contacto_emergencia": True})
    
    # Por nivel de confiabilidad
    pipeline_confiabilidad = [
        {"$match": query},
        {"$group": {"_id": "$nivel_confiabilidad", "count": {"$sum": 1}}}
    ]
    confiabilidad_cursor = db.red_apoyo.aggregate(pipeline_confiabilidad)
    por_nivel_confiabilidad = {c["_id"]: c["count"] async for c in confiabilidad_cursor}
    
    # Por estado
    pipeline_estado = [
        {"$match": query},
        {"$group": {"_id": "$estado", "count": {"$sum": 1}}}
    ]
    estado_cursor = db.red_apoyo.aggregate(pipeline_estado)
    por_estado = {e["_id"]: e["count"] async for e in estado_cursor}
    
    return RedApoyoStats(
        total=total,
        por_tipo_vinculo=por_tipo_vinculo,
        cuidadores_temporales=cuidadores_temporales,
        ppf=ppf,
        contactos_emergencia=contactos_emergencia,
        por_nivel_confiabilidad=por_nivel_confiabilidad,
        por_estado=por_estado
    )


@router.get("/nna/{nna_id}", response_model=List[RedApoyoResponse])
async def get_red_apoyo_by_nna(
    nna_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener red de apoyo de un NNA específico
    """
    db = get_db()
    
    if not ObjectId.is_valid(nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    # Verificar que el NNA existe
    nna = await db.nna.find_one({"_id": ObjectId(nna_id)})
    if not nna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    cursor = db.red_apoyo.find({"nna_id": nna_id, "estado": {"$ne": "rechazado"}}).sort([
        ("es_contacto_emergencia", -1),
        ("es_cuidador_temporal", -1),
        ("nivel_confiabilidad", -1),
        ("nombre", 1)
    ])
    
    red_list = await cursor.to_list(length=100)
    
    return [
        RedApoyoResponse(
            id=str(r["_id"]),
            nna_id=r["nna_id"],
            nombre=r["nombre"],
            apellido=r["apellido"],
            rut=r.get("rut"),
            fecha_nacimiento=r.get("fecha_nacimiento"),
            telefono_principal=r["telefono_principal"],
            telefono_secundario=r.get("telefono_secundario"),
            email=r.get("email"),
            direccion=r.get("direccion"),
            tipo_vinculo=r["tipo_vinculo"],
            descripcion_vinculo=r.get("descripcion_vinculo"),
            es_cuidador_temporal=r.get("es_cuidador_temporal", False),
            es_ppf=r.get("es_ppf", False),
            es_contacto_emergencia=r.get("es_contacto_emergencia", False),
            es_referente_significativo=r.get("es_referente_significativo", False),
            disponibilidad=r.get("disponibilidad", "limitada"),
            horario_especifico=r.get("horario_especifico"),
            nivel_confiabilidad=r.get("nivel_confiabilidad", "no_evaluado"),
            evaluacion_confiabilidad=r.get("evaluacion_confiabilidad"),
            estado=r.get("estado", "activo"),
            observaciones=r.get("observaciones"),
            tiene_antecedentes=r.get("tiene_antecedentes"),
            autorizado_para_retiro=r.get("autorizado_para_retiro", False),
            autorizado_para_informacion=r.get("autorizado_para_informacion", False),
            fecha_inicio_vinculo=r.get("fecha_inicio_vinculo"),
            fecha_fin_vinculo=r.get("fecha_fin_vinculo"),
            fecha_ultima_evaluacion=r.get("fecha_ultima_evaluacion"),
            evaluado_por=r.get("evaluado_por"),
            creado_en=r.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=r.get("actualizado_en"),
            creado_por=r["creado_por"]
        )
        for r in red_list
    ]


@router.get("/cuidadores-temporales", response_model=List[RedApoyoResponse])
async def get_cuidadores_temporales(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    disponible: Optional[bool] = None,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Listar cuidadores temporales
    """
    db = get_db()
    
    query = {"es_cuidador_temporal": True, "estado": "activo"}
    
    if disponible is not None:
        if disponible:
            query["disponibilidad"] = {"$ne": "no_disponible"}
        else:
            query["disponibilidad"] = "no_disponible"
    
    cursor = db.red_apoyo.find(query).skip(skip).limit(limit).sort("nombre", 1)
    red_list = await cursor.to_list(length=limit)
    
    return [
        RedApoyoResponse(
            id=str(r["_id"]),
            nna_id=r["nna_id"],
            nombre=r["nombre"],
            apellido=r["apellido"],
            rut=r.get("rut"),
            fecha_nacimiento=r.get("fecha_nacimiento"),
            telefono_principal=r["telefono_principal"],
            telefono_secundario=r.get("telefono_secundario"),
            email=r.get("email"),
            direccion=r.get("direccion"),
            tipo_vinculo=r["tipo_vinculo"],
            descripcion_vinculo=r.get("descripcion_vinculo"),
            es_cuidador_temporal=r.get("es_cuidador_temporal", False),
            es_ppf=r.get("es_ppf", False),
            es_contacto_emergencia=r.get("es_contacto_emergencia", False),
            es_referente_significativo=r.get("es_referente_significativo", False),
            disponibilidad=r.get("disponibilidad", "limitada"),
            horario_especifico=r.get("horario_especifico"),
            nivel_confiabilidad=r.get("nivel_confiabilidad", "no_evaluado"),
            evaluacion_confiabilidad=r.get("evaluacion_confiabilidad"),
            estado=r.get("estado", "activo"),
            observaciones=r.get("observaciones"),
            tiene_antecedentes=r.get("tiene_antecedentes"),
            autorizado_para_retiro=r.get("autorizado_para_retiro", False),
            autorizado_para_informacion=r.get("autorizado_para_informacion", False),
            fecha_inicio_vinculo=r.get("fecha_inicio_vinculo"),
            fecha_fin_vinculo=r.get("fecha_fin_vinculo"),
            fecha_ultima_evaluacion=r.get("fecha_ultima_evaluacion"),
            evaluado_por=r.get("evaluado_por"),
            creado_en=r.get("creado_en", datetime.now(timezone.utc)),
            actualizado_en=r.get("actualizado_en"),
            creado_por=r["creado_por"]
        )
        for r in red_list
    ]


@router.get("/{red_id}", response_model=RedApoyoResponse)
async def get_red_apoyo_by_id(
    red_id: str,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Obtener miembro de red de apoyo por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(red_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    red = await db.red_apoyo.find_one({"_id": ObjectId(red_id)})
    
    if not red:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro de red de apoyo no encontrado"
        )
    
    return RedApoyoResponse(
        id=str(red["_id"]),
        nna_id=red["nna_id"],
        nombre=red["nombre"],
        apellido=red["apellido"],
        rut=red.get("rut"),
        fecha_nacimiento=red.get("fecha_nacimiento"),
        telefono_principal=red["telefono_principal"],
        telefono_secundario=red.get("telefono_secundario"),
        email=red.get("email"),
        direccion=red.get("direccion"),
        tipo_vinculo=red["tipo_vinculo"],
        descripcion_vinculo=red.get("descripcion_vinculo"),
        es_cuidador_temporal=red.get("es_cuidador_temporal", False),
        es_ppf=red.get("es_ppf", False),
        es_contacto_emergencia=red.get("es_contacto_emergencia", False),
        es_referente_significativo=red.get("es_referente_significativo", False),
        disponibilidad=red.get("disponibilidad", "limitada"),
        horario_especifico=red.get("horario_especifico"),
        nivel_confiabilidad=red.get("nivel_confiabilidad", "no_evaluado"),
        evaluacion_confiabilidad=red.get("evaluacion_confiabilidad"),
        estado=red.get("estado", "activo"),
        observaciones=red.get("observaciones"),
        tiene_antecedentes=red.get("tiene_antecedentes"),
        autorizado_para_retiro=red.get("autorizado_para_retiro", False),
        autorizado_para_informacion=red.get("autorizado_para_informacion", False),
        fecha_inicio_vinculo=red.get("fecha_inicio_vinculo"),
        fecha_fin_vinculo=red.get("fecha_fin_vinculo"),
        fecha_ultima_evaluacion=red.get("fecha_ultima_evaluacion"),
        evaluado_por=red.get("evaluado_por"),
        creado_en=red.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=red.get("actualizado_en"),
        creado_por=red["creado_por"]
    )


@router.post("", response_model=RedApoyoResponse, status_code=status.HTTP_201_CREATED)
async def create_red_apoyo(
    data: RedApoyoCreate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Crear nuevo miembro de red de apoyo
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
    
    # Validar RUT si se proporciona
    if data.rut and not validate_rut_chile(data.rut):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RUT inválido"
        )
    
    # Formatear RUT
    rut_formateado = format_rut(data.rut) if data.rut else None
    
    new_red = {
        "nna_id": data.nna_id,
        "nombre": data.nombre,
        "apellido": data.apellido,
        "rut": rut_formateado,
        "fecha_nacimiento": data.fecha_nacimiento,
        "telefono_principal": data.telefono_principal,
        "telefono_secundario": data.telefono_secundario,
        "email": data.email,
        "direccion": data.direccion.dict() if data.direccion else None,
        "tipo_vinculo": data.tipo_vinculo,
        "descripcion_vinculo": data.descripcion_vinculo,
        "es_cuidador_temporal": data.es_cuidador_temporal,
        "es_ppf": data.es_ppf,
        "es_contacto_emergencia": data.es_contacto_emergencia,
        "es_referente_significativo": data.es_referente_significativo,
        "disponibilidad": data.disponibilidad,
        "horario_especifico": data.horario_especifico,
        "nivel_confiabilidad": data.nivel_confiabilidad,
        "evaluacion_confiabilidad": data.evaluacion_confiabilidad,
        "estado": data.estado,
        "observaciones": data.observaciones,
        "tiene_antecedentes": data.tiene_antecedentes,
        "autorizado_para_retiro": data.autorizado_para_retiro,
        "autorizado_para_informacion": data.autorizado_para_informacion,
        "fecha_inicio_vinculo": data.fecha_inicio_vinculo,
        "fecha_fin_vinculo": data.fecha_fin_vinculo,
        "fecha_ultima_evaluacion": data.fecha_ultima_evaluacion,
        "evaluado_por": data.evaluado_por,
        "creado_en": datetime.now(timezone.utc),
        "creado_por": current_user.user_id
    }
    
    result = await db.red_apoyo.insert_one(new_red)
    
    logger.info(f"Miembro de red de apoyo creado: {data.nombre} {data.apellido} por {current_user.email}")
    
    return RedApoyoResponse(
        id=str(result.inserted_id),
        **{k: v for k, v in new_red.items() if k not in ["creado_por"]}
    )


@router.put("/{red_id}", response_model=RedApoyoResponse)
async def update_red_apoyo(
    red_id: str,
    data: RedApoyoUpdate,
    current_user: TokenData = Depends(require_tecnico)
):
    """
    Actualizar miembro de red de apoyo
    """
    db = get_db()
    
    if not ObjectId.is_valid(red_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    existing = await db.red_apoyo.find_one({"_id": ObjectId(red_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro de red de apoyo no encontrado"
        )
    
    # Validar RUT si se actualiza
    if data.rut and not validate_rut_chile(data.rut):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RUT inválido"
        )
    
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            if field == "direccion" and value:
                update_data[field] = value.dict()
            elif field == "rut" and value:
                update_data[field] = format_rut(value)
            else:
                update_data[field] = value
    
    await db.red_apoyo.update_one(
        {"_id": ObjectId(red_id)},
        {"$set": update_data}
    )
    
    updated = await db.red_apoyo.find_one({"_id": ObjectId(red_id)})
    
    logger.info(f"Red de apoyo {red_id} actualizada por {current_user.email}")
    
    return RedApoyoResponse(
        id=str(updated["_id"]),
        nna_id=updated["nna_id"],
        nombre=updated["nombre"],
        apellido=updated["apellido"],
        rut=updated.get("rut"),
        fecha_nacimiento=updated.get("fecha_nacimiento"),
        telefono_principal=updated["telefono_principal"],
        telefono_secundario=updated.get("telefono_secundario"),
        email=updated.get("email"),
        direccion=updated.get("direccion"),
        tipo_vinculo=updated["tipo_vinculo"],
        descripcion_vinculo=updated.get("descripcion_vinculo"),
        es_cuidador_temporal=updated.get("es_cuidador_temporal", False),
        es_ppf=updated.get("es_ppf", False),
        es_contacto_emergencia=updated.get("es_contacto_emergencia", False),
        es_referente_significativo=updated.get("es_referente_significativo", False),
        disponibilidad=updated.get("disponibilidad", "limitada"),
        horario_especifico=updated.get("horario_especifico"),
        nivel_confiabilidad=updated.get("nivel_confiabilidad", "no_evaluado"),
        evaluacion_confiabilidad=updated.get("evaluacion_confiabilidad"),
        estado=updated.get("estado", "activo"),
        observaciones=updated.get("observaciones"),
        tiene_antecedentes=updated.get("tiene_antecedentes"),
        autorizado_para_retiro=updated.get("autorizado_para_retiro", False),
        autorizado_para_informacion=updated.get("autorizado_para_informacion", False),
        fecha_inicio_vinculo=updated.get("fecha_inicio_vinculo"),
        fecha_fin_vinculo=updated.get("fecha_fin_vinculo"),
        fecha_ultima_evaluacion=updated.get("fecha_ultima_evaluacion"),
        evaluado_por=updated.get("evaluado_por"),
        creado_en=updated.get("creado_en", datetime.now(timezone.utc)),
        actualizado_en=updated.get("actualizado_en"),
        creado_por=updated["creado_por"]
    )


@router.post("/{red_id}/evaluar")
async def evaluar_red_apoyo(
    red_id: str,
    nivel_confiabilidad: str,
    evaluacion: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Evaluar nivel de confiabilidad de un miembro de red de apoyo
    Solo coordinador o admin
    """
    db = get_db()
    
    if not ObjectId.is_valid(red_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    if nivel_confiabilidad not in ["alto", "medio", "bajo", "no_evaluado"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nivel de confiabilidad inválido"
        )
    
    existing = await db.red_apoyo.find_one({"_id": ObjectId(red_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro de red de apoyo no encontrado"
        )
    
    await db.red_apoyo.update_one(
        {"_id": ObjectId(red_id)},
        {
            "$set": {
                "nivel_confiabilidad": nivel_confiabilidad,
                "evaluacion_confiabilidad": evaluacion,
                "fecha_ultima_evaluacion": date.today().isoformat(),
                "evaluado_por": current_user.user_id,
                "actualizado_en": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"Red de apoyo {red_id} evaluada: {nivel_confiabilidad} por {current_user.email}")
    
    return {"message": f"Evaluación registrada: nivel {nivel_confiabilidad}"}


@router.delete("/{red_id}")
async def delete_red_apoyo(
    red_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Eliminar miembro de red de apoyo (solo coordinador o admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(red_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )
    
    existing = await db.red_apoyo.find_one({"_id": ObjectId(red_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro de red de apoyo no encontrado"
        )
    
    await db.red_apoyo.delete_one({"_id": ObjectId(red_id)})
    
    logger.info(f"Red de apoyo {red_id} eliminada por {current_user.email}")
    
    return {"message": "Miembro de red de apoyo eliminado correctamente"}
