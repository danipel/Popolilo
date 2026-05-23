# Research: Sistema de Autenticación con JWT

**Date**: 2026-05-23 | **Output of**: Phase 0 (Research & Clarifications)

---

## R0.1: Email Validation Research

**Question**: RFC 5322 compliant email validation?

**Decision**: Use `email-validator` library

**Rationale**: 
- RFC 5322 fully compliant (official library)
- Simple API: `validate_email(email)` throws `EmailNotValidError` if invalid
- Prevents false positives with weak regex
- Industry standard (used by Django, FastAPI examples)

**Alternatives Considered**:
- Simple regex `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`: Too weak, rejects valid emails
- Manual RFC parsing: Overkill, error-prone
- `email_validator` ✓: Best of both worlds (strict, simple)

**Implementation**: `domain/value_objects/email.py`
```python
from email_validator import validate_email, EmailNotValidError

class Email:
    def _is_valid(email: str) -> bool:
        try:
            validate_email(email)  # Raises EmailNotValidError if invalid
            return True
        except EmailNotValidError:
            return False
```

**Dependencies**: `pip install email-validator`

---

## R0.2: Password Hashing: Bcrypt vs Argon2

**Question**: Which hashing algorithm?

**Decision**: Use **Bcrypt** with Strategy pattern for future flexibility

**Rationale**:
- **Bcrypt**: Industry standard, proven, ~1 second cost factor (adaptive), resistant to GPU attacks
- **Argon2**: Memory-hard (better than Bcrypt), but overkill for typical web app auth
- **Approach**: Implement `HashingStrategy` interface to swap to Argon2 later without touching domain

**Performance Comparison**:
| Algorithm | Time (1 hash) | Relative Cost | Future-proof |
|-----------|---------------|---------------|-------------|
| bcrypt (cost=12) | ~200-250ms | Baseline | High |
| argon2 (m=65536, t=3) | ~100-150ms | Faster | Higher |
| plain MD5/SHA256 | <1ms | Unusable | Low |

**Selection**: Bcrypt (proven + Strategy pattern for flexibility)

**Implementation**: 
- `domain/interfaces/i_hashing_strategy.py`: Interface
- `infrastructure/security/bcrypt_strategy.py`: Implementation
- `domain/value_objects/password.py`: Uses strategy

---

## R0.3: SQLAlchemy Connection Pooling

**Question**: How to ensure thread-safe DB connections?

**Decision**: SQLAlchemy `QueuePool` for production, `NullPool` for development

**Justification**:
- **QueuePool** (default, production):
  - Maintains pool of 10 persistent connections
  - Each request gets isolated connection from queue
  - Connections returned to pool after request completes
  - NO sharing between threads → Thread-safe
  - Prevents "connection already in use" errors

- **NullPool** (development):
  - New connection per request, closed after
  - Simpler for development (no pool state)
  - Slightly slower, but fine for single-threaded dev

**Configuration**:
```python
# Production
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,        # Concurrent connections
    max_overflow=20      # Extra connections if all busy
)

# Development
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool   # No pooling, 1 connection per request
)
```

**Thread-Safety Guarantee**: 
Each request → unique connection → no race conditions on DB level

---

## R0.4: JWT Claims (RFC 7519)

**Question**: What claims to include in JWT?

**Decision**: Standard claims per RFC 7519: `sub`, `role`, `iat`, `exp`, `email`

**Claims Breakdown**:
| Claim | Type | Example | Purpose |
|-------|------|---------|---------|
| `sub` | string | "550e8400-e29b-41d4-a716-446655440000" | Subject (user_id), identifies token owner |
| `role` | string | "user" | Authorization role (expandable: "admin" later) |
| `iat` | int | 1705996800 | Issued at (Unix timestamp), audit trail |
| `exp` | int | 1706083200 | Expiration (iat + 24h), security boundary |
| `email` | string | "user@example.com" | User email for quick access (optional but useful) |

**Expirations**:
- Access token: 24 hours (per AUTH_SPEC.md)
- Refresh tokens: Not included in this iteration
- Clock skew: 0 seconds (strict expiration)

**Encoding/Decoding** (using `python-jose`):
```python
from jose import jwt
from datetime import datetime, timedelta

def encode(user_id: str, email: str, secret: str, algorithm: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "role": "user",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=24)).timestamp())
    }
    return jwt.encode(payload, secret, algorithm=algorithm)

def decode(token: str, secret: str, algorithm: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except JWTClaimsError:
        raise InvalidTokenError("Token claims invalid")
    except JWTError:
        raise InvalidTokenError("Token signature invalid")
```

**Security Notes**:
- Secret stored in `.env` (min 32 chars for HS256)
- Algorithm: HS256 (symmetric key, sufficient for single backend)
- No sensitive info in token (publicly readable)

---

## R0.5: PostgreSQL UNIQUE Constraints

**Question**: How to prevent duplicate emails at scale?

**Decision**: BD-level UNIQUE constraint + application-level exception handling

**Mechanism**:
1. **DB Constraint**: `CREATE UNIQUE INDEX idx_users_email ON users(email);`
2. **Enforcement**: PostgreSQL prevents 2nd insert with same email (at transaction boundary)
3. **Concurrency**: Even if 2 requests insert same email simultaneously:
   - Both hit serialization point (unique index check)
   - Only 1 succeeds, 1st gets `IntegrityError` (PostgreSQL ACID)
4. **Application Handling**: Catch `IntegrityError` → map to `UserAlreadyExistsError` → `409 Conflict`

**Example Race Condition Resolution**:
```
Request A (thread 1): INSERT user (email=test@example.com)
Request B (thread 2): INSERT user (email=test@example.com)  [concurrent]

Timeline:
T0: A validates email format ✓
T0: B validates email format ✓
T1: A checks email_exists() → false ✓
T1: B checks email_exists() → false ✓  [race condition, but OK]
T2: A executes INSERT + commits → SUCCESS
T3: B executes INSERT → IntegrityError (UNIQUE constraint violation)
T4: B catches IntegrityError → raises UserAlreadyExistsError → 409
```

**Code Pattern**:
```python
class UserRepository(IUserRepository):
    def create(self, user: User) -> User:
        model = UserModel(...)
        self.session.add(model)
        try:
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            if "users_email" in str(e):  # UNIQUE constraint on email
                raise UserAlreadyExistsError("Email already registered")
            raise  # Other IntegrityError
        return user
```

**Conclusion**: BD-enforced constraints are the correct approach for concurrent systems.

---

## R0.6: FastAPI Dependency Injection for Auth

**Question**: How to extract and validate JWT in FastAPI?

**Decision**: Use `Depends()` with custom dependency function + `HTTPBearer` security scheme

**Pattern**:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency: extract token from Authorization header.
    Returns user_id if valid, raises HTTPException(401) if invalid.
    """
    token = credentials.credentials
    
    try:
        payload = jwt_service.decode(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_id

# Usage in route
@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}
```

**Advantages**:
- Automatic OpenAPI documentation (security badge on Swagger)
- Per-route protection: `Depends(get_current_user)`
- Centralized auth logic: Changes to `get_current_user` apply everywhere
- FastAPI handles injection scope (per-request)

**Header Format**: `Authorization: Bearer <token>`
- `Bearer` is the auth scheme
- Token is the JWT
- FastAPI's `HTTPBearer` extracts automatically

**Thread-Safety**: Dependency is invoked per-request → each request has isolated context.

---

## Key Decisions Summary

| Decision | Choice | Why |
|----------|--------|-----|
| Email validation | email-validator | RFC 5322 compliant, proven |
| Password hashing | Bcrypt + Strategy pattern | Proven, flexible for future |
| Connection pooling | QueuePool (prod), NullPool (dev) | Ensures thread-safety via isolation |
| JWT claims | sub, role, iat, exp, email | RFC 7519 standard |
| Duplicate email prevention | BD UNIQUE constraint | ACID-enforced at transaction boundary |
| Auth middleware | FastAPI Depends + HTTPBearer | Idiomatic FastAPI, automatic docs |

---

## Next Steps (Phase 1)

1. Implement `domain/value_objects/email.py` (use email-validator)
2. Implement `domain/value_objects/password.py` (use bcrypt via strategy)
3. Implement `domain/entities/user.py` (aggregate root)
4. Implement `domain/interfaces/i_user_repository.py` (contract)
5. Validate zero external imports in `domain/`

All research findings inform the implementation order and patterns.
