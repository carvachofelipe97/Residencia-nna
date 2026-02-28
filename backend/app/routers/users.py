"""
Router de Usuarios - Gestión de usuarios del sistema
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_db
from app.models.user import UserCreate, UserUpdate, UserResponse, TokenData
from app.utils.security import hash_password
from app.middleware.auth import get_current_active_user
from app.middleware.rbac import require_admin, require_coordinador
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    rol: Optional[str] = None,
    activo: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Listar usuarios del sistema (Admin y Coordinador)
    """
    db = get_db()
    
    # Construir query
    query = {}
    if rol:
        query["rol"] = rol
    if activo is not None:
        query["activo"] = activo
    if search:
        query["$or"] = [
            {"nombre": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    # Ejecutar consulta
    cursor = db.usuarios.find(query).skip(skip).limit(limit).sort("creado_en", -1)
    users = await cursor.to_list(length=limit)
    
    return [
        UserResponse(
            id=str(u["_id"]),
            email=u["email"],
            nombre=u["nombre"],
            rol=u["rol"],
            activo=u.get("activo", True),
            ultimo_acceso=u.get("ultimo_acceso"),
            creado_en=u.get("creado_en", datetime.now(timezone.utc))
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(require_coordinador)
):
    """
    Obtener un usuario por ID
    """
    db = get_db()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    user = await db.usuarios.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        nombre=user["nombre"],
        rol=user["rol"],
        activo=user.get("activo", True),
        ultimo_acceso=user.get("ultimo_acceso"),
        creado_en=user.get("creado_en", datetime.now(timezone.utc))
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: TokenData = Depends(require_admin)
):
    """
    Crear nuevo usuario (Solo Admin)
    """
    db = get_db()
    
    # Verificar si el email ya existe
    existing = await db.usuarios.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este email"
        )
    
    # Crear usuario
    new_user = {
        "email": user_data.email,
        "nombre": user_data.nombre,
        "rol": user_data.rol,
        "activo": user_data.activo,
        "password_hash": hash_password(user_data.password),
        "creado_en": datetime.now(timezone.utc),
        "ultimo_acceso": None
    }
    
    result = await db.usuarios.insert_one(new_user)
    
    logger.info(f"Usuario creado: {user_data.email} por {current_user.email}")
    
    return UserResponse(
        id=str(result.inserted_id),
        email=new_user["email"],
        nombre=new_user["nombre"],
        rol=new_user["rol"],
        activo=new_user["activo"],
        ultimo_acceso=None,
        creado_en=new_user["creado_en"]
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: TokenData = Depends(require_admin)
):
    """
    Actualizar usuario (Solo Admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    # Verificar que el usuario existe
    existing = await db.usuarios.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # No permitir editar el usuario admin principal
    if existing["email"] == "admin@residencia.cl" and current_user.email != "admin@residencia.cl":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede editar el usuario administrador principal"
        )
    
    # Construir update
    update_data = {"actualizado_en": datetime.now(timezone.utc)}
    
    if user_data.nombre is not None:
        update_data["nombre"] = user_data.nombre
    if user_data.rol is not None:
        update_data["rol"] = user_data.rol
    if user_data.activo is not None:
        update_data["activo"] = user_data.activo
    if user_data.password is not None:
        update_data["password_hash"] = hash_password(user_data.password)
    
    await db.usuarios.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Obtener usuario actualizado
    updated = await db.usuarios.find_one({"_id": ObjectId(user_id)})
    
    logger.info(f"Usuario actualizado: {updated['email']} por {current_user.email}")
    
    return UserResponse(
        id=str(updated["_id"]),
        email=updated["email"],
        nombre=updated["nombre"],
        rol=updated["rol"],
        activo=updated.get("activo", True),
        ultimo_acceso=updated.get("ultimo_acceso"),
        creado_en=updated.get("creado_en", datetime.now(timezone.utc))
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(require_admin)
):
    """
    Eliminar usuario (Solo Admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    # Verificar que el usuario existe
    existing = await db.usuarios.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # No permitir eliminar el usuario admin principal
    if existing["email"] == "admin@residencia.cl":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se puede eliminar el usuario administrador principal"
        )
    
    # No permitir auto-eliminación
    if str(existing["_id"]) == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede eliminar su propio usuario"
        )
    
    await db.usuarios.delete_one({"_id": ObjectId(user_id)})
    
    logger.info(f"Usuario eliminado: {existing['email']} por {current_user.email}")
    
    return {"message": "Usuario eliminado correctamente"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    new_password: str,
    current_user: TokenData = Depends(require_admin)
):
    """
    Resetear contraseña de un usuario (Solo Admin)
    """
    db = get_db()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 8 caracteres"
        )
    
    user = await db.usuarios.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    await db.usuarios.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "actualizado_en": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"Contraseña reseteada para: {user['email']} por {current_user.email}")
    
    return {"message": "Contraseña reseteada correctamente"}
