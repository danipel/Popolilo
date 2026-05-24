# Pattern: Entity + Factory Method
from uuid import UUID, uuid4
from datetime import datetime
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password


class User:
    """Entity que representa un usuario del sistema.

    Características:
    - ID inmutable (generado al crear)
    - email y password son Value Objects
    - created_at inmutable
    - Factory method para construcción
    """

    def __init__(
        self,
        id: UUID,
        email: Email,
        password: Password,
        created_at: datetime,
    ):
        """Constructor privado. Usar User.create() en su lugar."""
        self._id = id
        self._email = email
        self._password = password
        self._created_at = created_at

    @staticmethod
    def create(email: str, password: str) -> "User":
        """Factory method para crear nuevo Usuario.

        Args:
            email: Dirección de email
            password: Password en texto plano

        Returns:
            Nueva instancia de User

        Raises:
            ValueError: Si email o password son inválidos
        """
        # Validar email (lanza ValueError si es inválido)
        email_vo = Email(email)

        # Validar password (lanza ValueError si es inválido)
        password_vo = Password(password)

        # Crear usuario con ID generado
        return User(
            id=uuid4(),
            email=email_vo,
            password=password_vo,
            created_at=datetime.utcnow(),
        )

    @property
    def id(self) -> UUID:
        """ID del usuario (inmutable)."""
        return self._id

    @property
    def email(self) -> Email:
        """Email del usuario (Value Object)."""
        return self._email

    @property
    def password(self) -> Password:
        """Password del usuario (Value Object)."""
        return self._password

    @property
    def created_at(self) -> datetime:
        """Fecha de creación (inmutable)."""
        return self._created_at

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"User(id={self.id}, email={self.email})"
