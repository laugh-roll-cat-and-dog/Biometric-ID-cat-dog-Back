from .upload import router as upload_router
from .health import router as health_router
from .search import router as search_router
from .searchbyimage import router as searchbyimage_router

__all__ = ["upload_router", "health_router", "search_router", "searchbyimage_router"]
