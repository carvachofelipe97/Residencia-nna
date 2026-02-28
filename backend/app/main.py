"""
Residencia NNA - API v2.0
Sistema de Gestión para Residencias de Niños, Niñas y Adolescentes
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import connect_db, close_db, init_admin_user
from app.routers import auth, users, nna, intervenciones, talleres, seguimiento, reportes, alertas, red_apoyo, planificacion, juridico

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    """
    # Startup
    logger.info("🚀 Iniciando Residencia NNA API v2.0")
    
    try:
        await connect_db()
        await init_admin_user()
        logger.info("✅ Aplicación lista")
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando aplicación")
    await close_db()
    logger.info("✅ Aplicación cerrada correctamente")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de Gestión para Residencias de Niños, Niñas y Adolescentes",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ALLOWED_ORIGINS == "*" else settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }


# Información del sistema
@app.get("/", tags=["Root"])
async def root():
    """Información básica del API"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# Setup inicial (crear admin)
@app.get("/setup", tags=["Setup"])
async def setup():
    """
    Endpoint de configuración inicial
    Crea el usuario administrador si no existe
    """
    try:
        await init_admin_user()
        return {
            "status": "ok",
            "message": "Configuración inicial completada",
            "admin_email": settings.ADMIN_EMAIL
        }
    except Exception as e:
        logger.error(f"Error en setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en configuración inicial: {str(e)}"
        )


# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(users.router, prefix="/api", tags=["Usuarios"])
app.include_router(nna.router, prefix="/api", tags=["NNA"])
app.include_router(intervenciones.router, prefix="/api", tags=["Intervenciones"])
app.include_router(talleres.router, prefix="/api", tags=["Talleres"])
app.include_router(seguimiento.router, prefix="/api", tags=["Seguimiento"])
app.include_router(reportes.router, prefix="/api", tags=["Reportes"])
app.include_router(alertas.router, prefix="/api", tags=["Alertas"])
app.include_router(red_apoyo.router, prefix="/api", tags=["Red de Apoyo"])
app.include_router(planificacion.router, prefix="/api", tags=["Planificación Anual"])
app.include_router(juridico.router, prefix="/api", tags=["Módulo Jurídico"])


# Manejadores de excepciones globales
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador de excepciones global"""
    logger.error(f"Error no manejado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"}
    )


# Importar datetime para el health check
from datetime import datetime


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
