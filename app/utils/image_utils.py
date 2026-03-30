from pathlib import Path

# Image storage root directory
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
