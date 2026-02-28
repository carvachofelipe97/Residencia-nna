"""
Router de Autenticación
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import UserLogin, Token, TokenData, UserResponse
from app.utils.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.middleware.auth import get_current_active_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Autenticación"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Iniciar sesión y obtener tokens JWT
    """
    db = get_db()
    
    # Buscar usuario por email
    user = await db.usuarios.find_one({"email": credentials.email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar si el usuario está activo
    if not user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado. Contacte al administrador."
        )
    
    # Verificar contraseña
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Actualizar último acceso
    await db.usuarios.update_one(
        {"_id": user["_id"]},
        {"$set": {"ultimo_acceso": datetime.now(timezone.utc)}}
    )
    
    # Crear tokens
    token_data = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "rol": user["rol"],
        "nombre": user["nombre"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info(f"Usuario {user['email']} inició sesión")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutos en segundos
        user=UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            nombre=user["nombre"],
            rol=user["rol"],
            activo=user.get("activo", True),
            ultimo_acceso=datetime.now(timezone.utc),
            creado_en=user.get("creado_en", datetime.now(timezone.utc))
        )
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: str):
    """
    Refrescar token de acceso usando refresh token
    """
    payload = decode_token(refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que sea un refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear nuevo access token
    token_data = {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "rol": payload.get("rol"),
        "nombre": payload.get("nombre")
    }
    
    new_access_token = create_access_token(token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: TokenData = Depends(get_current_active_user)):
    """
    Obtener información del usuario actual
    """
    db = get_db()
    user = await db.usuarios.find_one({"_id": current_user.user_id})
    
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


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_active_user)):
    """
    Cerrar sesión (invalidar token en cliente)
    """
    logger.info(f"Usuario {current_user.email} cerró sesión")
    return {"message": "Sesión cerrada correctamente"}


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Cambiar contraseña del usuario actual
    """
    from app.utils.security import hash_password, verify_password
    
    db = get_db()
    user = await db.usuarios.find_one({"_id": current_user.user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar contraseña actual
    if not verify_password(current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Validar nueva contraseña
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 8 caracteres"
        )
    
    # Actualizar contraseña
    await db.usuarios.update_one(
        {"_id": current_user.user_id},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "actualizado_en": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"Usuario {current_user.email} cambió su contraseña")
    
    return {"message": "Contraseña cambiada correctamente"}
