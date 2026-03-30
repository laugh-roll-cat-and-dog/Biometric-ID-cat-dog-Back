from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.database import Base, engine
from app.config.settings import settings
from app.routes import upload_router, health_router, search_router, searchbyimage_router

IMAGE_ROOT = Path("/srv/storage/whatthedog/Dogs image").resolve()


def to_public_image_path(file_path: str | None) -> str | None:
    """Convert file path to public image URL, preserving subdirectory structure."""
    if not file_path:
        return None
    
    try:
        abs_path = Path(file_path).resolve()
        rel = abs_path.relative_to(IMAGE_ROOT).as_posix()
        return f"/images/{rel}"
    except (ValueError, OSError):
        return None


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(health_router, tags=["Health"])
app.include_router(upload_router, tags=["Upload"])
app.include_router(search_router, tags=["Search"])
app.include_router(searchbyimage_router, tags=["Search By Image"])

# Mount static files for images
app.mount(
    "/images",
    StaticFiles(directory=str(IMAGE_ROOT)),
    name="images",
)