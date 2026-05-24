# Pattern: Custom Exceptions (Domain-specific errors)


class UserAlreadyExistsError(Exception):
    """Exception lanzada cuando se intenta registrar un email duplicado."""

    def __init__(self, message: str = "User with this email already exists"):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(Exception):
    """Exception lanzada cuando credenciales son inválidas en login."""

    def __init__(self, message: str = "Invalid email or password"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(Exception):
    """Exception lanzada cuando usuario no existe."""

    def __init__(self, message: str = "User not found"):
        self.message = message
        super().__init__(self.message)
