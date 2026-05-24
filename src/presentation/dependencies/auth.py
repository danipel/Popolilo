# Pattern: FastAPI Dependency Injection + Middleware
# FastAPI injeca nueva instancia por request → sin race conditions.
from fastapi import Request, HTTPException, Depends
from jose import JWTError, ExpiredSignatureError
from src.application.auth.jwt_service import JWTService
from src.infrastructure.config import settings


def get_jwt_service() -> JWTService:
    """Dependency que retorna instancia de JWTService."""
    return JWTService(settings)


def get_current_user(
    request: Request,
    jwt_service: JWTService = Depends(get_jwt_service)
) -> str:
    """Dependency que extrae y valida JWT del header.

    Args:
        request: FastAPI Request
        jwt_service: Inyectado vía Depends

    Returns:
        user_id extraído del token

    Raises:
        HTTPException: 401 si token inválido/expirado/faltante
    """
    # Extraer header Authorization
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )

    # Parsear "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )

    token = parts[1]

    try:
        # Verificar token
        payload = jwt_service.verify(token)
        user_id = jwt_service.extract_user_id(payload)
        return user_id
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
