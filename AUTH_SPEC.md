# Especificación: Sistema de Autenticación con JWT + Base Concurrencia

## Alcance
Implementar el subsistema de autenticación (registro, login, JWT) siguiendo Clean Architecture, DDD y principios de concurrencia. Esta iteración NO incluye workers ni colas de procesamiento.

## Contexto
El sistema será un backend distribuido concurrente. La autenticación debe ser thread-safe porque múltiples requests pueden llegar simultáneamente.

---

## Clarifications

### Session 2026-05-23
- Q: ¿Validación de email: regex simple o RFC 5322 robusto? → A: email-validator library (RFC 5322 compliant)
- Q: ¿Claims del JWT? → A: `sub` (user_id), `role`, `iat`, `exp`, `email`

---

## Requerimientos Funcionales

### RF1 - Registro de usuario
- **Endpoint:** `POST /register`
- **Body:** `{ "email": string, "password": string }`
- **Validaciones de negocio** (implementadas en Value Objects):
  - Email: formato válido (regex simple) y único en el sistema
  - Password: mínimo 8 caracteres, al menos 1 mayúscula, 1 número
- **Almacenamiento:** password hasheado (bcrypt)
- **Respuesta exitosa:** `201` con `{ "user_id": "uuid-string" }`
- **Errores:** 
  - `400` (validación fallida: email inválido, password débil)
  - `409` (email ya existe)

### RF2 - Login
- **Endpoint:** `POST /login`
- **Body:** `{ "email": string, "password": string }`
- **Proceso:**
  - Verificar credenciales contra hash almacenado
  - Generar JWT con expiración de 24 horas
  - **JWT claims (RFC 7519 estándar):**
    - `sub` (subject): user_id (UUID)
    - `role`: "user" (default; "admin" en futuras iteraciones)
    - `iat` (issued at): timestamp de emisión (int)
    - `exp` (expiration): timestamp de expiración (int, iat + 24h)
    - `email`: email del usuario (string)
- **Respuesta exitosa:** `200` con `{ "access_token": string, "token_type": "bearer" }`
- **Errores de credenciales:** `401` (sin diferenciar entre email no encontrado vs password incorrecto)

### RF3 - Middleware de autenticación
- **Endpoints protegidos:** crear endpoint dummy `GET /me` que retorne `{ "user_id": "uuid-string" }`
- **Lectura de token:** header `Authorization: Bearer <token>`
- **Validaciones:**
  - Firma JWT válida
  - Token no expirado
- **Inyección:** `user_id` en `request.state.user_id`
- **Errores:** `401` si token faltante, inválido o expirado

---

## Arquitectura DDD + Clean Architecture

```
src/
├── domain/
│   ├── entities/
│   │   └── user.py                 # User entity (id, email, password_hash)
│   ├── value_objects/
│   │   ├── email.py                # Email VO (validación, unicidad)
│   │   └── password.py             # Password VO (validación, hashing)
│   └── interfaces/
│       └── i_user_repository.py    # Interfaz abstracta (contrato)
├── application/
│   └── auth/
│       ├── auth_service.py         # Casos de uso: register, login
│       └── jwt_service.py          # Generar/verificar tokens
├── infrastructure/
│   ├── persistence/
│   │   ├── user_repository.py      # Implementación PostgreSQL
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   └── database.py             # Pool de conexiones, sesiones
│   └── config.py                   # Variables de entorno
└── presentation/
    ├── routers/
    │   └── auth.py                 # Endpoints /register, /login, /me
    ├── schemas/
    │   └── auth_schemas.py         # DTOs (RegisterRequest, LoginResponse, etc.)
    ├── dependencies/
    │   └── auth.py                 # Dependencia get_current_user
    └── main.py                     # FastAPI app instance
```

---

## Patrones de Diseño Obligatorios

### 1. Value Objects
- **Email**: Valida formato, implementa `__eq__`, `__hash__` (inmutable)
- **Password**: Valida requisitos, implementa hashing con bcrypt, nunca se serializa

```python
# Pattern: Value Object
class Email:
    def __init__(self, value: str):
        if not self._is_valid(value):
            raise ValueError(f"Invalid email: {value}")
        self._value = value
    
    @staticmethod
    def _is_valid(email: str) -> bool:
        # email-validator library (RFC 5322 compliant)
        # Implements robust validation per standard
        from email_validator import validate_email, EmailNotValidError
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    def __eq__(self, other):
        return isinstance(other, Email) and self._value == other._value
    
    def __hash__(self):
        return hash(self._value)
    
    def __str__(self):
        return self._value
```

### 2. Repository Pattern
- **Interfaz en `domain/interfaces/`**: contrato sin detalles técnicos
- **Implementación en `infrastructure/persistence/`**: SQLAlchemy, transacciones ACID

```python
# Pattern: Repository
class IUserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User:
        """Retorna el usuario creado con ID asignado."""
        pass
    
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """Retorna None si no existe."""
        pass
    
    @abstractmethod
    def email_exists(self, email: Email) -> bool:
        """Verifica existencia sin recuperar la entidad completa."""
        pass

class UserRepository(IUserRepository):
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def create(self, user: User) -> User:
        model = UserModel(
            id=str(user.id),
            email=str(user.email),
            password_hash=user.password.hash,
            created_at=datetime.utcnow()
        )
        self.session.add(model)
        self.session.commit()
        return user
```

### 3. Factory Pattern
- `User.create(email, password)` encapsula validación y construcción

```python
# Pattern: Factory
class User:
    @staticmethod
    def create(email: str, password: str) -> "User":
        """Factory que valida y construye la entidad."""
        email_vo = Email(email)  # Lanza si inválido
        password_vo = Password(password)  # Lanza si débil
        return User(
            id=UUID(int=0),  # Temporal, BD asigna
            email=email_vo,
            password=password_vo
        )
```

### 4. Strategy Pattern (Opcional)
- `HashingStrategy` permite cambiar bcrypt → argon2 sin modificar dominio

```python
# Pattern: Strategy (opcional pero recomendado)
class HashingStrategy(ABC):
    @abstractmethod
    def hash(self, plaintext: str) -> str:
        pass
    
    @abstractmethod
    def verify(self, plaintext: str, hash: str) -> bool:
        pass

class BcryptStrategy(HashingStrategy):
    def hash(self, plaintext: str) -> str:
        return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()
    
    def verify(self, plaintext: str, hash: str) -> bool:
        return bcrypt.checkpw(plaintext.encode(), hash.encode())

# En Password VO:
class Password:
    def __init__(self, plaintext: str, strategy: HashingStrategy = None):
        if not self._is_strong(plaintext):
            raise ValueError("Password too weak")
        strategy = strategy or BcryptStrategy()
        self._hash = strategy.hash(plaintext)
```

---

## Concurrencia (Thread-Safety)

### PostgreSQL como BD
- PostgreSQL es **ACID compliant** y thread-safe a nivel de conexión
- SQLAlchemy usa `NullPool` en desarrollo o `QueuePool` en producción
- **Cada request obtiene su propia conexión del pool** → sin race conditions

### Email Unique Constraint
- Usar constraint `UNIQUE` en BD: `CREATE UNIQUE INDEX idx_users_email ON users(email);`
- En caso de violación: `IntegrityError` → capturar y retornar `409`

### Código thread-safe
```python
# UserRepository.create() con constraint UNIQUE
try:
    self.session.add(model)
    self.session.commit()
except IntegrityError:
    self.session.rollback()
    raise UserAlreadyExistsError("Email already registered")
```

### JWTService
- **Stateless**, inherentemente thread-safe
- Solo lectura de config (JWT secret desde env)

### AuthService
- **Inyectado una sola vez** en el app (Singleton por FastAPI)
- Métodos puros: `register(email, password)` y `login(email, password)`
- Sin estado mutable compartido

---

## Configuración y Secretos

### `.env` y variables de entorno
```
DATABASE_URL=postgresql://user:password@localhost:5432/popolilo_db
JWT_SECRET_KEY=your-super-secret-key-min-32-chars-for-hs256
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### `config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## Criterios de Aceptación

### Funcionalidad Básica
- [ ] `POST /register` con email y password válidos retorna `201` con `user_id`
- [ ] `POST /register` con email existente retorna `409`
- [ ] `POST /register` con email inválido retorna `400`
- [ ] `POST /register` con password débil retorna `400`
- [ ] `POST /login` con credenciales válidas retorna `200` con `access_token`
- [ ] `POST /login` con password incorrecto retorna `401`
- [ ] `POST /login` con email no registrado retorna `401`
- [ ] `GET /me` con token válido retorna `200` con `user_id`
- [ ] `GET /me` sin token retorna `401`
- [ ] `GET /me` con token expirado retorna `401`
- [ ] `GET /me` con token inválido retorna `401`

### Clean Code + DDD
- [ ] Ninguna función `>20` líneas
- [ ] `domain/` no importa de `infrastructure/` ni `presentation/`
- [ ] `Email` y `Password` son Value Objects inmutables
- [ ] Password nunca se almacena en texto plano
- [ ] Patrones documentados con comentario `# Pattern: <Nombre>`

### Entregables
- [ ] Código fuente con estructura de carpetas completa
- [ ] `requirements.txt` con dependencias (fastapi, sqlalchemy, psycopg2, passlib[bcrypt], python-jose)
- [ ] `README.md` con instrucciones para setup PostgreSQL y ejecución
- [ ] `.env.example` con plantilla de variables
- [ ] Migraciones Alembic (opcional pero recomendado)

---

## No incluido en esta iteración
- Workers, colas, procesamiento de textos
- Reportes, WebSockets, métricas
- Priorización, cancelación
- Roles admin (estructura lista, sin endpoints)
- Webhooks
- **Script de prueba de concurrencia** (se construirá cuando se tenga implementación base)

---

## Referencia Rápida

| Concepto | Ubicación | Responsabilidad |
|---|---|---|
| Email validation | `domain/value_objects/email.py` | Validar formato, unicidad lógica |
| Password hashing | `domain/value_objects/password.py` | Validar requisitos, delegar hash a Strategy |
| User entity | `domain/entities/user.py` | Identidad, agregar email + password |
| IUserRepository | `domain/interfaces/i_user_repository.py` | Contrato abstracto |
| UserRepository | `infrastructure/persistence/user_repository.py` | Implementación PostgreSQL |
| AuthService | `application/auth/auth_service.py` | Casos de uso register/login |
| JWTService | `application/auth/jwt_service.py` | Generar y verificar tokens |
| AuthRouter | `presentation/routers/auth.py` | Endpoints FastAPI |
| get_current_user | `presentation/dependencies/auth.py` | Dependencia FastAPI para proteger rutas |

---

## Notas Importantes

1. **PostgreSQL en desarrollo**: Usa `psycopg2` o `psycopg[binary]`
2. **Migraciones**: Alembic es opcional pero recomendado para reproducibilidad
3. **JWT secret**: Generar con `secrets.token_urlsafe(32)` en `.env`
4. **Error handling**: Errores específicos en `domain/exceptions.py` (ej: `UserAlreadyExistsError`, `InvalidCredentialsError`)
5. **Logging**: Registrar intentos de login fallidos (no passwords)
6. **Rate limiting** (futuro): Preparar arquitectura para agregar rate limiting en `/login`
