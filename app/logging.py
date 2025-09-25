import logging
import logging.config
import sys
from typing import Any, Dict, Optional
import structlog
import os


def setup_logging(environment: str = "development") -> None:
    """
    Configure simplified structured logging.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if environment == "development":
        # Pretty console output for development
        shared_processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON output for production
        shared_processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Configure basic logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if environment == "production" else logging.DEBUG,
    )

    # Reduce noise from external libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured structlog logger."""
    return structlog.get_logger(name)


def add_request_context(logger: structlog.stdlib.BoundLogger,
                       request_id: str,
                       method: str,
                       path: str,
                       **extra: Any) -> structlog.stdlib.BoundLogger:
    """Add request-specific context to a logger."""
    return logger.bind(
        request_id=request_id,
        method=method,
        path=path,
        **extra
    )


def add_service_context(logger: structlog.stdlib.BoundLogger,
                       service: str,
                       operation: str,
                       **extra: Any) -> structlog.stdlib.BoundLogger:
    """Add service-specific context to a logger."""
    return logger.bind(
        service=service,
        operation=operation,
        **extra
    )


class ServiceOperationContext:
    """Context manager for service operations with timing."""

    def __init__(self, logger: structlog.stdlib.BoundLogger, operation: str, **context: Any):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        import time
        self.start_time = time.time()
        bound_logger = self.logger.bind(operation=self.operation, **self.context)
        bound_logger.info(f"Starting {self.operation}")
        return bound_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time if self.start_time else 0

        if exc_type is not None:
            self.logger.error(
                f"Operation {self.operation} failed",
                operation=self.operation,
                duration_ms=round(duration * 1000, 2),
                error=str(exc_val),
                error_type=exc_type.__name__ if exc_type else None,
                **self.context
            )
        else:
            self.logger.info(
                f"Operation {self.operation} completed successfully",
                operation=self.operation,
                duration_ms=round(duration * 1000, 2),
                **self.context
            )