import uuid
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.config.database import SessionLocal
from app.config.settings import settings
from app.models import Dog, DogPhoto
from app.utils.file_handler import detect_image_type, save_file
from app import to_public_image_path

import torch
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from ..network.network import Network_ConvNext
import os


router = APIRouter()
MAX_RESULTS = 3





class SearchRequest(BaseModel):
    query: str
    search_mode: str


@router.post("/search")
async def search(request: SearchRequest):
    query = request.query
    search_mode = request.search_mode
    print(f"[INFO] Query: {query}")
    print(f"[INFO] Search Mode (Column): {search_mode}")

    db = SessionLocal()
    try:
        # Dynamically query based on search_mode (which column to search)
        column = getattr(Dog, search_mode)
        
        # Convert query to appropriate type based on column
        if search_mode in ['id', 'age']:
            # These are integer columns
            try:
                query_value = int(query)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Query must be an integer for column '{search_mode}'"
                )
        else:
            # String columns
            query_value = query
        
        results = db.query(Dog).filter(column == query_value).all()
        
        print(f"[INFO] Found {len(results)} results")
        for result in results:
            print(f"[INFO] Dog ID: {result.id}, Name: {result.name}")
        
        # Format response with all images
        dog_list = []
        for dog in results:
            photos = db.query(DogPhoto).filter(DogPhoto.dog_id == dog.id).all()
            images = [
                {
                    "filename": photo.filename,
                    "path": to_public_image_path(photo.file_path),
                    "photo_id": photo.id
                }
                for photo in photos
            ]

            dog_data = {
                "id": dog.id,
                "name": dog.name,
                "breed": dog.breed,
                "age": dog.age,
                "description": dog.description,
                "images": images
            }
            dog_list.append(dog_data)
        
        limited_dog_list = dog_list[:MAX_RESULTS]

        return JSONResponse(
            status_code=200,
            content={
                "message": "Search completed",
                "query": query,
                "search_column": search_mode,
                "results": limited_dog_list,
                "count": len(limited_dog_list)
            }
        )
    except AttributeError:
        print(f"[ERROR] Invalid search mode: {search_mode}")
        raise HTTPException(status_code=400, detail=f"Invalid search column: {search_mode}") from None
    except Exception as e:
        print(f"[ERROR] Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database query failed") from e
    finally:
        db.close()