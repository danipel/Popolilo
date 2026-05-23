# Sistema Distribuido Concurrente — Especificación Técnica
> Spec-Driven Development · Clean Architecture · Python / FastAPI

---

## 1. Visión General

**Objetivo:** Diseñar e implementar un sistema distribuido concurrente que procese tareas en segundo plano garantizando consistencia, escalabilidad y desacoplamiento arquitectónico.

### Competencias clave a demostrar
- Diseño cliente-servidor y API REST profesional
- Arquitectura Limpia (Clean Architecture) + DDD básico
- Patrones de diseño aplicados (Repository, Factory, Strategy, Observer, etc.)
- Concurrencia real: locks, eventos, colas, semáforos, barreras
- Sistemas escalables con workers paralelos

---

## 2. Arquitectura General

### Estilo: Clean Architecture

```
┌─────────────────────────────────────────────────┐
│  PRESENTATION  (FastAPI, WebSocket, DTOs)        │
├─────────────────────────────────────────────────┤
│  APPLICATION   (Services, Use Cases)             │
│  AuthService · JobService · ProcessTextService   │
│  ReportService · NotificationService             │
├─────────────────────────────────────────────────┤
│  INFRASTRUCTURE (SQL, WorkerPool, Queue,         │
│  WebSocketManager, MetricsCollector)             │
├─────────────────────────────────────────────────┤
│  DOMAIN  (Entities, Value Objects, Interfaces,   │
│  Events)                                         │
│  User · Job · TextResult · Email · Password      │
│  JobCompletedEvent · IRepository interfaces      │
└─────────────────────────────────────────────────┘
```

### Modelo de Concurrencia

| Tipo de tarea | Estrategia | Justificación |
|---|---|---|
| CPU-bound (análisis NLP) | `multiprocessing` | Evita el GIL, paralelismo real |
| I/O-bound (API, WebSocket) | `threading` | Bajo costo, comparte estado |

### Primitivas de sincronización usadas
- `threading.Lock` / `RLock` — secciones críticas
- `threading.Event` — señalización entre hilos
- `queue.Queue` / `PriorityQueue` — cola thread-safe
- `threading.Semaphore` — control de acceso concurrente
- `threading.Barrier` — punto de sincronización global

---

## 3. Modelo de Dominio

### Entidades

```python
# User
- id: UUID
- email: Email          # Value Object — único
- password: Password    # Value Object — hasheado

# Job
- job_id: UUID
- user_id: UUID
- status: Enum[pending, processing, completed, failed, cancelled]
- texts: List[Text]
- priority: int         # menor = mayor prioridad
- created_at: datetime

# Text
- id: UUID
- content: str
- language: Optional[str]
- sentiment: Optional[Enum[POSITIVE, NEGATIVE, NEUTRAL]]
- score: Optional[float]  # -1.0 a 1.0

# TextResult
- text_id: UUID
- job_id: UUID
- label: Enum[POSITIVE, NEGATIVE, NEUTRAL]
- score: float
```

### Value Objects

```python
# Email — validación de formato, unicidad
# Password — mínimo 8 caracteres, 1 mayúscula, 1 número, almacenado hasheado
```

### Eventos de dominio

```python
# JobCompletedEvent
- job_id: UUID
- user_id: UUID
- results_url: str
- timestamp: datetime
```

---

## 4. Historias de Usuario y Especificaciones

---

### Historia 1 — Autenticación con JWT

**Como** analista de datos,  
**quiero** registrarme e iniciar sesión con email y contraseña,  
**para** obtener un token JWT que me permita acceder a los endpoints protegidos.

#### Reglas de negocio
- El email es único en el sistema.
- La contraseña requiere: mínimo 8 caracteres, al menos 1 mayúscula y 1 número.
- El token JWT expira después de 24 horas.
- El password nunca se almacena en texto plano.

#### Casos de uso
1. `RegisterUser(email, password) → User`
2. `LoginUser(email, password) → JWT`
3. `VerifyToken(token) → UserContext` _(middleware, cada request protegido)_

#### Contratos de API

```
POST /register
  Body:    { "email": string, "password": string }
  Returns: 201 { "user_id": UUID }
  Errors:  400 (validación), 409 (email ya existe)

POST /login
  Body:    { "email": string, "password": string }
  Returns: 200 { "access_token": string, "token_type": "bearer" }
  Errors:  401 (credenciales inválidas)
```

#### Patrones aplicados
| Patrón | Justificación |
|---|---|
| Repository | Abstrae la BD; permite cambiar de SQLite a PostgreSQL sin tocar el dominio |
| Factory | Encapsula validación de email y hashing al crear un `User` |
| Strategy | Permite cambiar el algoritmo de hash (bcrypt → argon2) sin modificar el dominio |

#### Concurrencia
`AuthService` debe ser **thread-safe**: múltiples requests de login concurrentes. Usar `RLock` si existe caché interna de sesiones.

#### Criterios de aceptación
- [ ] `POST /register` retorna `201` con `user_id`
- [ ] `POST /login` retorna JWT válido
- [ ] Endpoints protegidos retornan `401` sin token o con token inválido
- [ ] El password no se puede leer en la BD

---

### Historia 2 — Envío de tareas (Productor-Consumidor)

**Como** analista,  
**quiero** enviar hasta 100 textos a la vez y recibir inmediatamente un `job_id`,  
**para** que el sistema procese en segundo plano sin bloquear mi cliente.

#### Reglas de negocio
- Máximo 100 textos por lote; si se excede → rechazar con `400`.
- La respuesta debe ser `202 Accepted` con el `job_id` (no esperar procesamiento).
- El tiempo de respuesta debe ser < 100 ms.

#### Casos de uso
1. `CreateJob(user_id, texts[]) → Job`
2. `EnqueueTexts(job) → void` _(publica en la cola compartida)_

#### Contrato de API

```
POST /jobs
  Headers: Authorization: Bearer <token>
  Body:    { "texts": ["texto1", "texto2", ...] }   # max 100 items
  Returns: 202 { "job_id": UUID, "status": "pending" }
  Errors:  400 (lote vacío o > 100), 401
```

#### Patrones aplicados
| Patrón | Justificación |
|---|---|
| Producer-Consumer | Desacopla velocidad de llegada de solicitudes de la velocidad de procesamiento |
| Command | `TextAnalysisCommand` encapsula cada solicitud de análisis individual |
| Repository | `JobRepository` aísla la persistencia del `Job` |

#### Concurrencia
- `queue.Queue` es thread-safe por diseño.
- N workers iniciados al arranque del servidor esperan en la cola.
- `threading.Event` señala cierre ordenado del servidor.

#### Criterios de aceptación
- [ ] Respuesta < 100 ms aunque la cola tenga carga
- [ ] El job aparece con `status: pending` inmediatamente
- [ ] Los workers comienzan a consumir sin bloquear nuevas peticiones
- [ ] Lote de > 100 textos es rechazado con `400`

---

### Historia 3 — Procesamiento concurrente con Workers

**Como** analista,  
**quiero** que los textos se procesen en paralelo con múltiples workers,  
**para** obtener resultados rápidos sin perder ningún texto.

#### Reglas de negocio
- Cada worker procesa un texto a la vez.
- Resultado de cada texto: `POSITIVE | NEGATIVE | NEUTRAL` y score `[-1.0, 1.0]`.
- Si un texto falla → marcarlo como `failed`, continuar con el siguiente.
- Un `Job` es `completed` cuando todos sus textos están procesados (éxito o fallo).

#### Casos de uso
1. `ConsumeText(queue) → Text`
2. `AnalyzeText(text) → TextResult`
3. `UpdateJobProgress(job_id, processed_count) → void` _(atómico)_

#### Patrones aplicados
| Patrón | Justificación |
|---|---|
| Worker Pool | Reutiliza N hilos/procesos fijos, evita el costo de crearlos por tarea |
| Observer (opcional) | Job notifica cuando su contador llega a 0 → cambia a `completed` |
| Singleton | Cola y pool son instancias únicas compartidas por todos los workers |

#### Concurrencia — diseño del contador atómico

```
Opción A (threads): threading.Lock en contador en memoria
Opción B (procesos): multiprocessing.Value con Lock
Opción C (BD, recomendada):
  - Cada worker ejecuta:
      UPDATE texts SET status='done' WHERE id=?
      SELECT COUNT(*) FROM texts WHERE job_id=? AND status='pending'
  - Si count == 0 → UPDATE jobs SET status='completed'
  - Protegido por transacción ACID o SELECT FOR UPDATE
```

#### Criterios de aceptación
- [ ] Al menos 4 workers procesan concurrentemente
- [ ] Tiempo total de 100 textos @ 50 ms ≈ `(100 × 0.05) / N` segundos
- [ ] El `Job` pasa a `completed` sin quedarse en `processing`
- [ ] Ningún texto se procesa dos veces ni se pierde

---

### Historia 4 — Consulta de resultados y reportes

**Como** analista,  
**quiero** consultar el estado de un job y obtener un reporte agregado paginado,  
**para** evaluar rápidamente el sentimiento general del lote.

#### Reglas de negocio
- Si el job está `processing` → retornar `status` + `processed / total`.
- El reporte agregado es **inmutable** una vez completado.
- Paginación obligatoria: `page`, `per_page`.

#### Casos de uso
1. `GetJobStatus(job_id) → JobStatusDTO`
2. `GetTextResults(job_id, page, per_page) → Page<TextResultDTO>`
3. `GetJobReport(job_id) → ReportDTO`

#### Contratos de API

```
GET /jobs/{job_id}
  Returns: 200 { "job_id", "status", "processed": int, "total": int }
  Errors:  404, 403

GET /jobs/{job_id}/results?page=1&per_page=20
  Returns: 200 { "items": [...], "page", "per_page", "total" }

GET /jobs/{job_id}/report
  Returns: 200 {
    "positive_count": int,
    "negative_count": int,
    "neutral_count": int,
    "average_score": float
  }
```

#### Patrones aplicados
| Patrón | Justificación |
|---|---|
| DTO + Mapper | Evita exponer entidades de dominio directamente |
| Query Object | Encapsula lógica de paginación y filtros |
| Cache (lru_cache / Redis) | Reportes de jobs completados no cambian; se cachean |

#### Criterios de aceptación
- [ ] Tiempo de respuesta < 200 ms
- [ ] Paginación funciona correctamente
- [ ] Reporte solo disponible cuando `status == completed`
- [ ] Índices en BD sobre `job_id` y `status`

---

### Historia 5 — Notificaciones asíncronas por WebSocket

**Como** analista,  
**quiero** recibir una notificación automática cuando mi job termine,  
**para** no tener que hacer polling constante.

#### Reglas de negocio
- El cliente puede tener una conexión WebSocket activa o un callback HTTP registrado.
- La notificación contiene `job_id` y URL de resultados.
- Si falla el callback HTTP → reintentar hasta 3 veces con backoff exponencial.
- La notificación se dispara **exactamente una vez** por job.

#### Casos de uso
1. `RegisterWebSocket(user_id, connection) → void`
2. `NotifyJobCompleted(event: JobCompletedEvent) → void`
3. `RegisterWebhook(user_id, callback_url) → void` _(opcional)_

#### Contratos de API

```
WS  /ws
  Connect con token JWT
  Receive: { "event": "job_completed", "job_id": UUID, "results_url": string }

POST /webhooks   (opcional)
  Body:    { "callback_url": string }
  Returns: 201 { "webhook_id": UUID }
```

#### Patrones aplicados
| Patrón | Justificación |
|---|---|
| Observer / Event-Driven | `JobCompletedEvent` desacopla el procesamiento de la notificación |
| Singleton | `WebSocketManager` mantiene el diccionario de conexiones activas |
| Circuit Breaker | Evita saturar destinos de callback que fallan repetidamente |

#### Concurrencia
- `WebSocketManager` usa `threading.Lock` para agregar/remover clientes de forma segura.
- Comunicación workers (procesos) → WebSocketManager (thread): usar `multiprocessing.Queue` o un thread dedicado como puente.

#### Criterios de aceptación
- [ ] El cliente conectado a WS recibe notificación al completarse su job
- [ ] La notificación llega exactamente una vez
- [ ] Callback HTTP se reintenta 3 veces con backoff si falla

---

### Historia 6 — Cancelación y priorización de tareas

**Como** cliente premium,  
**quiero** cancelar un job pendiente y que mis jobs tengan mayor prioridad,  
**para** controlar mis recursos y costos.

#### Reglas de negocio
- Solo el propietario del job puede cancelarlo.
- No se puede cancelar un job ya `completed`.
- Usuarios premium tienen prioridad menor (número más bajo = mayor prioridad).
- Cancelación de job en ejecución: el worker verifica un flag antes de cada texto.

#### Casos de uso
1. `CancelJob(job_id, user_id) → void`
2. `EnqueueWithPriority(job, priority) → void`
3. `CheckCancelled(job_id) → bool` _(consultado por workers en cada iteración)_

#### Contrato de API

```
DELETE /jobs/{job_id}
  Returns: 200 { "message": "cancelled" }
  Errors:  403 (no es el dueño), 409 (ya completado), 404
```

#### Diseño de la cola con prioridad

```python
# Elemento de la PriorityQueue:
(priority: int, timestamp: float, job: Job)
# Ej: (0, 1720000000.0, job_premium) tiene mayor prioridad que (1, ...)
```

#### Patrones aplicados
| Patrón | Justificación |
|---|---|
| Priority Queue | Jobs con menor número se procesan antes |
| Command + CancellationToken | `threading.Event` por job; el worker lo verifica cooperativamente |

#### Criterios de aceptación
- [ ] `DELETE /jobs/{job_id}` retorna `200` si se cancela exitosamente
- [ ] Un job cancelado nunca es procesado
- [ ] Jobs premium se procesan antes que jobs de usuarios gratuitos
- [ ] El worker verifica cancelación antes de analizar cada texto

---

### Historia 7 — Dashboard de métricas administrativas

**Como** administrador,  
**quiero** consultar métricas del sistema en tiempo real,  
**para** detectar cuellos de botella y decidir cuándo escalar.

#### Reglas de negocio
- Solo accesible por usuarios con rol `admin`.
- Las métricas no modifican el dominio.
- Retraso máximo de 5 segundos en la actualización.

#### Métricas requeridas
- Tamaño actual de la cola
- Número de workers activos
- Jobs completados por minuto
- Tiempo promedio de procesamiento por texto (promedio móvil)

#### Contrato de API

```
GET /admin/metrics
  Headers: Authorization: Bearer <admin_token>
  Returns: 200 {
    "queue_size": int,
    "active_workers": int,
    "jobs_per_minute": float,
    "avg_processing_time_ms": float
  }
  Errors: 403
```

#### Patrones aplicados
| Patrón | Justificación |
|---|---|
| Singleton | Única instancia de `MetricsCollector` |
| Observer inverso | Workers reportan su estado al colector al iniciar/finalizar |
| Snapshot | Se captura un instante consistente de las métricas con lock |

#### Concurrencia
- `MetricsCollector` usa `threading.Lock` para todas las actualizaciones.
- Con procesos: usar `multiprocessing.Manager` o una queue de eventos dedicada.

#### Criterios de aceptación
- [ ] Endpoint devuelve las 4 métricas en JSON
- [ ] Retraso máximo de 5 s respecto al estado real
- [ ] La recolección de métricas no degrada el rendimiento del sistema

---

## 5. Casos especiales — Historias de plataforma

### Historia 8 — LMS: Sistema de entregas de estudiantes

#### 8a. Cola de corrección concurrente
| Ítem | Detalle |
|---|---|
| Cola | `queue.Queue(maxsize=10)` |
| Productores | 15 estudiantes simulados como hilos |
| Workers | N=3 `AssignmentWorker(Thread)` |
| Bloqueo | `put(block=True)` — el productor espera si la cola está llena |
| Payload | `{ student_id, course_id, assignment_id, answer_text }` |
| Resultado | Nota aleatoria 0–100 almacenada en `GradeRepository` con `RLock` |

**Criterios de aceptación**
- [ ] `GradeRepository` es thread-safe con `Lock` o `RLock`
- [ ] 15 entregas se procesan completamente con 3 workers
- [ ] El productor bloquea correctamente cuando la cola está llena

#### 8b. Lector-Escritor para notas (Reader-Writer Lock)

**Requisito:** Permitir lectura concurrente pero exclusión mutua en escritura. Escritores tienen prioridad (evitar inanición).

```
Actores: 10 lectores (estudiantes), 2 escritores (profesores)
Lectores: leen nota aleatoria × 5
Escritores: actualizan nota × 3
```

**Criterios de aceptación**
- [ ] `ReadWriteLock` implementa `acquire_read / release_read / acquire_write / release_write`
- [ ] Múltiples lectores concurrentes permitidos
- [ ] Un escritor excluye a todos los demás
- [ ] Los escritores no sufren inanición

#### 8c. Inicio sincronizado de examen (Barrier)

**Requisito:** 5 estudiantes deben estar listos antes de que el examen comience para todos simultáneamente.

```python
barrier = threading.Barrier(5)
# Cada estudiante: llega en momento aleatorio → barrier.wait() → comienza examen
```

**Criterios de aceptación**
- [ ] Ningún estudiante comienza antes de que los 5 estén listos
- [ ] La impresión de "comienza el examen" es simultánea para todos

---

### Historia 9 — Pagos internacionales

#### 9a. Cola de procesamiento de pagos
| Ítem | Detalle |
|---|---|
| Cola | `queue.Queue(maxsize=20)` |
| Productores | 15 solicitudes de pago |
| Workers | N=3 `PaymentWorker(Thread)` |
| Payload | `{ merchant_id, amount, currency, method_type }` |
| Procesamiento | Validación antifraude + comisión + gateway simulado |
| Resultado | Actualiza `BalanceRepository` (thread-safe con `Lock`) |

**Salida esperada en consola:**
```
[Productor 1] Encolando pago de merchant 101 por 50.00 USD
[Worker A] Procesando pago 1: merchant 101, método tarjeta... Comisión 2.5 USD
[Worker A] Pago completado. Nuevo saldo de merchant 101: 47.50 USD
```

**Criterios de aceptación**
- [ ] `BalanceRepository` es thread-safe
- [ ] 15 pagos se procesan sin pérdidas ni duplicados
- [ ] La salida es eventual y consistente (no necesariamente secuencial)

#### 9b. Lector-Escritor para tasas de cambio

**Requisito:** `PaymentConfig` es leída frecuentemente y actualizada periódicamente. Escritores tienen prioridad.

```
Actores: 10 lectores (consultan tasa × 5), 2 escritores (actualizan × 3)
```

**Criterios de aceptación**
- [ ] `ReadWriteLock` con prioridad a escritores usando `threading.Condition`
- [ ] Demostración de exclusión y prioridad en el script de prueba

#### 9c. Liquidación diaria sincronizada (Barrier)

**Requisito:** 3 hilos (EUR, GBP, JPY → USD) deben terminar su conversión antes de calcular el total.

```python
barrier = threading.Barrier(3)
# Cada hilo: convierte montos → barrier.wait() → hilo principal imprime total USD
```

**Criterios de aceptación**
- [ ] El total en USD solo se imprime cuando los 3 hilos terminaron
- [ ] Uso correcto de `threading.Barrier(3)`

---

## 6. Estructura de carpetas sugerida

```
src/
├── domain/
│   ├── entities/          # User, Job, Text, TextResult
│   ├── value_objects/     # Email, Password
│   ├── events/            # JobCompletedEvent
│   └── interfaces/        # IUserRepository, IJobRepository
├── application/
│   ├── auth/              # AuthService, JwtService
│   ├── jobs/              # JobService, ProcessTextService
│   ├── reports/           # ReportService
│   └── notifications/     # NotificationService
├── infrastructure/
│   ├── persistence/       # SQLAlchemy repos, models
│   ├── workers/           # WorkerPool, Worker, WorkerManager
│   ├── queue/             # QueueManager (Queue / PriorityQueue)
│   ├── websocket/         # WebSocketManager
│   └── metrics/           # MetricsCollector
└── presentation/
    ├── routers/           # auth, jobs, admin
    ├── schemas/           # DTOs de entrada/salida
    └── dependencies/      # auth middleware, db session
tests/
├── unit/
├── integration/
└── load/
```

---

## 7. Matriz de patrones de diseño

| Patrón | Dónde se usa | Historia |
|---|---|---|
| Repository | User, Job, TextResult | 1, 2, 3, 4 |
| Factory | Creación de `User` con validaciones | 1 |
| Strategy | Algoritmo de hashing intercambiable | 1 |
| Producer-Consumer | Cola API → Workers | 2, 3 |
| Command | `TextAnalysisCommand`, `CancellationToken` | 2, 6 |
| Worker Pool | `ProcessPoolExecutor` / N threads fijos | 3 |
| Observer / Event-Driven | `JobCompletedEvent` → `NotificationService` | 5 |
| Singleton | Cola, WorkerPool, WebSocketManager, MetricsCollector | 2, 5, 7 |
| Circuit Breaker | Callbacks HTTP con reintentos | 5 |
| Priority Queue | Priorización de jobs premium | 6 |
| ReadWriteLock | GradeRepository, PaymentConfig | 8b, 9b |
| Barrier | Inicio de examen, liquidación de pagos | 8c, 9c |
| DTO + Mapper | Separar API de entidades de dominio | 4 |
| Query Object | Paginación y filtros reutilizables | 4 |
| Snapshot | Lectura consistente de métricas | 7 |

---

## 8. Checklist de entrega

### Funcional
- [ ] H1: Registro y login con JWT funcionando
- [ ] H2: POST /jobs retorna 202 en < 100 ms
- [ ] H3: Mínimo 4 workers concurrentes, sin pérdida de textos
- [ ] H4: 3 endpoints de consulta con respuesta < 200 ms
- [ ] H5: Notificación WebSocket al completar job
- [ ] H6: Cancelación y priorización funcionando
- [ ] H7: GET /admin/metrics retorna las 4 métricas

### Concurrencia
- [ ] Sin condiciones de carrera en el contador de textos
- [ ] Cola thread-safe verificada con carga concurrente
- [ ] ReadWriteLock correcto (no inanición de escritores)
- [ ] Barrier sincroniza correctamente los N hilos

### Arquitectura
- [ ] Capas de Clean Architecture respetadas (sin dependencias hacia afuera)
- [ ] Todos los repositorios con interfaz en dominio
- [ ] DTOs definidos para todos los endpoints
- [ ] Tests unitarios de `AuthService` y `JobService`
