# Pattern: FastAPI Application + Dependency Container
# FastAPI Dependency Injection maneja thread-safety:
# Cada request → nueva instancia de dependencias.
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from src.infrastructure.persistence.database import engine, Base
from src.infrastructure.persistence.models import UserModel
from src.presentation.routers.auth import router as auth_router


# Crear tablas en BD (si no existen)
Base.metadata.create_all(bind=engine)

# Instancia FastAPI
app = FastAPI(
    title="Popolilo Auth API",
    version="1.0.0",
    description="Autenticación con JWT + DDD + Clean Architecture"
)


# Registrar routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])


@app.get("/health", tags=["health"])
async def health():
    """Endpoint de health check (sin autenticación)."""
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador global para HTTPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejador global para excepciones inesperadas."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
