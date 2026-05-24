# Pattern: FastAPI Routers + Dependency Injection
# Cada request = nueva transacción BD + nueva sesión SQLAlchemy.
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.domain.exceptions import UserAlreadyExistsError, InvalidCredentialsError
from src.infrastructure.persistence.database import get_db
from src.application.auth.auth_service import AuthService
from src.application.auth.jwt_service import JWTService
from src.infrastructure.persistence.user_repository import UserRepository
from src.infrastructure.config import settings
from src.presentation.schemas.auth_schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    MeResponse
)
from src.presentation.dependencies.auth import get_current_user


router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency que crea AuthService con sus dependencias."""
    repo = UserRepository(db)
    jwt_service = JWTService(settings)
    return AuthService(repo, jwt_service)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"]
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> RegisterResponse:
    """Endpoint para registrar nuevo usuario.

    Args:
        request: RegisterRequest con email y password
        auth_service: Inyectado vía Depends

    Returns:
        RegisterResponse con user_id

    Raises:
        400: Si email/password inválidos
        409: Si email ya existe
    """
    try:
        result = auth_service.register(request.email, request.password)
        return RegisterResponse(user_id=result["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    tags=["auth"]
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """Endpoint para login de usuario.

    Args:
        request: LoginRequest con email y password
        auth_service: Inyectado vía Depends

    Returns:
        LoginResponse con access_token

    Raises:
        400: Si email inválido
        401: Si credenciales incorrectas
    """
    try:
        result = auth_service.login(request.email, request.password)
        return LoginResponse(
            access_token=result["access_token"],
            token_type=result["token_type"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )


@router.get(
    "/me",
    response_model=MeResponse,
    tags=["auth"]
)
async def get_me(user_id: str = Depends(get_current_user)) -> MeResponse:
    """Endpoint protegido para obtener datos del usuario autenticado.

    Args:
        user_id: Inyectado vía get_current_user dependency

    Returns:
        MeResponse con user_id

    Raises:
        401: Si token inválido/expirado/faltante
    """
    return MeResponse(user_id=user_id)
