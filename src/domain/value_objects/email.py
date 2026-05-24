# Pattern: Value Object
from email_validator import validate_email, EmailNotValidError


class Email:
    """Value Object para direcciones de email.

    Características:
    - Inmutable (propiedades read-only)
    - Auto-validación en construcción
    - Comparable y hasheable
    - Nunca expone el valor en serialización
    """

    def __init__(self, address: str):
        """Constructor que valida email RFC 5322.

        Args:
            address: String con dirección de email

        Raises:
            ValueError: Si el email es inválido
        """
        if not address or not isinstance(address, str):
            raise ValueError("Email must be a non-empty string")

        try:
            # Validar y normalizar con email-validator
            validation = validate_email(address, check_deliverability=False)
            self._address = validation.normalized
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email: {str(e)}")

    @property
    def value(self) -> str:
        """Retorna la dirección de email normalizada."""
        return self._address

    def __str__(self) -> str:
        """String representation."""
        return self._address

    def __eq__(self, other) -> bool:
        """Comparación por valor."""
        if not isinstance(other, Email):
            return False
        return self._address == other._address

    def __hash__(self) -> int:
        """Hash para uso en sets/dicts."""
        return hash(self._address)

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"Email({self._address!r})"
