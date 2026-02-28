"""
Conexión y gestión de MongoDB
"""
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cliente y base de datos
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


async def connect_db() -> AsyncIOMotorDatabase:
    """Conectar a MongoDB Atlas"""
    global client, db
    
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.MONGO_URL,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            tls=True,
            tlsAllowInvalidCertificates=False,
            maxPoolSize=50,
            minPoolSize=10,
        )
        
        # Verificar conexión
        await client.admin.command('ping')
        db = client[settings.DB_NAME]
        
        logger.info(f"✅ Conectado a MongoDB: {settings.DB_NAME}")
        
        # Crear índices
        await create_indexes()
        
        return db
        
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        raise


async def create_indexes():
    """Crear índices para optimizar consultas"""
    try:
        # Índices de usuarios
        await db.usuarios.create_index("email", unique=True)
        await db.usuarios.create_index("rol")
        await db.usuarios.create_index("activo")
        
        # Índices de NNA
        await db.nna.create_index("rut", unique=True, sparse=True)
        await db.nna.create_index("nombre")
        await db.nna.create_index("estado")
        await db.nna.create_index("fecha_ingreso")
        
        # Índices de intervenciones
        await db.intervenciones.create_index("nna_id")
        await db.intervenciones.create_index("fecha")
        await db.intervenciones.create_index("tipo")
        
        # Índices de talleres
        await db.talleres.create_index("nombre")
        await db.talleres.create_index("fecha")
        await db.talleres.create_index("participantes.nna_id")
        
        # Índices de seguimiento
        await db.seguimiento.create_index("nna_id")
        await db.seguimiento.create_index("fecha")
        
        # Índices de notificaciones
        await db.notificaciones.create_index("usuario_id")
        await db.notificaciones.create_index("leida")
        await db.notificaciones.create_index("fecha_creacion")
        
        # Índices de alertas
        await db.alertas.create_index("nna_id")
        await db.alertas.create_index("tipo")
        await db.alertas.create_index("prioridad")
        await db.alertas.create_index("estado")
        await db.alertas.create_index("fecha_vencimiento")
        await db.alertas.create_index("asignado_a")
        await db.alertas.create_index("creado_en")
        
        # Índices de red de apoyo
        await db.red_apoyo.create_index("nna_id")
        await db.red_apoyo.create_index("tipo_vinculo")
        await db.red_apoyo.create_index("es_cuidador_temporal")
        await db.red_apoyo.create_index("es_ppf")
        await db.red_apoyo.create_index("es_contacto_emergencia")
        await db.red_apoyo.create_index("nivel_confiabilidad")
        await db.red_apoyo.create_index("estado")
        await db.red_apoyo.create_index("nombre")
        
        # Índices de planificación
        await db.planificacion.create_index("nna_id")
        await db.planificacion.create_index("tipo")
        await db.planificacion.create_index("categoria")
        await db.planificacion.create_index("estado")
        await db.planificacion.create_index("fecha_inicio")
        await db.planificacion.create_index("responsable_id")
        await db.planificacion.create_index("anio")
        
        # Índices de medidas judiciales
        await db.medidas_judiciales.create_index("nna_id")
        await db.medidas_judiciales.create_index("estado")
        await db.medidas_judiciales.create_index("tipo_solicitud")
        await db.medidas_judiciales.create_index("tipo_medida")
        await db.medidas_judiciales.create_index("fecha_termino")
        await db.medidas_judiciales.create_index("fecha_solicitud")
        
        # Índices de restricciones
        await db.restricciones.create_index("nna_id")
        await db.restricciones.create_index("medida_id")
        await db.restricciones.create_index("estado")
        await db.restricciones.create_index("tipo")
        
        logger.info("✅ Índices creados correctamente")
        
    except Exception as e:
        logger.warning(f"⚠️ Algunos índices ya existen: {e}")


async def close_db():
    """Cerrar conexión a MongoDB"""
    global client
    if client:
        client.close()
        logger.info("🔌 Conexión a MongoDB cerrada")


def get_db() -> AsyncIOMotorDatabase:
    """Obtener instancia de la base de datos"""
    if db is None:
        raise Exception("Base de datos no conectada. Llama a connect_db() primero.")
    return db


async def init_admin_user():
    """Inicializar usuario administrador si no existe"""
    from app.utils.security import hash_password
    
    try:
        existing = await db.usuarios.find_one({"email": settings.ADMIN_EMAIL})
        
        if not existing:
            admin_user = {
                "email": settings.ADMIN_EMAIL,
                "nombre": settings.ADMIN_NOMBRE,
                "rol": "admin",
                "password_hash": hash_password(settings.ADMIN_PASSWORD),
                "activo": True,
                "ultimo_acceso": None,
                "creado_en": datetime.now(timezone.utc),
            }
            
            result = await db.usuarios.insert_one(admin_user)
            logger.info(f"✅ Usuario admin creado: {settings.ADMIN_EMAIL}")
        else:
            logger.info(f"ℹ️ Usuario admin ya existe: {settings.ADMIN_EMAIL}")
            
    except Exception as e:
        logger.error(f"❌ Error creando usuario admin: {e}")
