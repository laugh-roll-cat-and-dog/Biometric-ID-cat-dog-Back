from pathlib import Path

# Image storage root directory (using symlink without spaces to avoid StaticFiles issues)
IMAGE_ROOT = Path("/srv/storage/whatthedog/dog_images").resolve()


def _find_by_filename(filename: str) -> str | None:
    """Find an image by filename under dog_* folders and return public path."""
    matches = IMAGE_ROOT.glob(f"dog_*/{filename}")
    first = next(matches, None)
    if first and first.exists():
        rel = first.relative_to(IMAGE_ROOT).as_posix()
        return f"/images/{rel}"
    return None


def to_public_image_path(
    file_path: str | None,
    dog_id: int | None = None,
    filename: str | None = None,
) -> str | None:
    """Convert file path to public image URL, preserving subdirectory structure."""
    if not file_path:
        if dog_id is not None and filename:
            candidate = IMAGE_ROOT / f"dog_{dog_id}" / filename
            if candidate.exists():
                return f"/images/dog_{dog_id}/{filename}"
            return _find_by_filename(filename)
        return None

    if file_path.startswith("/images/"):
        return file_path

    if file_path.startswith("file://"):
        file_path = file_path[7:]
    
    try:
        abs_path = Path(file_path).resolve()
        rel = abs_path.relative_to(IMAGE_ROOT).as_posix()
        if abs_path.exists():
            return f"/images/{rel}"
        if filename:
            return _find_by_filename(filename)
        return None
    except (ValueError, OSError):
        parts = Path(file_path).parts
        for i, part in enumerate(parts):
            if part.startswith("dog_"):
                suffix = Path(*parts[i:]).as_posix()
                candidate = IMAGE_ROOT / suffix
                if candidate.exists():
                    return f"/images/{suffix}"

        if dog_id is not None and filename:
            candidate = IMAGE_ROOT / f"dog_{dog_id}" / filename
            if candidate.exists():
                return f"/images/dog_{dog_id}/{filename}"
            return _find_by_filename(filename)

        return None
