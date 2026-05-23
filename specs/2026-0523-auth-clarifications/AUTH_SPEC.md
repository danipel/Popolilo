# Autenticación - Decisiones Técnicas

## Token Strategy

**Decision P4:** Solo access tokens 24h ahora, refresh tokens en v2

- **Access Token:** JWT de corta vida (24 horas)
- **Estrategia de refresco:** Diferida a v2
- **Rationale:** Reduce complejidad en v1; permite validación rápida; refresh flow se implementa en iteración siguiente

### Implantación

#### Access Token (JWT)
- **Tiempo de expiración:** 24 horas
- **Payload:**
  - `sub`: user_id
  - `iat`: issued at
  - `exp`: expiration (iat + 86400)
  - `email`: user email
- **Signing:** HS256 con secret configurado en env

#### Flujo de Autenticación
1. POST /register: Crear usuario
2. POST /login: Validar credenciales → generar JWT de 24h
3. GET /me: Validar token vigente → retornar datos usuario
4. Token expirado: Cliente recibe 401 → vuelve a login (v1)

#### Future (v2)
- Refresh tokens con rotación
- Sliding window expirations
- Token revocation list (si es necesario)

---

## DTOs - Estructura de Respuestas

**Decision P5:** [PENDIENTE - En evaluación]

Opciones bajo evaluación:
- **Registro:** Determinar campos en respuesta
- **Login:** Incluir `expires_in` para renovación proactiva
- **GET /me:** Retornar perfil completo o información mínima

Status: Aguardando respuesta usuario

