import logging
import logging.config
import sys
from typing import Any, Dict, Optional
import structlog
from structlog import stdlib
import os


def setup_logging(environment: str = "development") -> None:
    """
    Configure structured logging with structlog and stdlib integration.

    Args:
        environment: "development" or "production"
    """

    # Configure structlog processors
    processors = [
        stdlib.filter_by_level,  # Filter by log level first
        stdlib.add_logger_name,  # Add the logger name to the event dict
        stdlib.add_log_level,    # Add the log level to the event dict
        stdlib.PositionalArgumentsFormatter(),  # Format positional arguments
        structlog.processors.TimeStamper(fmt="ISO"),  # Add timestamp
        structlog.processors.StackInfoRenderer(),  # Render stack info if present
        structlog.processors.format_exc_info,  # Format exception info
    ]

    if environment == "development":
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # JSON output for production (better for log aggregation)
        processors.append(structlog.processors.JSONRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=stdlib.BoundLogger,
        logger_factory=stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=False) if environment == "development"
                    else structlog.processors.JSONRenderer(),
                ],
                "foreign_pre_chain": processors,
            },
        },
        "handlers": {
            "default": {
                "level": "INFO" if environment == "production" else "DEBUG",
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "plain",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": "INFO" if environment == "production" else "DEBUG",
                "propagate": True,
            },
            # Reduce noise from external libraries
            "uvicorn": {"level": "INFO"},
            "uvicorn.access": {"level": "WARNING"},
            "sqlalchemy.engine": {"level": "WARNING"},
            "httpx": {"level": "WARNING"},
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structlog logger.

    Args:
        name: Logger name, typically __name__

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding structured context to all logs within a scope."""

    def __init__(self, **context: Any):
        self.context = context
        self.bound_logger: Optional[structlog.stdlib.BoundLogger] = None

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        self.bound_logger = structlog.get_logger().bind(**self.context)
        return self.bound_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def add_request_context(logger: structlog.stdlib.BoundLogger,
                       request_id: str,
                       method: str,
                       path: str,
                       **extra: Any) -> structlog.stdlib.BoundLogger:
    """
    Add request-specific context to a logger.

    Args:
        logger: Base logger to bind context to
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        **extra: Additional context data

    Returns:
        Logger bound with request context
    """
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
    """
    Add service-specific context to a logger.

    Args:
        logger: Base logger to bind context to
        service: Service name (e.g., "forecast_service")
        operation: Operation name (e.g., "generate_forecast")
        **extra: Additional context data

    Returns:
        Logger bound with service context
    """
    return logger.bind(
        service=service,
        operation=operation,
        **extra
    )


class DatabaseTransactionContext:
    """Context manager for database transactions with logging."""

    def __init__(self, db_session, logger: structlog.stdlib.BoundLogger, operation: str):
        self.db_session = db_session
        self.logger = logger
        self.operation = operation

    def __enter__(self):
        self.logger.debug("Starting database transaction", operation=self.operation)
        return self.db_session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.db_session.rollback()
            self.logger.error(
                "Database transaction failed, rolled back",
                operation=self.operation,
                error=str(exc_val),
                error_type=exc_type.__name__ if exc_type else None,
                exc_info=True
            )
        else:
            try:
                self.db_session.commit()
                self.logger.debug("Database transaction committed successfully", operation=self.operation)
            except Exception as commit_error:
                self.db_session.rollback()
                self.logger.error(
                    "Database commit failed, rolled back",
                    operation=self.operation,
                    error=str(commit_error),
                    error_type=type(commit_error).__name__,
                    exc_info=True
                )
                raise


class ServiceOperationContext:
    """Context manager for service operations with timing and error handling."""

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
                exc_info=True,
                **self.context
            )
        else:
            self.logger.info(
                f"Operation {self.operation} completed successfully",
                operation=self.operation,
                duration_ms=round(duration * 1000, 2),
                **self.context
            )