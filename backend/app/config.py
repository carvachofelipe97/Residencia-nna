"""
Configuración centralizada del sistema
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # App
    APP_NAME: str = "Residencia NNA API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Database
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "residencia_nna"
    
    # Security
    SECRET_KEY: str = "tu-clave-secreta-cambiar-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Admin User
    ADMIN_EMAIL: str = "admin@residencia.cl"
    ADMIN_PASSWORD: str = "AdminNNA2025!"
    ADMIN_NOMBRE: str = "Administrador del Sistema"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Obtener configuración cacheada"""
    return Settings()


settings = get_settings()
