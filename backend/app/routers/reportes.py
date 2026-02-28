"""
Router de Reportes y Estadísticas
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime, date, timedelta
from bson import ObjectId
from app.database import get_db
from app.models.user import TokenData
from app.middleware.rbac import require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Estadísticas para el dashboard principal
    """
    db = get_db()
    
    # NNA
    total_nna = await db.nna.count_documents({})
    nna_activos = await db.nna.count_documents({"estado": "activo"})
    nna_egresados = await db.nna.count_documents({"estado": "egresado"})
    
    # Intervenciones
    total_intervenciones = await db.intervenciones.count_documents({})
    intervenciones_pendientes = await db.intervenciones.count_documents({"estado": "pendiente"})
    intervenciones_urgentes = await db.intervenciones.count_documents({"prioridad": "urgente"})
    
    # Talleres
    total_talleres = await db.talleres.count_documents({})
    talleres_proximos = await db.talleres.count_documents({
        "fecha": {"$gte": date.today()},
        "estado": {"$in": ["programado", "en_curso"]}
    })
    
    # Usuarios
    total_usuarios = await db.usuarios.count_documents({})
    usuarios_activos = await db.usuarios.count_documents({"activo": True})
    
    # Intervenciones por mes (últimos 6 meses)
    seis_meses_atras = date.today() - timedelta(days=180)
    pipeline_meses = [
        {
            "$match": {
                "fecha": {"$gte": seis_meses_atras}
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$fecha"},
                    "month": {"$month": "$fecha"}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    
    meses_cursor = db.intervenciones.aggregate(pipeline_meses)
    intervenciones_por_mes = [
        {
            "mes": f"{m['_id']['year']}-{m['_id']['month']:02d}",
            "cantidad": m["count"]
        }
        async for m in meses_cursor
    ]
    
    return {
        "nna": {
            "total": total_nna,
            "activos": nna_activos,
            "egresados": nna_egresados
        },
        "intervenciones": {
            "total": total_intervenciones,
            "pendientes": intervenciones_pendientes,
            "urgentes": intervenciones_urgentes
        },
        "talleres": {
            "total": total_talleres,
            "proximos": talleres_proximos
        },
        "usuarios": {
            "total": total_usuarios,
            "activos": usuarios_activos
        },
        "intervenciones_por_mes": intervenciones_por_mes
    }


@router.get("/nna/detalle/{nna_id}")
async def get_nna_report(
    nna_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Reporte completo de un NNA
    """
    db = get_db()
    
    if not ObjectId.is_valid(nna_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de NNA inválido"
        )
    
    # Obtener NNA
    nna = await db.nna.find_one({"_id": ObjectId(nna_id)})
    if not nna:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NNA no encontrado"
        )
    
    # Obtener intervenciones
    intervenciones = await db.intervenciones.find(
        {"nna_id": nna_id}
    ).sort("fecha", -1).to_list(100)
    
    # Obtener seguimientos
    seguimientos = await db.seguimiento.find(
        {"nna_id": nna_id}
    ).sort("fecha", -1).to_list(100)
    
    # Obtener talleres donde participa
    talleres = await db.talleres.find(
        {"participantes.nna_id": nna_id}
    ).sort("fecha", -1).to_list(100)
    
    return {
        "nna": {
            "id": str(nna["_id"]),
            "nombre": f"{nna['nombre']} {nna['apellido']}",
            "rut": nna.get("rut"),
            "estado": nna["estado"],
            "fecha_ingreso": nna["fecha_ingreso"]
        },
        "resumen": {
            "total_intervenciones": len(intervenciones),
            "total_seguimientos": len(seguimientos),
            "total_talleres": len(talleres)
        },
        "intervenciones": [
            {
                "id": str(i["_id"]),
                "fecha": i["fecha"],
                "tipo": i["tipo"],
                "motivo": i["motivo"],
                "estado": i["estado"],
                "prioridad": i["prioridad"]
            }
            for i in intervenciones
        ],
        "seguimientos": [
            {
                "id": str(s["_id"]),
                "fecha": s["fecha"],
                "tipo": s["tipo"],
                "evaluacion_general": s["evaluacion_general"][:100] + "..." if len(s["evaluacion_general"]) > 100 else s["evaluacion_general"]
            }
            for s in seguimientos
        ],
        "talleres": [
            {
                "id": str(t["_id"]),
                "nombre": t["nombre"],
                "fecha": t["fecha"],
                "estado": t["estado"]
            }
            for t in talleres
        ]
    }


@router.get("/intervenciones/por-tipo")
async def get_intervenciones_por_tipo(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Reporte de intervenciones agrupadas por tipo
    """
    db = get_db()
    
    match_stage = {}
    if fecha_desde or fecha_hasta:
        match_stage["fecha"] = {}
        if fecha_desde:
            match_stage["fecha"]["$gte"] = fecha_desde
        if fecha_hasta:
            match_stage["fecha"]["$lte"] = fecha_hasta
    
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {
            "$group": {
                "_id": "$tipo",
                "cantidad": {"$sum": 1},
                "completadas": {
                    "$sum": {"$cond": [{"$eq": ["$estado", "completada"]}, 1, 0]}
                },
                "pendientes": {
                    "$sum": {"$cond": [{"$eq": ["$estado", "pendiente"]}, 1, 0]}
                }
            }
        },
        {"$sort": {"cantidad": -1}}
    ]
    
    cursor = db.intervenciones.aggregate(pipeline)
    resultados = [
        {
            "tipo": r["_id"],
            "cantidad": r["cantidad"],
            "completadas": r["completadas"],
            "pendientes": r["pendientes"]
        }
        async for r in cursor
    ]
    
    return {
        "periodo": {
            "desde": fecha_desde,
            "hasta": fecha_hasta
        },
        "resultados": resultados
    }


@router.get("/talleres/asistencia")
async def get_talleres_asistencia(
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Reporte de asistencia a talleres
    """
    db = get_db()
    
    query = {}
    if fecha_desde or fecha_hasta:
        query["fecha"] = {}
        if fecha_desde:
            query["fecha"]["$gte"] = fecha_desde
        if fecha_hasta:
            query["fecha"]["$lte"] = fecha_hasta
    
    talleres = await db.talleres.find(query).to_list(1000)
    
    reporte = []
    for t in talleres:
        participantes = t.get("participantes", [])
        asistentes = sum(1 for p in participantes if p.get("asistencia", False))
        
        reporte.append({
            "id": str(t["_id"]),
            "nombre": t["nombre"],
            "fecha": t["fecha"],
            "capacidad": t.get("capacidad_maxima", 20),
            "inscritos": len(participantes),
            "asistentes": asistentes,
            "tasa_asistencia": round(asistentes / len(participantes) * 100, 2) if participantes else 0
        })
    
    return {
        "periodo": {
            "desde": fecha_desde,
            "hasta": fecha_hasta
        },
        "total_talleres": len(talleres),
        "reporte": sorted(reporte, key=lambda x: x["fecha"], reverse=True)
    }


@router.get("/actividad/reciente")
async def get_actividad_reciente(
    limit: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Obtener actividad reciente del sistema
    """
    db = get_db()
    
    # Intervenciones recientes
    intervenciones = await db.intervenciones.find().sort("creado_en", -1).limit(limit).to_list(limit)
    
    # NNA recientes
    nna_recientes = await db.nna.find().sort("creado_en", -1).limit(limit).to_list(limit)
    
    # Talleres recientes
    talleres = await db.talleres.find().sort("creado_en", -1).limit(limit).to_list(limit)
    
    actividad = []
    
    for i in intervenciones:
        actividad.append({
            "tipo": "intervencion",
            "fecha": i.get("creado_en"),
            "descripcion": f"Nueva intervención: {i['motivo'][:50]}...",
            "entidad_id": str(i["_id"]),
            "nna_id": i["nna_id"]
        })
    
    for n in nna_recientes:
        actividad.append({
            "tipo": "nna",
            "fecha": n.get("creado_en"),
            "descripcion": f"NNA registrado: {n['nombre']} {n['apellido']}",
            "entidad_id": str(n["_id"])
        })
    
    for t in talleres:
        actividad.append({
            "tipo": "taller",
            "fecha": t.get("creado_en"),
            "descripcion": f"Taller creado: {t['nombre']}",
            "entidad_id": str(t["_id"])
        })
    
    # Ordenar por fecha
    actividad.sort(key=lambda x: x["fecha"] or datetime.min, reverse=True)
    
    return {"actividad": actividad[:limit]}
