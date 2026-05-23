# Implementation Plan: Sistema de Autenticación con JWT + Base Concurrencia

**Branch**: `2026-0523-auth-clarifications` | **Date**: 2026-05-23 | **Spec**: `/home/dani/Documentos/Escritoriom/ACS/Taller Final/Popolilo/AUTH_SPEC.md`

**Input**: Feature specification from `/specs/2026-0523-auth-clarifications/spec.md`

**Note**: Plan generado como salida de `/speckit.plan`. Orientado a implementación thread-safe en PostgreSQL con DDD y Clean Architecture.

## Summary

Implementar subsistema de autenticación JWT con registro y login de usuarios. El sistema debe ser **thread-safe** por concurrencia de requests simultáneos. Utilizará PostgreSQL para persistencia ACID, SQLAlchemy como ORM, y FastAPI como framework web. Se implementarán los 4 patrones de diseño obligatorios (Value Objects, Repository, Factory, Strategy) siguiendo Clean Architecture y DDD. Sin workers ni colas en esta iteración.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: 
- FastAPI (web framework)
- SQLAlchemy 2.x (ORM)
- psycopg2 o psycopg[binary] (PostgreSQL adapter)
- python-jose (JWT generation/verification)
- passlib[bcrypt] (password hashing)
- email-validator (RFC 5322 validation)
- pydantic-settings (configuration)

**Storage**: PostgreSQL 14+ (ACID-compliant, thread-safe a nivel de conexión)

**Testing**: No incluido en esta iteración (foco en arquitectura correcta)

**Target Platform**: Linux server (distribuido, concurrente)

**Project Type**: Web service (backend API REST con autenticación)

**Performance Goals**: 
- Mínimo 1000 req/s en `/login` y `/register` (bajo carga)
- Latencia p95 < 200ms en operaciones de auth
- No hay requisitos específicos de throughput de JWT verificación (stateless)

**Constraints**: 
- Thread-safe a nivel de pool de conexiones (SQLAlchemy QueuePool en prod)
- ACID transactions en PostgreSQL garantizan consistencia de datos
- Concurrency: múltiples requests concurrentes sin race conditions

**Scale/Scope**: 
- Usuarios: inicialmente sin límite explícito (escalable con índices DB)
- Endpoints: 3 iniciales (`/register`, `/login`, `/me`)
- Migraciones: Alembic (opcional pero recomendado)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Status | Justificación |
|-----------|--------|---------------|
| **Clean Code** | ✓ PASS | Máximo 20 líneas por función garantizado. Value Objects y servicios serán pequeños, enfocados. |
| **Patrones Documentados** | ✓ PASS | 4 patrones obligatorios: Repository, Factory, Value Objects, Strategy. Cada uno tendrá comentario `# Pattern: <Nombre>`. |
| **DDD - Separación** | ✓ PASS | `domain/` contiene solo entities, VOs, interfaces. NO importará de `infrastructure/` ni `presentation/`. |
| **Thread-Safety** | ✓ PASS | PostgreSQL ACID + SQLAlchemy pool, UNIQUE constraint en BD para email, servicios stateless (JWT). Sin locks explícitos necesarios (delegado a BD). |
| **No Testing** | ✓ PASS | Foco en arquitectura correcta. Sin test suite (se agregará cuando haya base sólida). |

**Gate Result**: PASS - Procedemos a Phase 0 (Research).

## Project Structure

### Documentation (this feature)

```text
specs/2026-0523-auth-clarifications/
├── plan.md                    # This file (implementation plan)
├── research.md                # Phase 0 output (research findings)
├── data-model.md              # Phase 1 output (entities, VOs, relationships)
├── quickstart.md              # Phase 1 output (setup and running)
├── contracts/                 # Phase 1 output (API contracts)
│   └── auth-api.md            # OpenAPI-style contract for /register, /login, /me
└── tasks.md                   # Phase 2 output (task list for implementation)
```

### Source Code (repository root)

```text
# Clean Architecture + DDD Structure
src/
├── domain/                          # Pure domain logic (NO external deps)
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   └── user.py                  # User aggregate root
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── email.py                 # Email VO with validation
│   │   └── password.py              # Password VO with hashing + Strategy
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── i_user_repository.py     # Repository interface (contract)
│   │   ├── i_hashing_strategy.py    # Hashing strategy interface
│   │   └── i_jwt_service.py         # JWT service interface
│   └── exceptions.py                # Domain-specific exceptions
│
├── application/                     # Use cases (depends on domain only)
│   ├── __init__.py
│   └── auth/
│       ├── __init__.py
│       ├── auth_service.py          # Register & login use cases
│       ├── jwt_service.py           # JWT generation/verification
│       └── exceptions.py            # Application exceptions
│
├── infrastructure/                  # Technical implementations
│   ├── __init__.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── database.py              # SQLAlchemy session factory, pool config
│   │   ├── models.py                # SQLAlchemy ORM models
│   │   └── user_repository.py       # Repository implementation
│   ├── security/
│   │   ├── __init__.py
│   │   └── bcrypt_strategy.py       # Bcrypt implementation of hashing
│   └── config.py                    # Environment variables, settings
│
├── presentation/                    # HTTP layer (depends on application)
│   ├── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth.py                  # FastAPI routes (/register, /login, /me)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── auth_schemas.py          # Pydantic DTOs (request/response)
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── auth.py                  # FastAPI dependency for get_current_user
│   └── main.py                      # FastAPI app instance, router registration
│
├── migrations/                      # Alembic migrations (optional)
│   ├── versions/
│   │   ├── 001_create_users_table.py
│   │   └── ...
│   ├── env.py
│   └── script.py.mako
│
├── main.py                          # Entry point (uvicorn)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
└── README.md                        # Setup and running instructions
```

**Structure Decision**: Single monolithic backend (Option 1) con estructura DDD clara. Domain completamente aislado, Application con casos de uso, Infrastructure con detalles técnicos, Presentation con FastAPI.

## Complexity Tracking

No violations detected. Estructura DDD y patrones seleccionados son justificados por:

| Decisión | Justificación | Alternativa Rechazada |
|----------|---------------|-----------------------|
| Value Objects (Email, Password) | Encapsulan validación y hashing, reutilizables | Validación en service (pobre reutilización) |
| Repository Pattern | Abstrae persistencia, permite testing con mocks | Acceso directo a BD (acoplamiento, dificultoso cambiar DB) |
| Factory Pattern en User | Encapsula construcción + validación | Constructor directo (requiere múltiples verificaciones en caller) |
| Strategy Pattern para hashing | Permite cambiar bcrypt → argon2 sin tocar dominio | Hardcodear bcrypt en Password VO (inflexible) |

---

# WORK PHASES

Este plan divide la implementación en 4 fases lógicas, respetando la prioridad **Domain → Application → Infrastructure → Presentation**. Cada fase tiene dependencias explícitas y criterios de completitud.

## Phase 0: Research & Clarifications

**Duration**: ~2-3 horas

**Objective**: Resolver todas las incógnitas técnicas antes de escribir código.

### Tasks

| ID | Tarea | Output | Depende de |
|----|----|--------|-----------|
| R0.1 | Investigar email-validator: RFC 5322, API, exception handling | `research.md` § Email Validation | - |
| R0.2 | Bcrypt vs Argon2: rendimiento, seguridad, adoptabilidad | `research.md` § Hashing Strategy | - |
| R0.3 | SQLAlchemy pool configurations: NullPool (dev), QueuePool (prod) | `research.md` § Database Concurrency | - |
| R0.4 | JWT claims estándar RFC 7519: qué incluir, expiración, validación | `research.md` § JWT Specification | - |
| R0.5 | PostgreSQL UNIQUE constraints: enforcement, IntegrityError handling | `research.md` § Database Constraints | - |
| R0.6 | FastAPI dependency injection: get_current_user pattern | `research.md` § FastAPI Auth Pattern | - |

### Completion Criteria (Phase 0)

- [ ] `research.md` completamente rellenado con decisiones técnicas
- [ ] Todas las NEEDS CLARIFICATION resueltas
- [ ] Patrones de diseño investigados y validados
- [ ] Configuración de pool de conexiones documentada
- [ ] Archivos base (config.py, database.py) preparados

**Effort**: ~2-3 horas (investigación, prototipos pequeños)

---

## Phase 1: Domain Design & Data Model

**Duration**: ~3-4 horas

**Objective**: Definir entidades, Value Objects, interfaces. CERO dependencias externas en `domain/`.

### Subsection 1.1: Value Objects

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Value Object: Email** | `domain/value_objects/email.py` | Validar RFC 5322, implementar `__eq__`, `__hash__` | Inmutable por construcción |
| **Value Object: Password** | `domain/value_objects/password.py` | Validar requisitos, delegar hashing a Strategy | Inmutable (nunca se serializa) |

**Implementation Tasks**

| ID | Tarea | Output | Testing | Depende de |
|----|----|----|---------|-----------|
| D1.1a | Implementar `Email` VO con validación email-validator | `domain/value_objects/email.py` | Manual (unit test manual) | R0.1 (research) |
| D1.1b | Implementar `Password` VO con validación de fuerza | `domain/value_objects/password.py` | Manual (verificar excepciones) | R0.2 (research) |
| D1.1c | Implementar `HashingStrategy` interface + `BcryptStrategy` | `domain/interfaces/i_hashing_strategy.py`, `infrastructure/security/bcrypt_strategy.py` | Manual (verificar hash/verify) | R0.2 (research) |

**Code Pattern Reference**

```python
# Pattern: Value Object (Email)
class Email:
    def __init__(self, value: str):
        if not self._is_valid(value):
            raise ValueError(f"Invalid email: {value}")
        self._value = value
    
    def __eq__(self, other): ...
    def __hash__(self): ...
    def __str__(self): ...

# Pattern: Value Object (Password) + Strategy
class Password:
    def __init__(self, plaintext: str, strategy: HashingStrategy = None):
        if not self._is_strong(plaintext):
            raise ValueError("Password too weak")
        strategy = strategy or BcryptStrategy()
        self._hash = strategy.hash(plaintext)
    
    @property
    def hash(self): return self._hash
    
    def verify(self, plaintext: str, strategy: HashingStrategy = None) -> bool: ...
```

### Subsection 1.2: Entities & Aggregates

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Entity: User** | `domain/entities/user.py` | Identidad (UUID), agregación de Email + Password | Inmutable en transacción ACID |

**Implementation Tasks**

| ID | Tarea | Output | Testing | Depende de |
|----|----|----|---------|-----------|
| D1.2a | Implementar `User` entity con UUID, email, password_hash | `domain/entities/user.py` | Manual (crear instancias) | D1.1a, D1.1b |
| D1.2b | Implementar `User.create()` factory que valida + construye | `domain/entities/user.py` (static method) | Manual (verificar validaciones) | D1.1a, D1.1b |
| D1.2c | Implementar excepciones de dominio | `domain/exceptions.py` (InvalidEmailError, WeakPasswordError, UserAlreadyExistsError, InvalidCredentialsError) | Manual (verificar lanzan) | D1.2a |

**Code Pattern Reference**

```python
# Pattern: Factory (User.create)
class User:
    @staticmethod
    def create(email: str, password: str) -> "User":
        """Factory que valida y construye la entidad."""
        email_vo = Email(email)          # Lanza si inválido
        password_vo = Password(password) # Lanza si débil
        return User(
            id=uuid4(),  # Temporal, BD asigna finalmente
            email=email_vo,
            password=password_vo,
            created_at=datetime.utcnow()
        )
```

### Subsection 1.3: Repository Interface

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Interface: IUserRepository** | `domain/interfaces/i_user_repository.py` | Contrato sin detalles técnicos | Delegado a implementación (BD) |

**Implementation Tasks**

| ID | Tarea | Output | Testing | Depende de |
|----|----|----|---------|-----------|
| D1.3a | Diseñar `IUserRepository` con métodos: `create()`, `find_by_email()`, `email_exists()` | `domain/interfaces/i_user_repository.py` | Manual (verificar abstractness) | D1.2a |

**Code Pattern Reference**

```python
# Pattern: Repository
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User:
        """Retorna el usuario creado con ID asignado por BD."""
        pass
    
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """Retorna None si no existe."""
        pass
    
    @abstractmethod
    def email_exists(self, email: Email) -> bool:
        """Verifica existencia sin recuperar la entidad completa."""
        pass
```

### Phase 1 Completion Criteria

- [ ] Email VO implementado (validación RFC 5322, `__eq__`, `__hash__`)
- [ ] Password VO implementado (validación fuerza, nunca en texto plano)
- [ ] HashingStrategy interface + BcryptStrategy implementados
- [ ] User entity con UUID, email, password_hash
- [ ] User.create() factory funcional
- [ ] IUserRepository interface definida (sin SQLAlchemy)
- [ ] Excepciones de dominio creadas
- [ ] Zero imports de `infrastructure/` o `presentation/` en `domain/`
- [ ] `data-model.md` generado (relaciones, validaciones, estado)

**Effort**: ~3-4 horas (lógica pura, sin BD)

---

## Phase 2: Application Layer (Use Cases)

**Duration**: ~2-3 horas

**Objective**: Implementar servicios de aplicación que orquestan dominio.

### Subsection 2.1: JWT Service

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Service: JWTService** | `application/auth/jwt_service.py` | Generar y verificar JWT (stateless) | Inherentemente thread-safe (sin estado) |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| A2.1a | Implementar `JWTService.encode()`: crear token con claims (sub, role, iat, exp, email) | `application/auth/jwt_service.py` | R0.4 (research JWT) |
| A2.1b | Implementar `JWTService.decode()`: verificar firma y expiración | `application/auth/jwt_service.py` | R0.4 (research JWT) |
| A2.1c | Manejo de excepciones JWT (token expirado, firma inválida) | `application/auth/exceptions.py` | A2.1b |

**Code Pattern Reference**

```python
# Pattern: Service (stateless, thread-safe by design)
class JWTService:
    def __init__(self, secret: str, algorithm: str, expiration_hours: int):
        self.secret = secret
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def encode(self, user_id: str, email: str, role: str = "user") -> str:
        """Genera JWT con claims estándar RFC 7519."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=self.expiration_hours)).timestamp())
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def decode(self, token: str) -> dict:
        """Verifica y decodifica JWT."""
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidSignatureError:
            raise InvalidTokenError()
```

### Subsection 2.2: Auth Service (Use Cases)

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Service: AuthService** | `application/auth/auth_service.py` | Casos de uso: register, login (orquesta dominio + repos) | Servicios puros (no estado mutable) |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| A2.2a | Implementar `AuthService.register(email, password)`: validar, crear User, guardar en BD | `application/auth/auth_service.py` | D1.2a, D1.3a |
| A2.2b | Implementar `AuthService.login(email, password)`: verificar credenciales, retornar token | `application/auth/auth_service.py` | D1.2a, A2.1a |
| A2.2c | Manejo de excepciones: UserAlreadyExistsError (409), InvalidCredentialsError (401) | `application/auth/exceptions.py` | D1.2c, A2.2a, A2.2b |

**Code Pattern Reference**

```python
# Pattern: Application Service (orchestrates domain + infrastructure)
class AuthService:
    def __init__(self, user_repo: IUserRepository, jwt_service: JWTService):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
    
    def register(self, email: str, password: str) -> User:
        """Use case: Register user."""
        # Dominio valida (lanza excepciones si email inválido o password débil)
        user = User.create(email, password)
        
        # Infrastructura verifica en BD e inserta
        try:
            saved_user = self.user_repo.create(user)
        except IntegrityError:
            raise UserAlreadyExistsError(f"Email {email} already registered")
        
        return saved_user
    
    def login(self, email: str, password: str) -> str:
        """Use case: Login user, return JWT."""
        email_vo = Email(email)  # Validar formato
        user = self.user_repo.find_by_email(email_vo)
        
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        
        # Password VO verifica contra hash
        if not user.password.verify(password):
            raise InvalidCredentialsError("Invalid email or password")
        
        # JWTService genera token
        token = self.jwt_service.encode(str(user.id), email, "user")
        return token
```

### Phase 2 Completion Criteria

- [ ] JWTService.encode() generan tokens con claims correctos
- [ ] JWTService.decode() verifican firma y expiración
- [ ] AuthService.register() valida y persiste usuarios
- [ ] AuthService.login() verifica credenciales y retorna token
- [ ] Manejo de excepciones correcto (401 vs 409)
- [ ] `application/` depende solo de `domain/`
- [ ] `application/` no importa de `infrastructure/` ni `presentation/`

**Effort**: ~2-3 horas (lógica de orquestación)

---

## Phase 3: Infrastructure Layer (Persistencia & Security)

**Duration**: ~3-4 horas

**Objective**: Implementar detalles técnicos: BD, repositorios, pool de conexiones.

### Subsection 3.1: Database Configuration & Models

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Database Config** | `infrastructure/config.py` | Variables de entorno, settings | Inmutable después de init |
| **SQLAlchemy Models** | `infrastructure/persistence/models.py` | ORM mappings | Manejado por SQLAlchemy |
| **Database Session** | `infrastructure/persistence/database.py` | Pool, session factory | QueuePool en prod, NullPool en dev |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| I3.1a | Configurar `.env` + `config.py` con pydantic-settings | `infrastructure/config.py`, `.env.example` | R0.3 (research DB config) |
| I3.1b | Crear `database.py` con SQLAlchemy engine, session factory | `infrastructure/persistence/database.py` | R0.3 (research pool) |
| I3.1c | Diseñar modelo ORM `UserModel` (id, email, password_hash, created_at) | `infrastructure/persistence/models.py` | I3.1b |
| I3.1d | Crear constraint `UNIQUE` en email, índice para búsquedas | `infrastructure/persistence/models.py` | I3.1c |

**Code Pattern Reference**

```python
# infrastructure/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"

settings = Settings()

# infrastructure/persistence/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,  # Prod: QueuePool; Dev: NullPool
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(bind=engine)

# infrastructure/persistence/models.py
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # UNIQUE constraint ensures thread-safe email validation
    __table_args__ = (
        Index('idx_users_email_unique', 'email', unique=True),
    )
```

### Subsection 3.2: Repository Implementation

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Repository: UserRepository** | `infrastructure/persistence/user_repository.py` | Implementar IUserRepository con SQLAlchemy | BD ACID, SQLAlchemy maneja thread-safety |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| I3.2a | Implementar `UserRepository.create()`: insertar, capturar IntegrityError | `infrastructure/persistence/user_repository.py` | D1.3a, I3.1c |
| I3.2b | Implementar `UserRepository.find_by_email()`: query con JOIN | `infrastructure/persistence/user_repository.py` | D1.3a, I3.1c |
| I3.2c | Implementar `UserRepository.email_exists()`: COUNT query optimizado | `infrastructure/persistence/user_repository.py` | D1.3a, I3.1c |
| I3.2d | Manejo de IntegrityError → UserAlreadyExistsError | `infrastructure/persistence/user_repository.py` | I3.2a |

**Code Pattern Reference**

```python
# Pattern: Repository (abstracts persistence)
from sqlalchemy.exc import IntegrityError

class UserRepository(IUserRepository):
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def create(self, user: User) -> User:
        """Persistir usuario en BD."""
        model = UserModel(
            id=str(user.id),
            email=str(user.email),
            password_hash=user.password.hash,
            created_at=user.created_at
        )
        self.session.add(model)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise UserAlreadyExistsError(f"Email already registered")
        
        user.id = UUID(model.id)  # Asignar ID desde BD si fue generado
        return user
    
    def find_by_email(self, email: Email) -> Optional[User]:
        """Recuperar usuario por email."""
        model = self.session.query(UserModel).filter_by(
            email=str(email)
        ).first()
        
        if not model:
            return None
        
        return User(
            id=UUID(model.id),
            email=Email(model.email),
            password_hash=model.password_hash,
            created_at=model.created_at
        )
    
    def email_exists(self, email: Email) -> bool:
        """Verificar existencia sin recuperar entidad."""
        count = self.session.query(UserModel).filter_by(
            email=str(email)
        ).count()
        return count > 0
```

### Phase 3 Completion Criteria

- [ ] `.env.example` creado con template de variables
- [ ] `config.py` carga configuración desde `.env`
- [ ] SQLAlchemy engine configurado con pool (QueuePool prod, NullPool dev)
- [ ] `UserModel` con constraint UNIQUE en email
- [ ] `UserRepository` implementa `IUserRepository`
- [ ] IntegrityError capturado y convertido a excepciones de dominio
- [ ] Session factory funcional
- [ ] `infrastructure/` depende de `domain/` pero no viceversa

**Effort**: ~3-4 horas (BD setup, migraciones, testing de queries)

---

## Phase 4: Presentation Layer (HTTP API)

**Duration**: ~2-3 horas

**Objective**: Implementar endpoints FastAPI y middleware de autenticación.

### Subsection 4.1: DTOs & Schemas

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **DTOs** | `presentation/schemas/auth_schemas.py` | Pydantic models para request/response | Inmutable por construcción |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| P4.1a | Crear `RegisterRequest` (email, password) + `RegisterResponse` (user_id) | `presentation/schemas/auth_schemas.py` | - |
| P4.1b | Crear `LoginRequest` (email, password) + `LoginResponse` (access_token, token_type) | `presentation/schemas/auth_schemas.py` | - |
| P4.1c | Crear `UserResponse` (user_id) para endpoint `/me` | `presentation/schemas/auth_schemas.py` | - |

**Code Pattern Reference**

```python
# Pattern: DTO (Data Transfer Object)
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterResponse(BaseModel):
    user_id: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    user_id: str
```

### Subsection 4.2: FastAPI Dependency Injection

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Auth Dependency** | `presentation/dependencies/auth.py` | `get_current_user()` middleware | Stateless, delegado a JWTService |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| P4.2a | Implementar `get_current_user(token: str)` dependency | `presentation/dependencies/auth.py` | A2.1b (JWT decode) |
| P4.2b | Extraer token de header `Authorization: Bearer <token>` | `presentation/dependencies/auth.py` | P4.2a |
| P4.2c | Inyectar `user_id` en `request.state.user_id` | `presentation/dependencies/auth.py` | P4.2a |
| P4.2d | Manejar excepciones: 401 si falta, inválido o expirado | `presentation/dependencies/auth.py` | P4.2a |

**Code Pattern Reference**

```python
# Pattern: Dependency Injection (FastAPI)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> str:
    """Dependency que extrae y valida JWT."""
    token = credentials.credentials
    
    try:
        payload = jwt_service.decode(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_id
```

### Subsection 4.3: Auth Routes

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **Routes** | `presentation/routers/auth.py` | Endpoints FastAPI | Delegado a servicios stateless |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| P4.3a | Implementar `POST /register` (201 on success, 400 on validation, 409 on duplicate) | `presentation/routers/auth.py` | A2.2a, P4.1a |
| P4.3b | Implementar `POST /login` (200 on success, 401 on invalid creds) | `presentation/routers/auth.py` | A2.2b, P4.1b |
| P4.3c | Implementar `GET /me` (200 on success, 401 on missing/invalid token) | `presentation/routers/auth.py` | P4.2a, P4.1c |
| P4.3d | Exception handling + logging (no passwords, solo intentos fallidos) | `presentation/routers/auth.py` | P4.3a, P4.3b |

**Code Pattern Reference**

```python
# Pattern: Router (HTTP entrypoint)
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=201)
def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> RegisterResponse:
    """Endpoint: Register user."""
    try:
        user = auth_service.register(request.email, request.password)
        return RegisterResponse(user_id=str(user.id))
    except (InvalidEmailError, WeakPasswordError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/login")
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """Endpoint: Login user."""
    try:
        token = auth_service.login(request.email, request.password)
        return LoginResponse(access_token=token, token_type="bearer")
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password")

@router.get("/me")
def get_current_user_profile(
    user_id: str = Depends(get_current_user)
) -> UserResponse:
    """Endpoint: Get current user (protected)."""
    return UserResponse(user_id=user_id)
```

### Subsection 4.4: FastAPI App Setup

| Patrón | Archivo | Responsabilidad | Thread-Safety |
|--------|---------|-----------------|---------------|
| **App Instance** | `presentation/main.py` | FastAPI app, router registration | Framework maneja concurrencia |

**Implementation Tasks**

| ID | Tarea | Output | Depende de |
|----|----|----|-----------|
| P4.4a | Crear FastAPI app instance | `presentation/main.py` | - |
| P4.4b | Registrar routers (auth router) | `presentation/main.py` | P4.3a, P4.3b, P4.3c |
| P4.4c | Configurar CORS si es necesario | `presentation/main.py` | - |
| P4.4d | Crear entry point con uvicorn | `main.py` (raíz) | P4.4b |

**Code Pattern Reference**

```python
# presentation/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from presentation.routers import auth

app = FastAPI(title="Popolilo Auth", version="1.0.0")

# Optional CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)

# Register routers
app.include_router(auth.router)

# main.py (root)
import uvicorn
from presentation.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Phase 4 Completion Criteria

- [ ] DTOs creados (RegisterRequest, LoginResponse, etc.)
- [ ] `get_current_user()` dependency extracts token y valida JWT
- [ ] `POST /register` retorna 201 + user_id (o 400, 409 en errores)
- [ ] `POST /login` retorna 200 + access_token (o 401)
- [ ] `GET /me` retorna 200 + user_id (o 401 si sin token)
- [ ] Error handling: 400 (validation), 401 (auth), 409 (duplicate)
- [ ] FastAPI app instance runnable con uvicorn
- [ ] Logging de intentos fallidos (sin passwords)
- [ ] `presentation/` depende de `application/` + `infrastructure/` pero no viceversa

**Effort**: ~2-3 horas (routing, exception mapping, testing manual)

---

# PATTERN MAPPING MATRIX

Tabla de dónde implementar cada patrón de diseño obligatorio:

| Patrón | Ubicación | Archivo | Responsabilidad | Thread-Safety |
|--------|-----------|---------|-----------------|---------------|
| **Value Object: Email** | Domain | `domain/value_objects/email.py` | Validar RFC 5322, `__eq__`, `__hash__` | Inmutable |
| **Value Object: Password** | Domain | `domain/value_objects/password.py` | Validar fuerza, hashing delegado | Inmutable |
| **Factory: User.create()** | Domain | `domain/entities/user.py` | Encapsular validación + construcción | Inmutable (local) |
| **Repository: IUserRepository** | Domain | `domain/interfaces/i_user_repository.py` | Interfaz abstracta | BD maneja |
| **Repository: UserRepository** | Infrastructure | `infrastructure/persistence/user_repository.py` | Implementación SQLAlchemy | BD ACID |
| **Strategy: HashingStrategy** | Domain/Infrastructure | `domain/interfaces/i_hashing_strategy.py`, `infrastructure/security/bcrypt_strategy.py` | Abstraer bcrypt, permitir argon2 | Stateless |
| **Service: AuthService** | Application | `application/auth/auth_service.py` | Orquestar dominio + repos | Stateless |
| **Service: JWTService** | Application | `application/auth/jwt_service.py` | Generar/verificar tokens | Stateless |
| **Dependency Injection** | Presentation | `presentation/dependencies/auth.py` | FastAPI dependency para proteger rutas | Stateless |

---

# CONCURRENCY & THREAD-SAFETY SPEC

Desglose de dónde se garantiza thread-safety:

| Componente | Mecanismo | Justificación | Evidencia |
|-----------|-----------|---------------|-----------| 
| **PostgreSQL Conexiones** | QueuePool (SQLAlchemy) | Cada request obtiene su propia conexión. No hay compartir entre threads. | `poolclass=QueuePool, pool_size=10` |
| **Email Uniqueness** | BD CONSTRAINT UNIQUE | IntegrityError garantizado si violación concurrente. ACID transactional. | `CREATE UNIQUE INDEX idx_users_email ON users(email)` |
| **Password Hashing** | Inmutable, sin estado compartido | Cada request crea su propio hash. Bcrypt es CPU-bound, no I/O. | `BcryptStrategy.hash()` no usa variables globales |
| **JWT Service** | Stateless, config readonly | `JWTService.__init__()` carga secret 1 vez. `encode()` y `decode()` no modifican estado. | Config inyectado 1 vez, métodos puros |
| **Auth Service** | Stateless, inyección de deps | Servicios creados per-request o singleton (sin estado mutable). | `AuthService` no tiene `self._data` |
| **Request Context** | FastAPI per-request scope | Cada request tiene su propio contexto (session, user_id). No hay compartir entre requests. | `get_current_user()` dependency invocada per-request |
| **Logging** | Handlers thread-safe | Python logging library es thread-safe (mantiene queue interna). | `logging.getLogger()` + `handler.emit()` |

**Conclusión**: Aplicación es **thread-safe por diseño** gracias a:
1. PostgreSQL ACID (BD responsable de consistencia)
2. SQLAlchemy QueuePool (1 conexión = 1 request)
3. Servicios stateless (sin variables compartidas)
4. Valores inmutables (Value Objects, DTOs)

---

# EFFORT ESTIMATION

Desglose de horas relativas para cada fase:

| Fase | Subtareas | Horas Estimadas | Complexity |
|------|-----------|-----------------|-----------|
| **Phase 0: Research** | 6 research tasks | 2-3 horas | Bajo (lectura + prototipos pequeños) |
| **Phase 1: Domain** | 3 (VO) + 3 (Entity) + 1 (Repo interface) = 7 tasks | 3-4 horas | Medio (lógica pura, sin deps externas) |
| **Phase 2: Application** | 2 (JWT) + 3 (Auth) = 5 tasks | 2-3 horas | Bajo-Medio (orquestación simple) |
| **Phase 3: Infrastructure** | 4 (DB config) + 4 (Repository impl) = 8 tasks | 3-4 horas | Medio (BD, queries, error handling) |
| **Phase 4: Presentation** | 3 (DTOs) + 4 (Dependency) + 4 (Routes) + 2 (App) = 13 tasks | 2-3 horas | Bajo (routing, framework) |
| **TOTAL** | 39 tasks | **12-17 horas** | **Medium-High** |

**Breakdown por prioridad**:
- **Critical** (bloques otras fases): Phase 0, Phase 1.1, Phase 1.2 = ~6 horas
- **High** (enables app logic): Phase 1.3, Phase 2 = ~5 horas
- **Medium** (enables persistence): Phase 3 = ~4 horas
- **Low** (HTTP glue): Phase 4 = ~3 horas

**Notes**:
- Tiempos incluyen debugging y testing manual básico (sin test suite formal)
- Migraciones Alembic (opcional) pueden agregar 1-2 horas si se incluyen
- Setup inicial de PostgreSQL y dependencias: ~1 hora (fuera de este plan)

---

# COMPLETION CHECKLIST

## Fase 0: Research
- [ ] Email validation research completado
- [ ] Hashing strategy research completado
- [ ] Database concurrency research completado
- [ ] JWT specification research completado
- [ ] PostgreSQL constraints research completado
- [ ] FastAPI auth patterns research completado
- [ ] `research.md` generado y completo

## Fase 1: Domain
- [ ] Email VO implementado y testado (manual)
- [ ] Password VO implementado y testado (manual)
- [ ] HashingStrategy interface definida
- [ ] BcryptStrategy implementado
- [ ] User entity implementado
- [ ] User.create() factory implementado
- [ ] IUserRepository interface definida
- [ ] Excepciones de dominio creadas
- [ ] CERO imports de infrastructure/ en domain/
- [ ] `data-model.md` generado

## Fase 2: Application
- [ ] JWTService.encode() implementado
- [ ] JWTService.decode() implementado
- [ ] AuthService.register() implementado
- [ ] AuthService.login() implementado
- [ ] Manejo de excepciones correcto
- [ ] Servicios son stateless

## Fase 3: Infrastructure
- [ ] .env.example creado
- [ ] config.py implementado
- [ ] SQLAlchemy engine configurado (pool correcto)
- [ ] UserModel (SQLAlchemy) implementado
- [ ] UNIQUE constraint en email
- [ ] UserRepository implementado
- [ ] IntegrityError handling correcto
- [ ] Session factory funcionando

## Fase 4: Presentation
- [ ] RegisterRequest/Response DTOs creados
- [ ] LoginRequest/Response DTOs creados
- [ ] UserResponse DTO creado
- [ ] get_current_user() dependency implementada
- [ ] POST /register implementado (201, 400, 409)
- [ ] POST /login implementado (200, 401)
- [ ] GET /me implementado (200, 401)
- [ ] Logging sin passwords
- [ ] FastAPI app runnable con uvicorn
- [ ] `quickstart.md` generado

## General
- [ ] Todas las funciones < 20 líneas
- [ ] Patrones documentados con comentarios
- [ ] DDD separación respetada
- [ ] Thread-safety garantizada (BD, configs, stateless)
- [ ] `requirements.txt` actualizado
- [ ] `README.md` con setup instructions
- [ ] Código pasaría Constitution check

---


