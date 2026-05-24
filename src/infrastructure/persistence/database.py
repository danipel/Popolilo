# SQLAlchemy Database Configuration
# Thread-safety: PostgreSQL es ACID compliant.
# Cada request obtiene su propia conexión del pool.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from src.infrastructure.config import settings

# Crear engine con configuración para desarrollo
# NullPool en desarrollo (sin persistencia de conexiones entre requests)
# QueuePool en producción (reutiliza conexiones)
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False
)

# Crear session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base declarativa para modelos ORM
Base = declarative_base()


def get_db():
    """Dependency para FastAPI. Retorna una Session por request.

    Uso:
        @router.get("/")
        def get_something(db: Session = Depends(get_db)):
            ...

    Thread-safety: FastAPI injeta nueva instancia Session por request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
