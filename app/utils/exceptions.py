import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    def _request_meta(request: Request) -> dict:
        request_id = getattr(request.state, "request_id", None)
        return {"request_id": request_id} if request_id else {}

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = [
            {
                "field": " → ".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Validation error",
                    "details": errors,
                },
                "meta": _request_meta(request),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        details = exc.detail if isinstance(exc.detail, (dict, list)) else None
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": message,
                    "details": details,
                },
                "meta": _request_meta(request),
            },
            headers=exc.headers,
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "PYDANTIC_VALIDATION_ERROR",
                    "message": "Data validation failed",
                    "details": exc.errors(),
                },
                "meta": _request_meta(request),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                    "details": None,
                },
                "meta": _request_meta(request),
            },
        )
