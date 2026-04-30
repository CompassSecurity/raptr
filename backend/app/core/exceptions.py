"""
Custom exception handlers for the application.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors to redact sensitive password fields.
    """
    errors = exc.errors()

    for error in errors:
        # Redact password input values
        if any("password" in str(loc).lower() for loc in error.get("loc", [])):
            error["input"] = "<redacted>"

        # Convert non-JSON-serializable context values to strings
        if "ctx" in error and isinstance(error["ctx"], dict):
            for key, value in error["ctx"].items():
                if isinstance(value, Exception):
                    error["ctx"][key] = str(value)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": errors},
    )
