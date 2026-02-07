import uuid
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from app.config.database import SessionLocal
from app.config.settings import settings
from app.models import Dog, DogPhoto
from app.utils.file_handler import detect_image_type, save_file

router = APIRouter()


@router.post("/upload/photo")
async def upload_photo(
    images: list[UploadFile] = File(...),
    name: str = Form(...),
    breed: str = Form(...),
    age: int = Form(...),
    description: str = Form(...)
) -> JSONResponse:
    """Upload photos for a new dog"""
    
    # Create a folder for this dog
    dog_folder = settings.BASE_UPLOAD_DIR / name.strip().replace("/", "_").replace("\\", "_")
    dog_folder.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Created/verified dog folder: {dog_folder}")

    uploaded_files = []
    db = SessionLocal()

    try:
        # Create ONE dog record for this upload (even if multiple images)
        new_dog = Dog(
            name=name,
            breed=breed,
            age=age,
            description=description
        )
        db.add(new_dog)
        db.commit()
        db.refresh(new_dog)
        dog_id = new_dog.id
        print(f"[INFO] Dog record created with ID: {dog_id}")

        # Process each image and link to the same dog
        for image in images:
            content_type = image.content_type or ""
            if not content_type.startswith("image/"):
                print(f"[ERROR] Invalid content type: {content_type}")
                continue  # Skip non-image files

            temp_path = dog_folder / f"{uuid.uuid4().hex}.upload"
            bytes_written = await save_file(image, temp_path)

            extension = detect_image_type(temp_path)
            destination = temp_path.with_suffix(f".{extension}")
            temp_path.rename(destination)
            print(f"[INFO] File renamed to final destination: {destination}")

            # Save photo record linked to the dog
            new_photo = DogPhoto(
                dog_id=dog_id,
                filename=destination.name,
                file_path=str(destination),
                file_size_bytes=bytes_written,
                file_extension=extension
            )
            db.add(new_photo)
            db.commit()
            db.refresh(new_photo)
            print(f"[INFO] Photo saved to database with ID: {new_photo.id}")

            uploaded_files.append({
                "filename": destination.name,
                "path": str(destination),
                "bytes": bytes_written,
                "photo_id": new_photo.id
            })

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Database error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to save to database"
        ) from e
    finally:
        db.close()

    response_data = {
        "message": "Upload successful",
        "dog_id": dog_id,
        "total_images": len(uploaded_files),
        "uploaded_files": uploaded_files,
        "pet_info": {
            "name": name,
            "breed": breed,
            "age": age,
            "description": description
        }
    }
    print(f"[INFO] Upload completed successfully - Response: {response_data}")
    return JSONResponse(
        status_code=201,
        content=response_data,
    )
