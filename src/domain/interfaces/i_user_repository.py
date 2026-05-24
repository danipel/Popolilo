# Pattern: Repository (Domain Interface)
from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.user import User
from src.domain.value_objects.email import Email


class IUserRepository(ABC):
    """Interfaz de repositorio para operaciones de User.

    Define el contrato de persistencia sin detalles de implementación.
    La implementación concreta (SQLAlchemy) se encuentra en infrastructure/
    """

    @abstractmethod
    def create(self, user: User) -> User:
        """Persiste un nuevo usuario.

        Args:
            user: Instancia de User Entity

        Returns:
            El mismo user persistido

        Raises:
            UserAlreadyExistsError: Si email ya existe
        """
        pass

    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """Busca usuario por email.

        Args:
            email: Email Value Object

        Returns:
            User si existe, None en caso contrario
        """
        pass

    @abstractmethod
    def email_exists(self, email: Email) -> bool:
        """Verifica si email ya está registrado.

        Args:
            email: Email Value Object

        Returns:
            True si existe, False en caso contrario
        """
        pass
