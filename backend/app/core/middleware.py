"""HTTP middleware: request IDs, access logging, timing."""

from __future__ import annotations

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.context import get_request_id, reset_request_id, set_request_id

logger = logging.getLogger("app.request")

MAX_REQUEST_ID_LENGTH = 128


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("x-request-id")
        request_id = (
            incoming
            if incoming and 0 < len(incoming) <= MAX_REQUEST_ID_LENGTH
            else str(uuid4())
        )

        token = set_request_id(request_id)
        started = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            logger.exception(
                "http_request_failed",
                extra={"extra_fields": {"method": request.method, "path": request.url.path}},
            )
            raise
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "http_request",
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                        "request_id": get_request_id(),
                    }
                },
            )
            reset_request_id(token)
