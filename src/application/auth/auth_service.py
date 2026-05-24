# Pattern: Service (Application Use Cases)
# AuthService es stateless, inyecta dependencias.
# Repository maneja sincronización en BD.
# JWT token generación es stateless.
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.interfaces.i_user_repository import IUserRepository
from src.domain.exceptions import InvalidCredentialsError
from src.application.auth.jwt_service import JWTService


class AuthService:
    """Servicio de casos de uso de autenticación."""

    def __init__(
        self,
        user_repository: IUserRepository,
        jwt_service: JWTService
    ):
        """Constructor inyecta dependencias.

        Args:
            user_repository: Implementación de IUserRepository
            jwt_service: Instancia de JWTService
        """
        self.user_repository = user_repository
        self.jwt_service = jwt_service

    def register(self, email: str, password: str) -> dict:
        """Caso de uso: Registrar nuevo usuario.

        Args:
            email: Dirección de email
            password: Password en texto plano

        Returns:
            Dict con user_id

        Raises:
            ValueError: Si email o password inválidos
            UserAlreadyExistsError: Si email ya existe
        """
        # User.create() valida email/password (lanza ValueError si inválido)
        user = User.create(email, password)

        # Persistir en BD (puede lanzar UserAlreadyExistsError)
        saved_user = self.user_repository.create(user)

        return {
            "user_id": str(saved_user.id)
        }

    def login(self, email: str, password: str) -> dict:
        """Caso de uso: Login de usuario.

        Args:
            email: Dirección de email
            password: Password en texto plano

        Returns:
            Dict con access_token

        Raises:
            ValueError: Si email inválido
            InvalidCredentialsError: Si email no existe o password incorrecto
        """
        # Validar email (lanza ValueError si inválido)
        email_vo = Email(email)

        # Buscar usuario
        user = self.user_repository.find_by_email(email_vo)
        if user is None:
            raise InvalidCredentialsError("Invalid email or password")

        # Verificar password
        if not user.password.verify(password):
            raise InvalidCredentialsError("Invalid email or password")

        # Generar token
        token = self.jwt_service.generate(
            user_id=str(user.id),
            email=str(user.email),
            role="user"
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }
