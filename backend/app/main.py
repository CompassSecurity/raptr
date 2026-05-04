from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.core.config import settings
from app.core.exceptions import validation_exception_handler
from app.core.logging import app_logger
from app.core.startup import (
    create_admin_user,
    create_db_and_tables,
    ensure_admin_password,
    ensure_secret_key,
)
from app.frontend.frontend import init_frontend

# fxai was here


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Event ---
    app_logger.info("Application starting up...")
    ensure_secret_key()
    ensure_admin_password()
    create_db_and_tables()
    create_admin_user()
    yield
    # --- Shutdown Event ---
    app_logger.info("Application shutting down...")


app = FastAPI(
    lifespan=lifespan,
    title="RAPTR Backend API",
    version=settings.RAPTR_VERSION,
    openapi_url="/openapi.json" if settings.FASTAPI_DOCUMENTATION else None,
)

# Register custom exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# CORS Settings
if settings.CORS_ENABLED:
    app_logger.info("CORS enabled for origins: %s", settings.CORS_ORIGINS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_CREDENTIALS,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )

# Import the main router for /api/v1/
app.include_router(router)

# Initialize frontend serving (assets + SPA)
init_frontend(app)
