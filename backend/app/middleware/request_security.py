from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

logger = logging.getLogger(__name__)

_CSP = (
    "default-src 'none'; "
    "script-src 'self'; "
    "connect-src 'self'; "
    "img-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "frame-ancestors 'none';"
)


class RequestSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_content_length: int = 65536) -> None:
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        if len(body) > self.max_content_length:
            logger.warning(
                "Request blocked: body size %d bytes exceeds %d byte limit.",
                len(body),
                self.max_content_length,
            )
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload Too Large"},
            )

        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        response.headers["Content-Security-Policy"] = _CSP
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        return response
