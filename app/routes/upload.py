import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from app.config.database import SessionLocal
from app.config.settings import settings
from app.models import Dog, DogPhoto
from app.utils.file_handler import detect_image_type, save_file
import os

import torch
import torchvision.transforms as transforms
from PIL import Image
from ..network.network import Network_ConvNext
import torch.nn.functional as F

from app.utils.embedding import embed_image
from app.utils.crop import crop_image
import cv2

router = APIRouter()


@router.post("/upload/photo")
async def upload_photo(
    images: list[UploadFile] = File(...),
    name: Optional[str] = Form(None),
    breed: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    dog_id: Optional[int] = Form(None)
) -> JSONResponse:
    """Upload photos for a new dog"""
    
    uploaded_files = []
    db = SessionLocal()

    try:
        # Use existing dog if dog_id is provided, otherwise create a new dog
        if dog_id is not None:
            existing_dog = db.query(Dog).filter(Dog.id == dog_id).first()
            if existing_dog is None:
                raise HTTPException(status_code=404, detail="Dog not found")
            dog_record = existing_dog
            print(f"[INFO] Using existing dog record with ID: {dog_record.id}")
        else:
            if not all([name, breed, age is not None, description is not None]):
                raise HTTPException(
                    status_code=422,
                    detail="name, breed, age, description are required when dog_id is not provided"
                )
            dog_record = Dog(
                name=name,
                breed=breed,
                age=age,
                description=description
            )
            db.add(dog_record)
            db.commit()
            db.refresh(dog_record)
            print(f"[INFO] Dog record created with ID: {dog_record.id}")

        # Capture dog info before session closes
        dog_id_value = dog_record.id
        pet_info = {
            "name": dog_record.name,
            "breed": dog_record.breed,
            "age": dog_record.age,
            "description": dog_record.description,
        }

        foldername = f"dog_{dog_id_value}"

        # Create a folder for this dog
        dog_folder = settings.BASE_UPLOAD_DIR / foldername
        dog_folder.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Created/verified dog folder: {dog_folder}")

        nose_folder = settings.BASE_UPLOAD_DIR / foldername / "nose"
        nose_folder.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Created/verified nose folder: {nose_folder}")

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
            print(f"[INFO] Renaming file {temp_path} to {destination}")
            print(f"[INFO] Renaming file {temp_path} to {destination.name}")
            temp_path.rename(destination)
            print(f"[INFO] File renamed to final destination: {destination}")

            #make embedding vector for image
            
            emb = embed_image(destination)
            print(f"[INFO] Embedding generated: {emb}")

            # Crop image to get nose region
            nose_crop = crop_image(destination)
            print(f"[INFO] Image cropped: {nose_crop}")

            # Save cropped nose image if detected
            nose_destination = None
            nose_emb = None
            if nose_crop is not None:
                nose_filename = f"{uuid.uuid4().hex}_nose.jpeg"
                nose_destination = nose_folder / nose_filename
                
                # Convert BGR to RGB and save using PIL
                nose_rgb = cv2.cvtColor(nose_crop, cv2.COLOR_BGR2RGB)
                nose_pil = Image.fromarray(nose_rgb)
                nose_pil.save(str(nose_destination), 'JPEG')
                print(f"[INFO] Nose saved to: {nose_destination}")

                nose_emb = embed_image(nose_destination)
                print(f"[INFO] Nose embedding generated: {nose_emb}")
            else:
                print(f"[WARN] No nose detected in image")



            # Save photo record linked to the dog
            new_photo = DogPhoto(
                dog_id=dog_id_value,
                filename=destination.name,
                file_path=str(destination),
                file_size_bytes=bytes_written,
                file_extension=extension,
                embedding=F.normalize(emb[0], p=2, dim=0),
                cropped_nose_path=str(nose_destination) if nose_destination else None,
                nose_embedding=F.normalize(nose_emb[0], p=2, dim=0) if nose_emb is not None else None
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
        "dog_id": dog_id_value,
        "total_images": len(uploaded_files),
        "uploaded_files": uploaded_files,
        "pet_info": pet_info
    }
    print(f"[INFO] Upload completed successfully - Response: {response_data}")
    return JSONResponse(
        status_code=201,
        content=response_data,
    )
