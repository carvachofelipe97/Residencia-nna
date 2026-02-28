"""
Middleware de Control de Acceso Basado en Roles (RBAC)
"""
from fastapi import Depends, HTTPException, status
from typing import List, Callable
from functools import wraps
from app.middleware.auth import get_current_active_user
from app.models.user import TokenData


# Jerarquía de roles (mayor número = más permisos)
ROLE_HIERARCHY = {
    "viewer": 1,      # Solo lectura
    "tecnico": 2,     # Lectura + crear/editar sus registros
    "coordinador": 3, # Lectura + crear/editar todo + reportes
    "admin": 4,       # Acceso total
}


class RoleChecker:
    """Verificador de roles"""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: TokenData = Depends(get_current_active_user)) -> TokenData:
        if user.rol not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{user.rol}' no tiene permisos para esta operación"
            )
        return user


def require_role(*roles: str) -> Callable:
    """Decorador para requerir roles específicos"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener usuario de los kwargs o dependencias
            current_user = kwargs.get("current_user")
            
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no autenticado"
                )
            
            if current_user.rol not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Se requiere uno de los roles: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def has_permission(user_role: str, required_role: str) -> bool:
    """
    Verificar si un rol tiene permisos suficientes
    Basado en jerarquía de roles
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def can_edit_any_record(user_role: str) -> bool:
    """Verificar si el rol puede editar cualquier registro"""
    return user_role in ["admin", "coordinador"]


def can_delete_records(user_role: str) -> bool:
    """Verificar si el rol puede eliminar registros"""
    return user_role == "admin"


def can_manage_users(user_role: str) -> bool:
    """Verificar si el rol puede gestionar usuarios"""
    return user_role == "admin"


def can_generate_reports(user_role: str) -> bool:
    """Verificar si el rol puede generar reportes"""
    return user_role in ["admin", "coordinador"]


# Instancias predefinidas para uso común
require_admin = RoleChecker(["admin"])
require_coordinador = RoleChecker(["admin", "coordinador"])
require_tecnico = RoleChecker(["admin", "coordinador", "tecnico"])
require_any_user = RoleChecker(["admin", "coordinador", "tecnico", "viewer"])
