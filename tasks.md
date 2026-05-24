# Tasks: Sistema de Autenticación con JWT + DDD

**Autor:** Generated from AUTH_SPEC.md  
**Fecha:** 2026-05-23  
**Versión:** 1.0  

---

## Resumen Ejecutivo

**Total de Tareas:** 13  
**Orden de Ejecución:** Lineal con dependencias explícitas  
**Duración Estimada:** 13-17 horas (XS: 1h, S: 2h, M: 4h, L: 6h)  
**Stack:** Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL, PyJWT, bcrypt, email-validator  

---

## Legenda

- **ID:** Identificador único (T1, T2, ...)
- **Estimación:** XS (1h), S (2h), M (4h), L (6h)
- **Dependencias:** Tareas que DEBEN completarse antes
- **Pattern:** Patrón de diseño aplicado
- **Criterios:** Qué significa "HECHO"

---

## FASE 1: Setup Inicial

### T1: Crear estructura de carpetas, .env y requirements.txt

**Estimación:** XS (1 hora)  
**Dependencias:** Ninguna  
**Pattern:** N/A  

**Descripción:**
Crear la estructura base del proyecto siguiendo Clean Architecture + DDD:
- Carpeta `src/` con subcarpetas: `domain/`, `application/`, `infrastructure/`, `presentation/`
- Dentro de cada carpeta: `__init__.py` para hacerlas módulos Python
- Crear `.env` (con placeholder) y `.env.example`
- Crear `requirements.txt` con todas las dependencias

**Criterios de Aceptación:**
```
- [ ] Carpeta src/domain/ existe con subcarpetas:
      - entities/
      - value_objects/
      - interfaces/
      - exceptions.py
- [ ] Carpeta src/application/ existe con subcarpeta:
      - auth/
- [ ] Carpeta src/infrastructure/ existe con subcarpetas:
      - persistence/
      - config.py
- [ ] Carpeta src/presentation/ existe con subcarpetas:
      - routers/
      - schemas/
      - dependencies/
      - main.py
- [ ] Archivo .env existe con variables:
      DATABASE_URL=postgresql://user:password@localhost:5432/popolilo_db
      JWT_SECRET_KEY=your-super-secret-key-min-32-chars-for-hs256
      JWT_ALGORITHM=HS256
      JWT_EXPIRATION_HOURS=24
- [ ] Archivo requirements.txt contiene:
      fastapi>=0.104.0
      sqlalchemy>=2.0.0
      psycopg2-binary>=2.9.0
      pydantic>=2.0.0
      pydantic-settings>=2.0.0
      python-jose>=3.3.0
      bcrypt>=4.0.0
      email-validator>=2.0.0
      python-multipart>=0.0.6
      uvicorn>=0.24.0
- [ ] Todos los __init__.py creados en carpetas de módulos
```

**Notas Técnicas:**
- Python 3.10+ requerido (f-strings, type hints mejorados)
- `pydantic-settings` es el reemplazo moderno de `pydantic.config`
- `python-multipart` necesario para FastAPI body parsing

---

## FASE 2: Domain Layer (Capa de Dominio)

### T2: Implementar Value Object Email (domain/value_objects/email.py)

**Estimación:** S (2 horas)  
**Dependencias:** T1  
**Pattern:** Value Object (Inmutable, auto-validación)  

**Descripción:**
Crear Value Object `Email` que encapsule:
1. Validación RFC 5322 con `email-validator` library
2. Inmutabilidad (propiedades read-only)
3. Métodos `__eq__`, `__hash__`, `__str__` para comparación y uso en sets/dicts
4. Nunca serializar el valor directamente (implementar conversor manual)

**Criterios de Aceptación:**
```
- [ ] Clase Email existe en src/domain/value_objects/email.py
- [ ] Constructor recibe un string y lanza ValueError si es inválido
- [ ] Validación usa email-validator.validate_email()
- [ ] Email es inmutable: no hay setters
- [ ] __eq__ compara correctamente dos instancias Email
- [ ] __hash__ permite usar Email como clave en dict/set
- [ ] __str__ retorna la dirección de email
- [ ] Ejemplo de uso:
      email1 = Email("user@example.com")
      email2 = Email("user@example.com")
      assert email1 == email2
      assert hash(email1) == hash(email2)
- [ ] Email("invalid") lanza ValueError
- [ ] Email("") lanza ValueError
- [ ] Pattern comentado en código: # Pattern: Value Object
```

**Notas Técnicas:**
- `email-validator` maneja normalización (ej: "User@Example.Com" → "user@example.com")
- Para hash inmutable necesitamos que el Value Object sea hasheable
- No confundir con SQLAlchemy UserModel.email (que sí es string)

---

### T3: Implementar Value Object Password (domain/value_objects/password.py)

**Estimación:** S (2 horas)  
**Dependencias:** T1  
**Pattern:** Value Object + Strategy (Hash/Verify)  

**Descripción:**
Crear Value Object `Password` que encapsule:
1. Validación de requisitos: mínimo 8 caracteres, ≥1 mayúscula, ≥1 número
2. Hashing con bcrypt via Strategy pattern (permite cambiar bcrypt → argon2 luego)
3. Método `verify()` para comparar plaintext contra hash
4. Nunca exponer plaintext ni hash en serialización

**Criterios de Aceptación:**
```
- [ ] Clase Password existe en src/domain/value_objects/password.py
- [ ] Interfaz HashingStrategy abstracta existe:
      - método hash(plaintext: str) -> str
      - método verify(plaintext: str, hash: str) -> bool
- [ ] Clase BcryptStrategy implementa HashingStrategy
- [ ] Clase BcryptStrategy.hash():
      - Usa bcrypt.gensalt(rounds=12)
      - Retorna hash como string UTF-8
- [ ] Clase BcryptStrategy.verify():
      - Retorna True si plaintext matchea hash
      - Retorna False en caso contrario
      - Maneja excepciones de bcrypt
- [ ] Clase Password:
      - Constructor valida requisitos:
        - Mínimo 8 caracteres
        - Al menos 1 mayúscula (A-Z)
        - Al menos 1 número (0-9)
      - Lanza ValueError con mensaje claro si falla validación
      - Almacena hash en propiedad read-only .hash
      - No almacena plaintext
- [ ] Método Password.verify(plaintext: str) -> bool
- [ ] Password("pass") lanza ValueError (menos de 8 caracteres)
- [ ] Password("password") lanza ValueError (sin mayúscula)
- [ ] Password("Password1") NO lanza (válido)
- [ ] Ejemplo:
      pwd = Password("TestPass123")
      assert pwd.verify("TestPass123") == True
      assert pwd.verify("WrongPass") == False
- [ ] Pattern comentado: # Pattern: Value Object + Strategy
```

**Notas Técnicas:**
- Regex para validación: `[A-Z]` y `\d` mediante regex simple
- `bcrypt.gensalt(rounds=12)` es el estándar de seguridad
- `verify()` es method del VO, no del Strategy (encapsulación)
- Strategy inyectable en constructor para testing sin bcrypt

---

### T4: Implementar User Entity (domain/entities/user.py)

**Estimación:** S (2 horas)  
**Dependencias:** T2, T3  
**Pattern:** Entity + Factory Method  

**Descripción:**
Crear Entity `User` que agregue `Email` y `Password` como Value Objects:
1. Atributos: `id` (UUID), `email` (Email VO), `password` (Password VO), `created_at` (datetime)
2. Factory method `User.create(email: str, password: str)` que valida y construye
3. Immutabilidad del `id` y `created_at` (read-only)

**Criterios de Aceptación:**
```
- [ ] Clase User existe en src/domain/entities/user.py
- [ ] Atributos:
      - id: UUID (inmutable)
      - email: Email VO
      - password: Password VO
      - created_at: datetime (inmutable)
- [ ] Constructor privado (o protegido): User.__init__() o User._init()
- [ ] Static Factory Method User.create(email: str, password: str) -> User:
      - Valida email via Email VO (puede lanzar ValueError)
      - Valida password via Password VO (puede lanzar ValueError)
      - Retorna nueva instancia User con UUID.uuid4()
      - Usa datetime.utcnow() para created_at
- [ ] Ejemplo:
      user = User.create("john@example.com", "SecurePass123")
      assert isinstance(user.id, UUID)
      assert isinstance(user.email, Email)
      assert isinstance(user.password, Password)
- [ ] User.create("invalid@", "Pass123") lanza ValueError
- [ ] User.create("john@example.com", "weak") lanza ValueError
- [ ] Pattern comentado: # Pattern: Entity + Factory Method
```

**Notas Técnicas:**
- Factory Method encapsula la lógica de construcción
- UUID generado al crear (no antes)
- No usar ORM aquí: es puro dominio

---

### T5: Crear Repository Interface (domain/interfaces/i_user_repository.py)

**Estimación:** XS (1 hora)  
**Dependencias:** T4  
**Pattern:** Repository Interface (Abstract Base Class)  

**Descripción:**
Definir contrato abstracto para operaciones de persistencia de User:
1. Métodos: `create()`, `find_by_email()`, `email_exists()`
2. Sin detalles de implementación (ni SQLAlchemy, ni SQL)
3. Documentar qué retorna cada método y qué excepciones lanza

**Criterios de Aceptación:**
```
- [ ] Archivo src/domain/interfaces/i_user_repository.py existe
- [ ] Clase IUserRepository es ABC (ABC de abc module)
- [ ] Método abstracto:
      create(user: User) -> User:
          """Persiste el usuario. Retorna el mismo user con id asignado.
          Lanza UserAlreadyExistsError si email duplicado.
          """
- [ ] Método abstracto:
      find_by_email(email: Email) -> Optional[User]:
          """Retorna el User si existe, None en caso contrario."""
- [ ] Método abstracto:
      email_exists(email: Email) -> bool:
          """True si email ya está registrado, False en caso contrario."""
- [ ] Pattern comentado: # Pattern: Repository (Domain Interface)
```

---

### T6: Crear Domain Exceptions (domain/exceptions.py)

**Estimación:** XS (1 hora)  
**Dependencias:** T1  
**Pattern:** Custom Exceptions (Domain-specific errors)  

**Descripción:**
Definir excepciones de negocio que dominio puede lanzar:
1. `UserAlreadyExistsError` (email duplicado)
2. `InvalidCredentialsError` (login fallido)
3. `UserNotFoundError` (usuario no existe)

**Criterios de Aceptación:**
```
- [ ] Archivo src/domain/exceptions.py existe
- [ ] Clase UserAlreadyExistsError(Exception):
      - mensaje: "User with this email already exists"
- [ ] Clase InvalidCredentialsError(Exception):
      - mensaje: "Invalid email or password"
- [ ] Clase UserNotFoundError(Exception):
      - mensaje: "User not found"
- [ ] Cada excepción hereda de Exception
- [ ] Ejemplo:
      raise UserAlreadyExistsError("Email already registered")
```

---

## FASE 3: Infrastructure Layer (Capa de Infraestructura)

### T7: Configurar Database (infrastructure/config.py, infrastructure/persistence/database.py)

**Estimación:** M (4 horas)  
**Dependencias:** T1  
**Pattern:** Configuration Management + Database Pool  

**Descripción:**
Configurar variables de entorno, connection pooling y sesiones SQLAlchemy:
1. `config.py`: Clase Settings que lee `.env`
2. `database.py`: Engine, SessionLocal, Base y configuración del pool

**Criterios de Aceptación:**
```
- [ ] Archivo src/infrastructure/config.py existe
- [ ] Clase Settings hereda BaseSettings (pydantic_settings)
- [ ] Atributos en Settings:
      - database_url: str (desde DATABASE_URL env)
      - jwt_secret_key: str (desde JWT_SECRET_KEY env)
      - jwt_algorithm: str = "HS256"
      - jwt_expiration_hours: int = 24
- [ ] Archivo src/infrastructure/persistence/database.py existe
- [ ] Crear SQLAlchemy engine:
      engine = create_engine(
          settings.database_url,
          poolclass=NullPool,  # Development
          echo=False
      )
- [ ] Crear SessionLocal:
      SessionLocal = sessionmaker(
          autocommit=False,
          autoflush=False,
          bind=engine
      )
- [ ] Crear declarative_base:
      Base = declarative_base()
- [ ] Función get_db():
      """Dependency para FastAPI, retorna Session."""
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
- [ ] Comentario técnico:
      # Thread-safety: PostgreSQL es ACID compliant.
      # Cada request obtiene su propia conexión del pool.
- [ ] settings singleton importable:
      from src.infrastructure.config import settings
```

**Notas Técnicas:**
- `NullPool` en desarrollo (sin persistencia entre requests)
- `QueuePool` en producción (reutiliza conexiones)
- PostgreSQL maneja thread-safety a nivel de conexión

---

### T8: Crear SQLAlchemy Models (infrastructure/persistence/models.py)

**Estimación:** S (2 horas)  
**Dependencias:** T7  
**Pattern:** ORM Model (Mapper a DB)  

**Descripción:**
Mapear User Entity a tabla `users` en PostgreSQL:
1. Tabla `users` con columnas: id, email, password_hash, created_at
2. Constraint UNIQUE en email para thread-safety
3. Índice en email para queries rápidas

**Criterios de Aceptación:**
```
- [ ] Archivo src/infrastructure/persistence/models.py existe
- [ ] Clase UserModel hereda Base (declarative_base)
- [ ] __tablename__ = "users"
- [ ] Columnas:
      - id: String (UUID as string), primary_key=True
      - email: String(255), unique=True, nullable=False, index=True
      - password_hash: String(255), nullable=False
      - created_at: DateTime, default=datetime.utcnow, nullable=False
- [ ] Comentario de thread-safety:
      # UNIQUE constraint previene race conditions en PostgreSQL
      # IntegrityError si email ya existe (manejado en Repository)
- [ ] Tabla se crea con Alembic o DDL manual:
      CREATE TABLE users (
          id VARCHAR(36) PRIMARY KEY,
          email VARCHAR(255) UNIQUE NOT NULL,
          password_hash VARCHAR(255) NOT NULL,
          created_at TIMESTAMP NOT NULL
      );
      CREATE INDEX idx_users_email ON users(email);
```

---

### T9: Implementar UserRepository (infrastructure/persistence/user_repository.py)

**Estimación:** M (4 horas)  
**Dependencias:** T5, T8, T6  
**Pattern:** Repository Implementation (SQLAlchemy)  

**Descripción:**
Implementar `UserRepository(IUserRepository)` que:
1. Convierte User Entity ↔ UserModel
2. Maneja IntegrityError para email duplicado
3. Transacciones ACID automáticas con SessionLocal

**Criterios de Aceptación:**
```
- [ ] Archivo src/infrastructure/persistence/user_repository.py existe
- [ ] Clase UserRepository(IUserRepository):
- [ ] Constructor:
      __init__(self, session: Session):
          self.session = session
- [ ] Método create(user: User) -> User:
      - Crea instancia UserModel desde User Entity
      - model.id = str(user.id)
      - model.email = str(user.email)
      - model.password_hash = user.password.hash
      - model.created_at = user.created_at
      - self.session.add(model)
      - self.session.commit()
      - Retorna el mismo user Entity
      - En caso de IntegrityError:
        - self.session.rollback()
        - raise UserAlreadyExistsError()
- [ ] Método find_by_email(email: Email) -> Optional[User]:
      - Query: SELECT * FROM users WHERE email = ?
      - Si existe: convertir UserModel → User Entity
      - Si no existe: retorna None
- [ ] Método email_exists(email: Email) -> bool:
      - Query: SELECT COUNT(*) FROM users WHERE email = ?
      - Retorna count > 0
- [ ] Helper privado _model_to_entity(model: UserModel) -> User:
      - Convierte SQLAlchemy model a dominio Entity
      - Reconstruye User desde id, email, password_hash, created_at
- [ ] Comentario de thread-safety:
      # PostgreSQL UNIQUE constraint + rollback en IntegrityError
      # Cada request tiene su propia Session → sin race conditions
- [ ] Ejemplo:
      repo = UserRepository(session)
      user = User.create("john@example.com", "SecurePass123")
      saved_user = repo.create(user)
      assert saved_user.id is not None
      found_user = repo.find_by_email(Email("john@example.com"))
      assert found_user.id == saved_user.id
```

**Notas Técnicas:**
- `_model_to_entity()` es inverse de la conversión en `create()`
- `find_by_email()` retorna None, nunca exception
- `session.commit()` es automático en FastAPI dependency

---

## FASE 4: Application Layer (Capa de Aplicación)

### T10: Implementar JWTService (application/auth/jwt_service.py)

**Estimación:** M (4 horas)  
**Dependencias:** T7  
**Pattern:** Service (Stateless, thread-safe)  

**Descripción:**
Crear servicio que genere y verifique JWT tokens:
1. `generate()`: crea token con claims `sub`, `role`, `iat`, `exp`, `email`
2. `verify()`: valida firma y expiración
3. Sin estado mutable: methods son puros

**Criterios de Aceptación:**
```
- [ ] Archivo src/application/auth/jwt_service.py existe
- [ ] Clase JWTService:
- [ ] Constructor:
      __init__(self, settings: Settings):
          self.settings = settings
- [ ] Método generate(user_id: str, email: str, role: str = "user") -> str:
      - Crea payload dict con claims RFC 7519:
        {
            "sub": user_id,        # subject (user_id as UUID string)
            "email": email,         # email del usuario
            "role": role,           # default "user"
            "iat": int(time.time()),# issued at
            "exp": int(time.time() + 24*3600)  # expiration 24h
        }
      - Usa jwt.encode(payload, secret, algorithm="HS256")
      - Retorna token string
- [ ] Método verify(token: str) -> dict:
      - Intenta jwt.decode(token, secret, algorithms=["HS256"])
      - Retorna payload dict si válido
      - Lanza jwt.ExpiredSignatureError si expirado
      - Lanza jwt.InvalidTokenError si firma inválida
- [ ] Método extract_user_id(payload: dict) -> str:
      - Retorna payload["sub"]
- [ ] Ejemplo:
      service = JWTService(settings)
      token = service.generate("user-id-uuid", "john@example.com")
      payload = service.verify(token)
      assert payload["sub"] == "user-id-uuid"
      assert payload["email"] == "john@example.com"
- [ ] Comentario de thread-safety:
      # JWTService es stateless: no almacena estado mutable.
      # Métodos puros → inherentemente thread-safe.
- [ ] Comentario de secrets:
      # JWT_SECRET_KEY debe tener mínimo 32 caracteres para HS256.
      # Verificar en settings o config.
```

**Notas Técnicas:**
- `python-jose` librería para JWT (alternativa: `PyJWT`)
- `iat` e `exp` son timestamps UNIX en segundos (int)
- Nunca serializar excepciones JWT directamente (manejarlo en API)

---

### T11: Implementar AuthService (application/auth/auth_service.py)

**Estimación:** M (4 horas)  
**Dependencias:** T9, T10  
**Pattern:** Service (Application Use Cases)  

**Descripción:**
Servicio de casos de uso `register()` y `login()`:
1. `register()`: valida, crea User entity, persiste via repo
2. `login()`: busca user, verifica password, retorna JWT token

**Criterios de Aceptación:**
```
- [ ] Archivo src/application/auth/auth_service.py existe
- [ ] Clase AuthService:
- [ ] Constructor:
      __init__(
          self,
          user_repository: IUserRepository,
          jwt_service: JWTService
      ):
- [ ] Método register(email: str, password: str) -> dict:
      - Crea User entity vía User.create(email, password)
      - Si User.create() lanza ValueError → propagar (cliente valida)
      - Persiste vía user_repository.create(user)
      - Si UserAlreadyExistsError → propagar (cliente retorna 409)
      - Retorna {"user_id": str(user.id)}
      - Excepciones posibles:
        - ValueError (de Email o Password VO)
        - UserAlreadyExistsError (email duplicado)
- [ ] Método login(email: str, password: str) -> dict:
      - Busca user vía user_repository.find_by_email(Email(email))
      - Si user es None: raise InvalidCredentialsError
      - Si email inválido (Email VO): raise ValueError
      - Verifica password: user.password.verify(password)
      - Si False: raise InvalidCredentialsError
      - Si True: genera token vía jwt_service.generate()
      - Retorna {"access_token": token, "token_type": "bearer"}
      - Excepciones posibles:
        - ValueError (email inválido)
        - InvalidCredentialsError (user no existe o password incorrecto)
- [ ] Ejemplo:
      service = AuthService(repo, jwt_service)
      # Register
      result = service.register("john@example.com", "SecurePass123")
      assert "user_id" in result
      # Login
      token_result = service.login("john@example.com", "SecurePass123")
      assert "access_token" in token_result
      assert token_result["token_type"] == "bearer"
      # Credenciales inválidas
      with pytest.raises(InvalidCredentialsError):
          service.login("john@example.com", "WrongPassword")
- [ ] Comentario de thread-safety:
      # AuthService es stateless, inyecta dependencias.
      # Repository maneja sincronización en BD.
      # JWT token generación es stateless.
```

---

## FASE 5: Presentation Layer (Capa de Presentación)

### T12: Crear DTOs/Schemas (presentation/schemas/auth_schemas.py)

**Estimación:** S (2 horas)  
**Dependencias:** T1  
**Pattern:** DTO (Data Transfer Object, Pydantic)  

**Descripción:**
Definir esquemas Pydantic para entrada/salida HTTP:

**Criterios de Aceptación:**
```
- [ ] Archivo src/presentation/schemas/auth_schemas.py existe
- [ ] Clase RegisterRequest(BaseModel):
      - email: str
      - password: str
- [ ] Clase RegisterResponse(BaseModel):
      - user_id: str
- [ ] Clase LoginRequest(BaseModel):
      - email: str
      - password: str
- [ ] Clase LoginResponse(BaseModel):
      - access_token: str
      - token_type: str = "bearer"
- [ ] Clase MeResponse(BaseModel):
      - user_id: str
- [ ] Validación adicional (opcional):
      - RegisterRequest.email puede incluir EmailStr de pydantic
      - RegisterRequest.password con field description
- [ ] Ejemplo:
      req = RegisterRequest(email="john@example.com", password="Secure123")
      resp = RegisterResponse(user_id="uuid-string")
```

---

### T13: Implementar Middleware/Dependencies (presentation/dependencies/auth.py)

**Estimación:** S (2 horas)  
**Dependencias:** T10  
**Pattern:** FastAPI Dependency Injection + Middleware  

**Descripción:**
Crear función `get_current_user()` que:
1. Extrae token del header `Authorization: Bearer <token>`
2. Valida token con JWTService
3. Inyecta `user_id` en `request.state`

**Criterios de Aceptación:**
```
- [ ] Archivo src/presentation/dependencies/auth.py existe
- [ ] Función get_current_user(
          request: Request,
          jwt_service: JWTService = Depends(...)
      ) -> str:
      - Extrae header Authorization
      - Si no existe: raise HTTPException(status_code=401, detail="Missing token")
      - Parsea formato "Bearer <token>"
      - Si no está en formato Bearer: raise HTTPException(401)
      - Intenta jwt_service.verify(token)
      - Si ExpiredSignatureError: raise HTTPException(401, "Token expired")
      - Si InvalidTokenError: raise HTTPException(401, "Invalid token")
      - Retorna user_id del payload
- [ ] Ejemplo uso en endpoint:
      @router.get("/me")
      async def me(user_id: str = Depends(get_current_user)):
          return {"user_id": user_id}
- [ ] HTTPException 401 para:
      - Token faltante
      - Token expirado
      - Firma inválida
- [ ] Comentario de thread-safety:
      # FastAPI injeca nueva instancia por request → sin race conditions.
```

---

### T14: Crear Routers (presentation/routers/auth.py)

**Estimación:** M (4 horas)  
**Dependencias:** T11, T12, T13  
**Pattern:** FastAPI Routers + Dependency Injection  

**Descripción:**
Implementar endpoints `/register`, `/login`, `/me`:

**Criterios de Aceptación:**
```
- [ ] Archivo src/presentation/routers/auth.py existe
- [ ] Endpoint POST /register:
      - Recibe RegisterRequest
      - Inyecta AuthService vía Depends
      - Llama auth_service.register(email, password)
      - Si ValueError (email/password inválido):
        - Retorna 400 con {"detail": "Invalid email or password"}
      - Si UserAlreadyExistsError:
        - Retorna 409 con {"detail": "Email already registered"}
      - Si OK:
        - Retorna 201 con RegisterResponse(user_id=...)
- [ ] Endpoint POST /login:
      - Recibe LoginRequest
      - Inyecta AuthService vía Depends
      - Llama auth_service.login(email, password)
      - Si ValueError (email inválido):
        - Retorna 400 con {"detail": "Invalid email"}
      - Si InvalidCredentialsError:
        - Retorna 401 con {"detail": "Invalid email or password"}
      - Si OK:
        - Retorna 200 con LoginResponse(access_token=...)
- [ ] Endpoint GET /me (protegido):
      - Inyecta user_id vía get_current_user dependency
      - Si token faltante/inválido:
        - Retorna 401 (automático por dependency)
      - Si OK:
        - Retorna 200 con MeResponse(user_id=...)
- [ ] Comentario de thread-safety:
      # Cada request = nueva transacción BD + nueva sesión SQLAlchemy.
- [ ] Ejemplo de integración:
      POST /register
      {"email": "john@example.com", "password": "SecurePass123"}
      → 201 {"user_id": "uuid-..."}
      
      POST /login
      {"email": "john@example.com", "password": "SecurePass123"}
      → 200 {"access_token": "eyJ...", "token_type": "bearer"}
      
      GET /me (header: "Authorization: Bearer eyJ...")
      → 200 {"user_id": "uuid-..."}
```

---

### T15: Crear Main App (presentation/main.py)

**Estimación:** S (2 horas)  
**Dependencias:** T14, T7, T10, T11  
**Pattern:** FastAPI Application + Dependency Container  

**Descripción:**
Crear instancia FastAPI y registrar routers, incluir inyección de dependencias:

**Criterios de Aceptación:**
```
- [ ] Archivo src/presentation/main.py existe
- [ ] Instancia FastAPI:
      app = FastAPI(
          title="Popolilo Auth API",
          version="1.0.0",
          description="Autenticación con JWT"
      )
- [ ] Registro de routers:
      app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
- [ ] Inyección de dependencias (FastAPI Lifespan o startup event):
      - Crear engine SQLAlchemy
      - Crear SessionLocal
      - Crear instancias de:
        - Settings
        - JWTService(settings)
        - UserRepository(SessionLocal)
        - AuthService(repo, jwt_service)
      - Hacer availables vía app.state o dependency override
- [ ] Endpoint GET /health (sin autenticación):
      - Retorna 200 {"status": "ok"}
- [ ] Manejo de excepciones global:
      - Interceptar HTTPException y retornar JSON
      - Interceptar excepciones inesperadas → 500
- [ ] Comentario de arquitectura:
      # FastAPI Dependency Injection maneja thread-safety:
      # Cada request → nueva instancia de dependencias.
- [ ] Ejemplo ejecución:
      if __name__ == "__main__":
          import uvicorn
          uvicorn.run(
              "src.presentation.main:app",
              host="0.0.0.0",
              port=8000,
              reload=True
          )
```

---

### T16: Crear Entry Point (main.py en raíz o app.py)

**Estimación:** XS (1 hora)  
**Dependencias:** T15  
**Pattern:** Entry Point Script  

**Descripción:**
Crear script ejecutable para correr la aplicación con Uvicorn:

**Criterios de Aceptación:**
```
- [ ] Archivo src/main.py o app.py existe en raíz proyecto
- [ ] Contenido:
      import uvicorn
      from src.presentation.main import app
      
      if __name__ == "__main__":
          uvicorn.run(
              app,
              host="0.0.0.0",
              port=8000
          )
- [ ] Script ejecutable:
      python src/main.py
      → Servidor levantado en http://localhost:8000
- [ ] API docs disponible:
      GET http://localhost:8000/docs (Swagger UI)
      GET http://localhost:8000/redoc (ReDoc)
```

---

## FASE 6: Testing + Documentación

### T17: Crear README.md y .env.example

**Estimación:** S (2 horas)  
**Dependencias:** Todas las anteriores  
**Pattern:** Documentation  

**Descripción:**
Documentar setup PostgreSQL, instalación, ejecución y ejemplos:

**Criterios de Aceptación:**
```
- [ ] Archivo README.md existe en raíz
- [ ] Secciones:
      1. Descripción breve (JWT auth, DDD, Clean Architecture)
      2. Requisitos: Python 3.10+, PostgreSQL 12+
      3. Setup PostgreSQL:
         - Crear BD: CREATE DATABASE popolilo_db;
         - User: postgresql://user:password@localhost:5432/popolilo_db
      4. Instalación:
         - python -m venv venv
         - source venv/bin/activate (o venv\Scripts\activate en Windows)
         - pip install -r requirements.txt
      5. Configuración:
         - Copiar .env.example → .env
         - Rellenar DATABASE_URL y JWT_SECRET_KEY
      6. Ejecución:
         - python src/main.py
         - O: uvicorn src.presentation.main:app --reload
      7. Ejemplos de uso (curl o Postman):
         - POST /api/v1/register
         - POST /api/v1/login
         - GET /api/v1/me (con Authorization header)
      8. Estructura de carpetas (diagrama ASCII)
- [ ] Archivo .env.example existe
- [ ] Contenido:
      DATABASE_URL=postgresql://user:password@localhost:5432/popolilo_db
      JWT_SECRET_KEY=your-super-secret-key-min-32-chars-for-hs256
      JWT_ALGORITHM=HS256
      JWT_EXPIRATION_HOURS=24
```

---

## Grafo de Dependencias

```
T1 (Setup)
├─ T2 (Email VO)
├─ T3 (Password VO)
├─ T5 (Domain Exceptions)
├─ T7 (Database Config)
│  ├─ T8 (SQLAlchemy Models)
│  │  └─ T9 (UserRepository)
│  │     ├─ T11 (AuthService)
│  │     │  └─ T14 (Routers)
│  │     │     └─ T15 (Main App)
│  │     │        └─ T16 (Entry Point)
│  │     │           └─ T17 (README)
│  │     └─ T4 (User Entity)
│  │        ├─ T2, T3
│  │        └─ T9
├─ T4 (User Entity)
│  ├─ T2, T3
│  └─ T5 (Domain Exceptions)
├─ T6 (Repository Interface)
│  └─ T4 (User Entity)
├─ T10 (JWTService)
│  ├─ T7 (Settings)
│  └─ T11 (AuthService)
│     └─ T14 (Routers)
├─ T12 (DTOs/Schemas)
│  └─ T14 (Routers)
├─ T13 (Middleware/Dependencies)
│  └─ T10 (JWTService)
│     └─ T14 (Routers)
```

---

## Orden de Ejecución Recomendado

1. **T1**: Setup (estructura, .env, requirements.txt)
2. **T2-T3**: Value Objects (Email, Password)
3. **T4**: User Entity
4. **T5**: Domain Exceptions
5. **T6**: Repository Interface
6. **T7**: Database Config
7. **T8**: SQLAlchemy Models
8. **T9**: UserRepository
9. **T10**: JWTService
10. **T11**: AuthService
11. **T12**: DTOs/Schemas
12. **T13**: Middleware/Dependencies
13. **T14**: Routers
14. **T15**: Main App
15. **T16**: Entry Point
16. **T17**: README + .env.example

---

## Resumen de Patrones por Tarea

| Tarea | Patrón | Ubicación | Comentario |
|-------|--------|-----------|-----------|
| T2 | Value Object | `domain/value_objects/` | Inmutable, auto-validación |
| T3 | Value Object + Strategy | `domain/value_objects/` | Strategy para hashing |
| T4 | Entity + Factory Method | `domain/entities/` | Factory encapsula construcción |
| T5 | Custom Exceptions | `domain/` | Domain-specific errors |
| T6 | Repository Interface | `domain/interfaces/` | Contrato abstracto |
| T8 | ORM Model | `infrastructure/persistence/` | SQLAlchemy mapper |
| T9 | Repository Implementation | `infrastructure/persistence/` | Convierte Entity ↔ Model |
| T10 | Service (Stateless) | `application/auth/` | JWT generation/verification |
| T11 | Service (Use Cases) | `application/auth/` | Orquesta domain + infra |
| T14 | Routers + DI | `presentation/routers/` | FastAPI endpoints |
| T15 | Factory + DI Container | `presentation/` | Inyecta dependencias |

---

## Thread-Safety Summary

| Componente | Estrategia | Notas |
|------------|-----------|-------|
| PostgreSQL | ACID + UNIQUE constraint | BD maneja sincronización |
| SQLAlchemy Pool | `QueuePool` (prod) / `NullPool` (dev) | Cada request = nueva conexión |
| Email Unique | Constraint en BD + IntegrityError handling | Previene duplicados concurrentes |
| JWTService | Stateless | Inherentemente thread-safe |
| AuthService | Stateless + inyección | Sin estado mutable compartido |
| FastAPI | Dependency per request | Aislamiento automático |

---

## Criterios de Completitud Global

**Setup Completo:**
- Todas las carpetas existen
- Archivo `.env` tiene 4 variables mínimas
- `requirements.txt` tiene todas las dependencias

**Dominio Válido:**
- Value Objects son inmutables (no hay setters)
- User Entity solo se crea via factory
- Repository es interface abstracta
- Excepciones son específicas de negocio

**Infraestructura Funcional:**
- PostgreSQL conexión exitosa
- SQLAlchemy modela tabla `users` con constraints
- UserRepository convierte Entity ↔ Model correctamente

**Aplicación Correcta:**
- JWTService genera tokens válidos (verificables)
- AuthService orquesta casos de uso
- Excepciones se propagan correctamente

**Presentación Completa:**
- DTOs validados con Pydantic
- Middleware valida tokens
- Endpoints retornan HTTP status correcto
- FastAPI docs funcionan (/docs)

**Documentación:**
- README explica setup PostgreSQL
- .env.example tiene todas las variables
- Patrones comentados en código

---

## Estimación Total

```
XS (1h):   T1, T5, T6, T16                              = 4 horas
S (2h):    T2, T3, T4, T12, T13, T17                    = 12 horas
M (4h):    T7, T8, T9, T10, T11, T14, T15               = 28 horas
───────────────────────────────────────────────────────
Total:                                                   = 44 horas (puede variar ±20% según experiencia)
```

**Sugerencia MVP (1-2 jornadas):**
- Hito 1: T1-T11 (Setup + Domain + Infra + Core Auth Service)
- Hito 2: T12-T17 (API Endpoints + Documentación)

---

## Notas Finales

1. **Sin Testing en esta iteración** (per "no testing" en CONSTITUTION.md)
2. **Thread-safety garantizada por:**
   - PostgreSQL constraints
   - SQLAlchemy session isolation
   - FastAPI dependency injection
3. **Patrones documentados en código** con comentario `# Pattern: <Nombre>`
4. **Concurrencia verificable** con load test en futuras iteraciones
5. **Secrets seguros:** JWT secret mínimo 32 caracteres, nunca en git

