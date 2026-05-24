# Popolilo Auth API

Sistema de autenticación con **JWT**, **DDD** y **Clean Architecture** implementado en Python con FastAPI.

## Descripción

API REST que implementa:
- ✅ Registro de usuarios con validación de email y password
- ✅ Login con generación de JWT tokens
- ✅ Endpoint protegido `/me` para obtener datos del usuario autenticado
- ✅ Thread-safe con PostgreSQL ACID + SQLAlchemy pool
- ✅ Patrones de diseño: Value Objects, Repository, Factory, Strategy
- ✅ Separación de capas: Domain, Application, Infrastructure, Presentation

## Requisitos

- **Python**: 3.10+
- **PostgreSQL**: 12+
- **pip**: Gestor de paquetes Python

## Setup PostgreSQL

```bash
# Crear base de datos
createdb popolilo_db

# O si usas psql:
psql -U postgres
CREATE DATABASE popolilo_db;
```

## Instalación

1. **Clonar repositorio**
   ```bash
   git clone <repo-url>
   cd Popolilo
   ```

2. **Crear virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # o: venv\Scripts\activate  # Windows
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus valores:
   # - DATABASE_URL: Ajustar user/password/host
   # - JWT_SECRET_KEY: Generar una clave segura (mínimo 32 caracteres)
   ```

## Ejecución

```bash
# Opción 1: Directo
python src/main.py

# Opción 2: Uvicorn
uvicorn src.presentation.main:app --reload

# La API está disponible en: http://localhost:8000
# Documentación interactiva: http://localhost:8000/docs (Swagger UI)
# ReDoc: http://localhost:8000/redoc
```

## Ejemplos de Uso

### 1. Registrar usuario

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'

# Respuesta (201 Created):
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'

# Respuesta (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Obtener datos del usuario (protegido)

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Respuesta (200 OK):
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Estructura del Proyecto

```
Popolilo/
├── src/
│   ├── domain/                 # Capa de Dominio (DDD)
│   │   ├── entities/           # Entidades de negocio
│   │   │   └── user.py
│   │   ├── value_objects/      # Value Objects (Email, Password)
│   │   │   ├── email.py
│   │   │   └── password.py
│   │   ├── interfaces/         # Contratos (Repository)
│   │   │   └── i_user_repository.py
│   │   └── exceptions.py       # Excepciones de dominio
│   │
│   ├── application/            # Capa de Aplicación
│   │   └── auth/
│   │       ├── auth_service.py # Casos de uso
│   │       └── jwt_service.py  # JWT
│   │
│   ├── infrastructure/         # Capa de Infraestructura
│   │   ├── config.py           # Configuración
│   │   └── persistence/
│   │       ├── database.py     # SQLAlchemy setup
│   │       ├── models.py       # ORM Models
│   │       └── user_repository.py  # Implementación
│   │
│   └── presentation/           # Capa de Presentación
│       ├── main.py             # FastAPI app
│       ├── routers/
│       │   └── auth.py         # Endpoints
│       ├── schemas/
│       │   └── auth_schemas.py # DTOs/Pydantic
│       └── dependencies/
│           └── auth.py         # Middleware
│
├── .env                        # Variables de entorno
├── .env.example                # Template
├── requirements.txt            # Dependencias
└── README.md                   # Este archivo
```

## Patrones de Diseño

| Patrón | Ubicación | Propósito |
|--------|-----------|----------|
| **Value Object** | `domain/value_objects/` | Email, Password (inmutables, auto-validación) |
| **Entity** | `domain/entities/` | User (con Factory Method) |
| **Repository** | `domain/interfaces/` + `infrastructure/` | Persistencia abstracta |
| **Strategy** | `domain/value_objects/password.py` | Hashing (bcrypt, extensible) |
| **Service** | `application/auth/` | Use cases stateless |
| **Dependency Injection** | `presentation/` | FastAPI con DI |

## Thread-Safety

| Componente | Estrategia |
|-----------|-----------|
| PostgreSQL | ACID + UNIQUE constraint |
| SQLAlchemy | Session pool (NullPool dev, QueuePool prod) |
| JWTService | Stateless → inherentemente thread-safe |
| FastAPI | Dependency per request → aislamiento automático |

## Configuración Avanzada

### JWT Secret Key

Generar clave segura (mínimo 32 caracteres):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database Pool (Producción)

Editar `src/infrastructure/persistence/database.py`:

```python
# Cambiar de NullPool a QueuePool
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

## Testing (Futuro)

```bash
pytest tests/
pytest --cov=src tests/  # Con coverage
```

**Nota**: Testing no incluido en esta iteración (foco en arquitectura).

## Notas de Seguridad

- ⚠️ **NUNCA** commitear `.env` con secretos reales
- ⚠️ JWT_SECRET_KEY debe ser mínimo 32 caracteres
- ⚠️ En producción usar HTTPS obligatoriamente
- ⚠️ Implementar rate limiting en endpoints

## Troubleshooting

### Error: `database "popolilo_db" does not exist`
```bash
createdb popolilo_db
```

### Error: `connection refused` en PostgreSQL
Verificar que PostgreSQL está corriendo:
```bash
psql -l  # Listar bases de datos
```

### Error: `JWT_SECRET_KEY` debe tener mínimo 32 caracteres
Editar `.env` y reemplazar valor de `JWT_SECRET_KEY`

## Contribución

1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/new-feature`)
3. Commit cambios (`git commit -am 'Add new feature'`)
4. Push a la rama (`git push origin feature/new-feature`)
5. Abrir Pull Request

## Licencia

MIT License
