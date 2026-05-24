# Pattern: DTO (Data Transfer Object, Pydantic)
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """Esquema para solicitud de registro."""
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Password (mín 8 chars, 1 mayúscula, 1 número)")


class RegisterResponse(BaseModel):
    """Esquema para respuesta de registro."""
    user_id: str = Field(..., description="UUID del usuario creado")


class LoginRequest(BaseModel):
    """Esquema para solicitud de login."""
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Esquema para respuesta de login."""
    access_token: str = Field(..., description="JWT token")
    token_type: str = Field(default="bearer", description="Tipo de token")


class MeResponse(BaseModel):
    """Esquema para respuesta del endpoint /me."""
    user_id: str = Field(..., description="UUID del usuario autenticado")
