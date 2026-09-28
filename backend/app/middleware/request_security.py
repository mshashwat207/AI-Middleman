from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RequestSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_content_length: int = 100000):
        super().__init__(app)
        self.max_content_length = max_content_length

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_content_length:
                    logger.warning(f"Request blocked due to payload size: {length} bytes")
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Payload Too Large"}
                    )
            except ValueError:
                pass
                
        response = await call_next(request)
        
        # Add secure headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
