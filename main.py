from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import Base, engine
from app.config.settings import settings
from app.routes import upload_router, health_router

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
