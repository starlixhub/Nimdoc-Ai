import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("nimdoc.access")
error_logger = logging.getLogger("nimdoc.error")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs incoming HTTP requests, records latency, and injects
    diagnostic headers (X-Request-ID, X-Process-Time-Ms).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["x-request-id"] = request_id
        response.headers["x-process-time-ms"] = str(duration_ms)

        logger.info(
            "%s %s -> status=%d duration=%.2fms req_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """
    Catches unhandled exceptions that escape route handlers, logs full traceback,
    and returns a structured JSON 500 response.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            error_logger.exception(
                "Unhandled server exception during %s %s: %s",
                request.method,
                request.url.path,
                exc,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": str(exc) if str(exc) else "An unexpected error occurred.",
                    "status_code": 500,
                    "path": request.url.path,
                },
            )
