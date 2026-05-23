# Feature Spec: Autenticación y Autorización

**Branch:** 2026-0523-auth-clarifications  
**Date:** 2026-05-23  
**Status:** En Clarificación (P5/5)

---

## Overview

Sistema de autenticación y autorización básico para v1 del producto Popolilo:
- Registro de usuarios (email + password)
- Autenticación con JWT de 24 horas
- Control de acceso a endpoints protegidos
- Gestión de estado de sesión en cliente

---

## Clarifications

### Session 2026-05-23

- **P1:** ¿Password hashing? → A: bcrypt con salt 10
- **P2:** ¿Rate limiting en login? → A: 5 intentos/15 min por IP
- **P3:** ¿Endpoint GET /me? → A: Sí, retorna user info actual
- **P4:** ¿Estrategia tokens? → A: Solo access tokens 24h ahora, refresh tokens en v2
- **P5:** ¿Estructura DTOs? → [PENDIENTE]

---

## Functional Requirements

### User Actors

1. **Unregistered User** - Puede registrarse o autenticarse
2. **Authenticated User** - Acceso a endpoints protegidos (GET /me)
3. **Admin** - [Futura] Gestión de usuarios y permisos

### Core Flows

#### 1. Registro (POST /register)
- Input: `{ email, password }`
- Validación: Email formato válido, password >= 8 caracteres
- Hash: bcrypt (salt 10)
- Output: DTOs mínimo (estructura definida en P5)
- Error 409: Email ya registrado
- Error 400: Validación falla

#### 2. Autenticación (POST /login)
- Input: `{ email, password }`
- Validación: Credenciales válidas
- Rate limit: 5 intentos / 15 min por IP
- Output: JWT access token (24h) + metadatos (definidos en P5)
- Error 401: Credenciales inválidas
- Error 429: Rate limit excedido

#### 3. Verificación de Sesión (GET /me)
- Require: Access token válido en header `Authorization: Bearer <token>`
- Output: User info (estructura definida en P5)
- Error 401: Token expirado o inválido
- Error 403: Token presente pero no autorizado (reservado)

### Out of Scope (v1)

- Refresh tokens → v2
- OAuth2 / SSO → v2
- 2FA → v2
- Password reset flow → v2
- Email verification → v2
- Role-based access control (RBAC) → v2
- Logout endpoint → v2 (token expiración en cliente)
- Audit logs → v2

---

## Data Model

### User Entity

```
{
  user_id: UUID (PK),
  email: VARCHAR(255, UNIQUE, NOT NULL),
  password_hash: VARCHAR(255, NOT NULL),
  created_at: TIMESTAMP DEFAULT NOW(),
  updated_at: TIMESTAMP DEFAULT NOW(),
  is_active: BOOLEAN DEFAULT TRUE
}
```

### JWT Payload

```
{
  sub: user_id,
  email: user_email,
  iat: issued_at_unix,
  exp: expiration_unix,
  aud: "popolilo-api"
}
```

---

## Non-Functional Requirements

### Performance

- **Login latency:** < 500ms (bcrypt hash + DB query)
- **GET /me latency:** < 100ms (token validation + DB query)
- **Token validation:** < 10ms (JWT sig check only)

### Security

- **Password storage:** bcrypt, salt 10, never plaintext
- **Token transmission:** HTTPS only + Bearer scheme
- **Token secret:** 256-bit, stored in .env (not in code)
- **Rate limiting:** 5 attempts / 15 min per IP on /login
- **No CORS:** API responses include CORS headers controlados

### Availability

- **Auth service uptime:** 99.9% SLA
- **Graceful degradation:** 500 error on auth service fail (no fallback)

### Observability

- **Logging:** Login attempts (success/fail), token generation
- **Metrics:** Auth success rate, avg latency, rate limit hits
- **Tracing:** Request ID propagation (future)

---

## Success Criteria

### Functional Acceptance

- [ ] Endpoint POST /register: crear usuario, validar email/password
- [ ] Endpoint POST /login: generar JWT, rate limit funcional
- [ ] Endpoint GET /me: retornar user info con token válido
- [ ] Error handling: 401/409/429/400 status codes correctos
- [ ] Token expires después 24h: cliente recibe 401

### Measurable Outcomes (Non-Functional)

- [ ] Login latency < 500ms (p95)
- [ ] Token validation < 10ms
- [ ] Rate limit: exactamente 5 intentos/15min por IP
- [ ] bcrypt verify: < 200ms en máquina típica

### Test Coverage

- [ ] Unit: Password hashing, token generation, validation
- [ ] Integration: Full /register, /login, /me flows
- [ ] Load: 100 concurrent login requests
- [ ] Security: JWT tampering detection, rate limit bypass attempts

---

## Edge Cases & Error Handling

- **Token expirado:** Retorn 401, mensaje "Token expired"
- **Token inválido/corrupto:** Retorn 401, mensaje "Invalid token"
- **Email duplicado:** Retorn 409, mensaje "Email already registered"
- **Password débil:** Retorn 400, mensaje con requisitos
- **Email inválido:** Retorn 400, mensaje formato incorrecto
- **Rate limit excedido:** Retorn 429, header `Retry-After: 900`
- **Server error en hash:** Retorn 500 (no exponer detalles)

---

## Constraints & Tradeoffs

| Constraint | Value | Rationale |
|-----------|-------|-----------|
| Token lifetime | 24h | Balance entre seguridad y UX (no refrescar constantemente) |
| bcrypt salt | 10 | Estándar: ~100ms en servidor moderno, seguro |
| No refresh tokens v1 | Defer to v2 | Reduce complejidad, suficiente para MVP |
| No email verification | Defer to v2 | Reduce friction, seguido post-launch |
| Password min length | 8 chars | OWASP recomendación mínima |
| Rate limit | 5/15min | Deterrent sin bloquear usuarios legítimos |

---

## Integration & External Dependencies

### Database

- **Type:** PostgreSQL (asumido, si no especificado)
- **Library:** psycopg2 (Python) o equivalente
- **Connection:** Pool de conexiones (10-20 conn)

### Crypto Library

- **bcrypt:** Para password hashing
- **JWT:** Para token generation/validation (PyJWT o similar)
- **Secrets/OS:** Para random token generation

### Environment

- **JWT_SECRET:** 256-bit hex string (env var)
- **BCRYPT_SALT_ROUNDS:** 10 (constant)
- **DB_CONNECTION_STRING:** (env var)
- **LOG_LEVEL:** debug/info/warn/error (env var)

---

## Glossary & Terminology

| Term | Definition |
|------|-----------|
| **Access Token** | JWT de corta vida que autoriza requests al API |
| **Password Hash** | Resultado bcrypt(password, salt), nunca plaintext |
| **Rate Limit** | Máx 5 intentos login / 15 min por IP origen |
| **Bearer Token** | Formato `Authorization: Bearer <token>` |
| **JWT Payload** | Claims dentro del token: sub, exp, iat, email, aud |
| **Token Expiration** | 24 horas desde emisión; cliente debe re-login |

---

## Implementation Notes

- **Framework:** Asumir FastAPI (Python) o similar (TBD en plan)
- **Package versions:** TBD en plan (bcrypt>=4.0, PyJWT>=2.6)
- **No external auth service:** Auth logic in-app (no Auth0, Cognito, etc. para v1)

---

## Next Steps

1. **Inmediato:** Responder P5 (DTOs estructura)
2. **Post-Clarify:** Ejecutar `/speckit.plan` para generar plan de implementación
3. **Post-Plan:** Crear tasks e iniciar sprint de coding

