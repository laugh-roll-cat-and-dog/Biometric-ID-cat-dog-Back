from pathlib import Path
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from app.config.settings import settings


def detect_image_type(path: Path) -> str:
    """Detect image format using Pillow and return a safe extension."""
    
    print(f"[DEBUG] Detecting image type for: {path}")
    try:
        # First, verify the image
        with Image.open(path) as img:
            img.verify()  # Validate file signature without decoding full image
        
        # Then, reopen to get the format (verify() consumes the file)
        with Image.open(path) as img:
            fmt = (img.format or "").upper()
            print(f"[DEBUG] Raw format detected: {fmt}")
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=400, 
            detail="File is not a supported image type"
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=400, 
            detail="Invalid image file"
        ) from exc

    if fmt == "JPEG":
        print(f"[DEBUG] Image type detected: JPEG")
        return "jpeg"
    if fmt:
        print(f"[DEBUG] Image type detected: {fmt.lower()}")
        return fmt.lower()
    
    raise HTTPException(status_code=400, detail="Could not detect image type")


async def save_file(file: UploadFile, dest: Path) -> int:
    """Stream the upload to disk and return the total bytes written."""
    
    print(f"[DEBUG] Starting file save to: {dest}")
    total = 0
    with dest.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)  # 1 MB chunks
            if not chunk:
                break
            total += len(chunk)
            if total > settings.MAX_BYTES:
                print(f"[ERROR] File exceeds {settings.MAX_BYTES} bytes limit. Total: {total}")
                raise HTTPException(
                    status_code=413, 
                    detail=f"File exceeds {settings.MAX_BYTES // (1024*1024)} MB limit"
                )
            buffer.write(chunk)
    
    print(f"[DEBUG] File saved successfully. Total bytes written: {total}")
    return total
