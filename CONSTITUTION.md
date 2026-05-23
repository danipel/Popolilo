# Constitución — Principios No Negociables

Este documento formaliza los principios que rigen el desarrollo del **Sistema Distribuido Concurrente** (Popolilo).

---

## 1. Clean Code

**Definición:** Código que expresa intención claramente, es fácil de mantener y resistente a bugs.

### Reglas
- **Nombres claros:** Variables y funciones reflejan su propósito; evitar `x`, `temp`, `data`.
- **Funciones pequeñas:** Máximo 20 líneas; una responsabilidad por función.
- **DRY (Don't Repeat Yourself):** Refactorizar al detectar 3+ líneas similares.
- **Errores específicos:** Excepciones que comuniquen qué salió mal, no genéricas.

### Ejemplos ✓
```python
# ✓ Bien: nombre claro, responsabilidad única
def extract_sentiment(text: str) -> Tuple[str, float]:
    if not text:
        raise ValueError("text cannot be empty")
    return sentiment_model.predict(text)

# ✗ Mal: genérico, múltiples responsabilidades
def process(x):
    return model.predict(x)
```

---

## 2. Patrones de Diseño

**Definición:** Soluciones arquitectónicas repetibles que resuelven problemas conocidos.

### Regla
- Usar solo patrones documentados en `Specs.md § 7 (Matriz de patrones)`.
- Documentar con comentario: `# Pattern: <Nombre>`.

### Aplicación
```python
# Pattern: Repository
class UserRepository(IUserRepository):
    """Abstrae persistencia de User; permite cambiar BD sin tocar dominio."""
    pass

# Pattern: Factory
def create_user(email: str, password: str) -> User:
    """Encapsula validación y hash del password."""
    pass

# Pattern: Observer
def emit_job_completed_event(job_id: UUID) -> None:
    """Desacopla procesamiento de notificación."""
    pass
```

---

## 3. DDD en Carpetas

**Definición:** Estructura que aísla el dominio crítico de detalles técnicos.

### Jerarquía
```
src/
├── domain/          ← Entidades, Value Objects, Eventos, Interfaces (SIN deps a infra)
├── application/     ← Servicios, Casos de Uso (depende de domain)
├── infrastructure/  ← Repositorios, Workers, Colas, BD (depende de domain + app)
└── presentation/    ← Routers, DTOs, Middleware (depende de app)
```

### Regla de Oro
**`domain/` NUNCA importa de `infrastructure/`, `presentation/` ni dependencias externas.**

### Ejemplos ✓
```python
# ✓ domain/entities/job.py
from dataclasses import dataclass
from uuid import UUID

@dataclass
class Job:
    job_id: UUID
    status: str
    # SIN SQLAlchemy, SIN FastAPI, SIN imports externos

# ✓ infrastructure/persistence/job_repository.py
from sqlalchemy.orm import Session
from domain.entities.job import Job

class JobRepository(IJobRepository):
    def __init__(self, session: Session):
        self.session = session
    # Usa Job del dominio, pero domain/ no conoce SQLAlchemy
```

---

## 4. Concurrencia Thread-Safe

**Definición:** Garantizar que datos compartidos entre hilos se acceden de forma segura.

### Reglas
1. **Lock en toda estructura compartida** → `threading.Lock` o `threading.RLock`.
2. **Colas con `queue.Queue`** → Productor-Consumidor (ya thread-safe).
3. **Workers verifican cancelación** → `threading.Event` antes de procesar.
4. **Contadores atómicos en BD** → `UPDATE + SELECT FOR UPDATE` o transacciones.
5. **Primitivas específicas:**
   - `Barrier` → Sincronización global de N hilos.
   - `Event` → Señalización (un hilo espera, otro dispara).
   - `Semaphore` → Limitar acceso concurrente a N recursos.

### Ejemplo: Lock
```python
# Pattern: Singleton
class MetricsCollector:
    _lock = threading.Lock()
    _instance = None
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance
    
    def record_metric(self, key: str, value: float):
        with self._lock:  # Proteger acceso a self._data
            self._data[key] = value
```

### Ejemplo: Cancelación
```python
# Pattern: CancellationToken
class Worker(Thread):
    def run(self):
        while not self.cancel_event.is_set():
            text = self.queue.get()
            if self.cancel_event.is_set():  # Verificar antes de procesar
                break
            self.process(text)
```

---

## 5. No Testing

El foco está en **arquitectura correcta y concurrencia segura**, no en cobertura de tests.

---

## Checklist de Implementación

Antes de hacer commit:

- [ ] **Clean Code:** Ninguna función > 20 líneas, nombres claros.
- [ ] **Patrones:** ¿Qué patrón usa? ¿Está documentado?
- [ ] **DDD:** `domain/` no importa de `infrastructure/`.
- [ ] **Thread-safe:** ¿Hay variables compartidas? ¿Con lock?
- [ ] **Cancelación:** ¿Los workers verifican `Event`?
- [ ] **BD para contadores:** ¿Uso `SELECT FOR UPDATE`?

---

## Referencias

- **Specs.md** — Historias, contratos de API, matriz de patrones.
- **Arquitectura Clean** — Independencia tecnológica, testabilidad.
- **Python threading** — Queue, Lock, Event, Barrier, Semaphore.
