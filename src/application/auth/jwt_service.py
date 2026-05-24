# Pattern: Service (Stateless, thread-safe)
# JWTService es stateless: no almacena estado mutable.
# Métodos puros → inherentemente thread-safe.
import time
from jose import jwt, JWTError, ExpiredSignatureError
from src.infrastructure.config import Settings


class JWTService:
    """Servicio para generar y verificar JWT tokens."""

    def __init__(self, settings: Settings):
        """Constructor inyecta configuración.

        Args:
            settings: Settings instance con JWT config
        """
        self.settings = settings

    def generate(
        self,
        user_id: str,
        email: str,
        role: str = "user"
    ) -> str:
        """Genera JWT token con claims RFC 7519.

        Args:
            user_id: UUID del usuario como string
            email: Dirección de email del usuario
            role: Rol del usuario (default: "user")

        Returns:
            JWT token como string
        """
        now = int(time.time())
        payload = {
            "sub": user_id,      # subject (user_id)
            "email": email,       # email del usuario
            "role": role,         # rol del usuario
            "iat": now,          # issued at
            "exp": now + (self.settings.jwt_expiration_hours * 3600)  # expiration
        }

        token = jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        return token

    def verify(self, token: str) -> dict:
        """Verifica y decodifica JWT token.

        Args:
            token: JWT token como string

        Returns:
            Payload dict si válido

        Raises:
            ExpiredSignatureError: Si token expiró
            JWTError: Si firma es inválida
        """
        payload = jwt.decode(
            token,
            self.settings.jwt_secret_key,
            algorithms=[self.settings.jwt_algorithm]
        )
        return payload

    def extract_user_id(self, payload: dict) -> str:
        """Extrae user_id del payload.

        Args:
            payload: Payload decodificado

        Returns:
            user_id como string
        """
        return payload["sub"]
