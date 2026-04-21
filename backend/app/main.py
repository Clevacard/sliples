"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse
from starlette.datastructures import MutableHeaders

from app.api.routes import health, environments, scenarios, runs, repos, steps, browsers, auth, users, schedules, seed, test_session, projects, pages, parser, recorder
from app.api.routes import settings as settings_routes
from app.config import get_settings
from app.database import engine
from app.models import Base


class PublicCORSMiddleware(BaseHTTPMiddleware):
    """Custom middleware to add CORS headers for public endpoints."""

    async def dispatch(self, request, call_next):
        # Handle CORS for all recorder endpoints
        if request.url.path.startswith("/api/v1/recorder"):
            # Handle CORS preflight for all recorder endpoints
            if request.method == "OPTIONS":
                return Response(
                    status_code=200,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, X-API-Key",
                        "Access-Control-Max-Age": "86400",
                        "Content-Length": "0",
                    },
                )
            response = await call_next(request)
            # Use MutableHeaders to modify response headers
            headers = MutableHeaders(response.headers)
            headers["Access-Control-Allow-Origin"] = "*"
            headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
            # Cache snippet for 1 hour
            if request.url.path == "/api/v1/recorder/snippet.js":
                headers["Cache-Control"] = "public, max-age=3600"
            return response

        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: create tables if they don't exist (dev only, use migrations in prod)
    # Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


settings = get_settings()

app = FastAPI(
    title="Sliples API",
    description="Web UI Automation Testing Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Custom CORS middleware for public endpoints like recorder snippet
# Must be added LAST (runs first - LIFO order)
# This handles OPTIONS preflight and sets CORS headers
app.add_middleware(PublicCORSMiddleware)

# CORS middleware - for all endpoints
# When using wildcard origins, set allow_credentials to False (CORS spec requirement)
cors_origins = settings.cors_origins
allow_credentials = cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(environments.router, prefix="/api/v1", tags=["Environments"])
app.include_router(pages.router, prefix="/api/v1", tags=["Pages"])
app.include_router(scenarios.router, prefix="/api/v1", tags=["Scenarios"])
app.include_router(runs.router, prefix="/api/v1", tags=["Test Runs"])
app.include_router(repos.router, prefix="/api/v1", tags=["Repositories"])
app.include_router(steps.router, prefix="/api/v1", tags=["Custom Steps"])
app.include_router(browsers.router, prefix="/api/v1", tags=["Browsers"])
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(schedules.router, prefix="/api/v1", tags=["Schedules"])
app.include_router(seed.router, prefix="/api/v1", tags=["Seed Data"])
app.include_router(test_session.router, prefix="/api/v1", tags=["Test Sessions"])
app.include_router(settings_routes.router, prefix="/api/v1", tags=["Settings"])
app.include_router(parser.router, prefix="/api/v1", tags=["Parser"])
app.include_router(recorder.router, prefix="/api/v1", tags=["Recorder"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Sliples API",
        "version": "0.1.0",
        "docs": "/docs",
    }
