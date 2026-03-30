from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.database import Base, engine
from app.config.settings import settings
from app.routes import upload_router, health_router, search_router, searchbyimage_router

app = FastAPI()
IMAGE_ROOT = Path("/srv/storage/whatthedog/Dogs image").resolve()
app.mount("/images", StaticFiles(directory=str(IMAGE_ROOT)), name="images")

def to_public_image_path(file_path: str | None) -> str | None:
    if not file_path:
        return None
    
    p = str(file_path)
    if p.startswith("file://"):
        p = p[7:]
    
    print(f"[DEBUG] Input file_path: {file_path}")
    print(f"[DEBUG] Cleaned path: {p}")
    print(f"[DEBUG] IMAGE_ROOT: {IMAGE_ROOT}")
    
    try:
        abs_path = Path(p).resolve()
        print(f"[DEBUG] Resolved abs_path: {abs_path}")
        
        rel = abs_path.relative_to(IMAGE_ROOT).as_posix()
        print(f"[DEBUG] Relative path: {rel}")
        
        result = f"/images/{rel}"
        print(f"[DEBUG] Final result: {result}")
        return result
    except (ValueError, OSError) as e:
        print(f"[DEBUG] Error: {e}")
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