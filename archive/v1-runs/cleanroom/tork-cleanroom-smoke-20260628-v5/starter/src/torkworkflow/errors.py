class WorkflowError(Exception):
    """Base public exception for workflow contract failures."""


class SpecError(WorkflowError):
    """Raised when a job or schedule specification is invalid."""


class NotFoundError(WorkflowError):
    """Raised when a public object cannot be found."""


class ConflictError(WorkflowError):
    """Raised when a lifecycle operation conflicts with current state."""
