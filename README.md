# Residencia NNA v2.0

Sistema de Gestión para Residencias de Niños, Niñas y Adolescentes

## Características

- **Autenticación JWT segura** con tokens de acceso y refresh
- **Control de roles** (Admin, Coordinador, Técnico, Viewer)
- **Gestión completa de NNA** con historial
- **Intervenciones** con seguimiento y prioridades
- **Talleres** con gestión de participantes
- **Seguimientos** multidisciplinarios
- **Reportes y estadísticas** en tiempo real
- **Dashboard** con gráficos interactivos

## Tecnologías

### Backend
- FastAPI 0.109.0
- MongoDB Atlas con Motor
- PyJWT para autenticación
- Pydantic para validación
- Passlib para hashing de contraseñas

### Frontend
- React 18 + TypeScript
- Vite para build
- Tailwind CSS
- Zustand para state management
- Recharts para gráficos
- React Router DOM

## Estructura del Proyecto

```
residencia-nna-v2/
├── backend/
│   ├── app/
│   │   ├── main.py              # Punto de entrada
│   │   ├── config.py            # Configuración
│   │   ├── database.py          # MongoDB
│   │   ├── models/              # Pydantic models
│   │   ├── routers/             # API endpoints
│   │   ├── middleware/          # Auth & RBAC
│   │   └── utils/               # Seguridad & validadores
│   ├── requirements.txt
│   └── railway.toml
├── frontend/
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── pages/               # Páginas
│   │   ├── hooks/               # Custom hooks
│   │   ├── services/            # API services
│   │   ├── store/               # Zustand stores
│   │   └── types/               # TypeScript types
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Despliegue en Railway

### 1. Preparar Backend

```bash
cd backend
```

### 2. Crear proyecto en Railway

1. Ir a [railway.com](https://railway.com)
2. Crear nuevo proyecto
3. Seleccionar "Deploy from GitHub repo"
4. Conectar tu repositorio

### 3. Configurar Variables de Entorno

En Railway, agregar las siguientes variables:

```env
MONGO_URL=mongodb+srv://usuario:password@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=residencia_nna
SECRET_KEY=TuClaveSecretaMuySegura123!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ADMIN_EMAIL=admin@residencia.cl
ADMIN_PASSWORD=TuPasswordSeguro123!
ADMIN_NOMBRE=Administrador del Sistema
```

### 4. Configurar MongoDB Atlas

1. Crear cluster en [MongoDB Atlas](https://cloud.mongodb.com)
2. Crear usuario de base de datos
3. Agregar IP de Railway a whitelist (0.0.0.0/0 para permitir todas)
4. Copiar connection string

### 5. Deploy Backend

Railway detectará automáticamente el `railway.toml` y hará deploy.

### 6. Verificar Deploy

```bash
curl https://tu-app.up.railway.app/health
```

Debería responder:
```json
{"status": "ok", "version": "2.0.0"}
```

### 7. Crear Usuario Admin

```bash
curl https://tu-app.up.railway.app/setup
```

### 8. Deploy Frontend

Opción A: Netlify/Vercel (Recomendado)

1. Conectar repositorio a Netlify o Vercel
2. Configurar build command: `npm run build`
3. Configurar output directory: `dist`
4. Agregar variable de entorno:
   ```
   VITE_API_URL=https://tu-backend.up.railway.app
   ```

Opción B: Railway (Servir desde backend)

Modificar `main.py` para servir el frontend build:

```python
from fastapi.staticfiles import StaticFiles

# Al final, antes de if __name__
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```

## Credenciales por Defecto

```
Email: admin@residencia.cl
Password: (la configurada en ADMIN_PASSWORD)
```

**IMPORTANTE:** Cambiar la contraseña en el primer inicio de sesión.

## Desarrollo Local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Crear .env con las variables
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Crear .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
```

## API Endpoints

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/refresh` - Refrescar token
- `GET /api/auth/me` - Obtener usuario actual
- `POST /api/auth/logout` - Cerrar sesión

### Usuarios (Admin)
- `GET /api/usuarios` - Listar usuarios
- `POST /api/usuarios` - Crear usuario
- `PUT /api/usuarios/{id}` - Actualizar usuario
- `DELETE /api/usuarios/{id}` - Eliminar usuario

### NNA
- `GET /api/nna` - Listar NNA
- `POST /api/nna` - Crear NNA
- `GET /api/nna/{id}` - Obtener NNA
- `PUT /api/nna/{id}` - Actualizar NNA
- `DELETE /api/nna/{id}` - Eliminar NNA

### Intervenciones
- `GET /api/intervenciones` - Listar intervenciones
- `POST /api/intervenciones` - Crear intervención
- `PUT /api/intervenciones/{id}` - Actualizar
- `DELETE /api/intervenciones/{id}` - Eliminar

### Talleres
- `GET /api/talleres` - Listar talleres
- `POST /api/talleres` - Crear taller
- `POST /api/talleres/{id}/participantes` - Agregar participante

### Reportes
- `GET /api/reportes/dashboard` - Estadísticas dashboard
- `GET /api/reportes/nna/detalle/{id}` - Reporte de NNA

## Roles y Permisos

| Rol | Permisos |
|-----|----------|
| Admin | Acceso total |
| Coordinador | CRUD todo, no gestión de usuarios |
| Técnico | Crear/editar sus registros |
| Viewer | Solo lectura |

## Seguridad

- Contraseñas hasheadas con bcrypt
- Tokens JWT con expiración
- Refresh tokens para sesiones largas
- CORS configurado
- Validación de inputs con Pydantic
- Rate limiting (configurable)

## Soporte

Para reportar problemas o solicitar funciones, contactar al administrador del sistema.

## Licencia

Sistema privado para uso interno de residencias NNA.
