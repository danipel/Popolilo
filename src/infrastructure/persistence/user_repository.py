# Pattern: Repository Implementation (SQLAlchemy)
# PostgreSQL UNIQUE constraint + rollback en IntegrityError
# Cada request tiene su propia Session → sin race conditions
from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import Session
from sqlalchemy.exc import IntegrityError
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password
from src.domain.interfaces.i_user_repository import IUserRepository
from src.domain.exceptions import UserAlreadyExistsError
from src.infrastructure.persistence.models import UserModel


class UserRepository(IUserRepository):
    """Implementación de repositorio User con SQLAlchemy."""

    def __init__(self, session: Session):
        """Constructor inyecta sesión de base de datos."""
        self.session = session

    def create(self, user: User) -> User:
        """Persiste usuario en BD.

        Args:
            user: User Entity

        Returns:
            El mismo user persistido

        Raises:
            UserAlreadyExistsError: Si email ya existe (UNIQUE constraint)
        """
        try:
            # Convertir Entity a Model
            model = UserModel(
                id=str(user.id),
                email=str(user.email),
                password_hash=user.password.hash,
                created_at=user.created_at,
            )
            # Persistir
            self.session.add(model)
            self.session.commit()
            return user
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e).lower():
                raise UserAlreadyExistsError("Email already registered")
            raise

    def find_by_email(self, email: Email) -> Optional[User]:
        """Busca usuario por email.

        Args:
            email: Email Value Object

        Returns:
            User si existe, None en caso contrario
        """
        model = self.session.query(UserModel).filter_by(
            email=str(email)
        ).first()

        if model is None:
            return None

        return self._model_to_entity(model)

    def email_exists(self, email: Email) -> bool:
        """Verifica si email existe.

        Args:
            email: Email Value Object

        Returns:
            True si existe
        """
        count = self.session.query(UserModel).filter_by(
            email=str(email)
        ).count()
        return count > 0

    def _model_to_entity(self, model: UserModel) -> User:
        """Convierte SQLAlchemy Model a Domain Entity.

        Args:
            model: UserModel (ORM)

        Returns:
            User Entity
        """
        # Reconstruir Value Objects desde model
        email = Email(model.email)
        # Necesitamos Password con hash preexistente
        password = Password.__new__(Password)
        password._hash = model.password_hash
        password._strategy = None  # No necesitamos strategy para verify

        # Reconstruir Entity
        user = User(
            id=UUID(model.id),
            email=email,
            password=password,
            created_at=model.created_at,
        )
        return user
