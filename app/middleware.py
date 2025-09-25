import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request correlation IDs and log request/response details.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for other handlers to use
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Create request-scoped logger
        request_logger = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown")
        )

        # Log request start
        request_logger.info(
            "Request started",
            query_params=dict(request.query_params) if request.query_params else None
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time

            # Log successful response
            request_logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
                response_size=response.headers.get("content-length")
            )

            # Add request ID to response headers for client-side correlation
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate request duration even for errors
            duration = time.time() - start_time

            # Log error
            request_logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration * 1000, 2),
                exc_info=True
            )

            # Re-raise the exception
            raise


class WebSocketLoggingMiddleware:
    """
    Helper class for WebSocket connection logging.
    Not a traditional middleware since WebSockets don't use the same pattern.
    """

    @staticmethod
    def get_connection_logger(session_id: str, client_ip: str = "unknown") -> structlog.stdlib.BoundLogger:
        """
        Get a logger bound with WebSocket connection context.

        Args:
            session_id: WebSocket session ID
            client_ip: Client IP address

        Returns:
            Logger bound with WebSocket context
        """
        connection_id = str(uuid.uuid4())

        return logger.bind(
            connection_id=connection_id,
            session_id=session_id,
            client_ip=client_ip,
            connection_type="websocket"
        )