"""Custom exception classes for the SAMi backend application."""


class ValidationError(Exception):
    """Raised when client input validation fails."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Raised when business logic rules are violated."""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_id:
            self.message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            self.message = f"{resource_type} not found"
        super().__init__(self.message)


class ConflictError(Exception):
    """Raised when a resource conflict occurs."""

    def __init__(self, message: str, conflicts: list = None):
        self.message = message
        self.conflicts = conflicts or []
        super().__init__(self.message)