# Pattern: Value Object + Strategy
import re
from abc import ABC, abstractmethod
import bcrypt


class HashingStrategy(ABC):
    """Estrategia abstracta para hashing de passwords."""

    @abstractmethod
    def hash(self, plaintext: str) -> str:
        """Convierte plaintext a hash."""
        pass

    @abstractmethod
    def verify(self, plaintext: str, hashed: str) -> bool:
        """Verifica plaintext contra hash."""
        pass


class BcryptStrategy(HashingStrategy):
    """Implementación de hashing con bcrypt."""

    ROUNDS = 12

    def hash(self, plaintext: str) -> str:
        """Hashea plaintext con bcrypt."""
        salt = bcrypt.gensalt(rounds=self.ROUNDS)
        hashed = bcrypt.hashpw(plaintext.encode(), salt)
        return hashed.decode()

    def verify(self, plaintext: str, hashed: str) -> bool:
        """Verifica plaintext contra hash bcrypt."""
        try:
            return bcrypt.checkpw(plaintext.encode(), hashed.encode())
        except Exception:
            return False


class Password:
    """Value Object para passwords.

    Características:
    - Validación de requisitos de seguridad
    - Hashing mediante Strategy
    - Inmutable después de construcción
    - Nunca expone plaintext ni hash en serialización
    """

    def __init__(self, plaintext: str, strategy: HashingStrategy = None):
        """Constructor que valida y hashea.

        Args:
            plaintext: Password en texto plano
            strategy: Estrategia de hashing (default: BcryptStrategy)

        Raises:
            ValueError: Si password no cumple requisitos
        """
        if strategy is None:
            strategy = BcryptStrategy()

        self._validate(plaintext)
        self._strategy = strategy
        self._hash = strategy.hash(plaintext)

    @staticmethod
    def _validate(plaintext: str) -> None:
        """Valida requisitos de seguridad.

        Requisitos:
        - Mínimo 8 caracteres
        - Al menos 1 mayúscula
        - Al menos 1 número

        Raises:
            ValueError: Si no cumple requisitos
        """
        if not plaintext or len(plaintext) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", plaintext):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"\d", plaintext):
            raise ValueError("Password must contain at least one digit")

    @property
    def hash(self) -> str:
        """Retorna el hash (read-only)."""
        return self._hash

    def verify(self, plaintext: str) -> bool:
        """Verifica plaintext contra el hash almacenado."""
        return self._strategy.verify(plaintext, self._hash)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return "Password(***)"

    def __str__(self) -> str:
        """String representation nunca expone el hash."""
        return "Password(***)"
