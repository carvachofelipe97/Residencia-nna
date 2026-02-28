"""
Modelos de Usuario
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Clase para manejar ObjectId de MongoDB en Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


# Roles disponibles
UserRole = Literal["admin", "tecnico", "coordinador", "viewer"]


class UserBase(BaseModel):
    """Base del modelo de usuario"""
    email: EmailStr
    nombre: str = Field(..., min_length=2, max_length=100)
    rol: UserRole = "tecnico"
    activo: bool = True


class UserCreate(UserBase):
    """Modelo para crear usuario"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Modelo para actualizar usuario"""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    rol: Optional[UserRole] = None
    activo: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserInDB(UserBase):
    """Modelo de usuario en base de datos"""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    password_hash: str
    ultimo_acceso: Optional[datetime] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class UserResponse(UserBase):
    """Modelo de respuesta de usuario (sin datos sensibles)"""
    id: str
    ultimo_acceso: Optional[datetime] = None
    creado_en: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Modelo para login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Modelo de token JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Datos extraídos del token"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None


class User(UserBase):
    """Modelo completo de usuario"""
    id: str
    ultimo_acceso: Optional[datetime] = None
    creado_en: datetime
    actualizado_en: Optional[datetime] = None
