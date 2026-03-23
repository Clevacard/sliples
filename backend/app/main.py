"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, environments, scenarios, runs, repos, steps, browsers, auth, users, schedules, seed, test_session, projects, pages, parser
from app.api.routes import settings as settings_routes
from app.config import get_settings
from app.database import engine
from app.models import Base


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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Sliples API",
        "version": "0.1.0",
        "docs": "/docs",
    }
