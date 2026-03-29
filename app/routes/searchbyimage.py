import uuid
from pathlib import Path
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from app.config.database import SessionLocal
from app.config.settings import settings
from app.models import Dog, DogPhoto
from app.utils.file_handler import detect_image_type, save_file
from app.utils.crop import crop_image

import torch
import cv2
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import Dataset, DataLoader
from ..network.network import Network_ConvNext
from app.utils.model_loader import load_convnext_checkpoint_compat
import os


router = APIRouter()

@router.post("/searchByImage")
async def search_by_image(image: UploadFile = File(...)) -> JSONResponse:
    """Search for similar dogs by uploading an image"""
    
    print("[INFO] SearchByImage endpoint accessed")
    
    # Validate image
    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")
    
    # Save temp file
    temp_path = Path("/tmp") / f"{uuid.uuid4().hex}.upload"
    bytes_written = await save_file(image, temp_path)
    
    try:
        # Detect image type and rename with proper extension
        extension = detect_image_type(temp_path)
        proper_temp_path = temp_path.with_suffix(f".{extension}")
        temp_path.rename(proper_temp_path)
        temp_path = proper_temp_path
        
        # Crop uploaded image to get nose region
        nose_crop = crop_image(temp_path)
        if nose_crop is None:
            raise HTTPException(status_code=400, detail="No nose detected in uploaded image. Please upload a clear image of a dog's face.")
        
        # Save cropped nose temporarily
        nose_temp_path = Path("/tmp") / f"{uuid.uuid4().hex}_nose.jpg"
        nose_rgb = cv2.cvtColor(nose_crop, cv2.COLOR_BGR2RGB)
        nose_pil = Image.fromarray(nose_rgb)
        nose_pil.save(str(nose_temp_path), 'JPEG')
        
        # Load model
        model = Network_ConvNext('dino', 'sb')
        load_convnext_checkpoint_compat(model, "./app/ai/dino_main_50_class.pt")
        model.eval()
        
        # Prepare transforms
        gallery_transforms = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Generate embedding for cropped nose
        img = Image.open(nose_temp_path).convert("RGB")
        img_tensor = gallery_transforms(img)
        img_batch = img_tensor.unsqueeze(0)
        
        with torch.no_grad():
            query_embedding = model(img_batch)[0]
        
        # Clean up temporary nose file
        if nose_temp_path.exists():
            nose_temp_path.unlink()
        
        print(f"[INFO] Query embedding generated")
        
        # Search database for similar embeddings
        db = SessionLocal()
        try:
            # Get all photos with embeddings
            all_photos = db.query(DogPhoto).all()
            
            if not all_photos:
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "No dogs found in database",
                        "results": []
                    }
                )
            
            # Calculate similarity scores using cosine similarity
            from torch.nn.functional import cosine_similarity
            import torch.nn.functional as F
            
            results = []
            for photo in all_photos:
                # Skip photos without nose embeddings
                if photo.nose_embedding is None:
                    continue
                    
                # Convert nose embedding to tensor
                photo_embedding = torch.tensor(photo.nose_embedding, dtype=torch.float32).unsqueeze(0)
                query_emb = F.normalize(query_embedding, p=2, dim=0)
                
                # Calculate cosine similarity
                similarity = torch.matmul(query_emb, photo_embedding.T)
                
                results.append({
                    "photo_id": photo.id,
                    "dog_id": photo.dog_id,
                    "filename": photo.filename,
                    "file_path": photo.file_path,
                    "cropped_nose_path": photo.cropped_nose_path,
                    "similarity_score": float(similarity)
                })
            
            # Sort by similarity score (highest first)
            results = sorted(results, key=lambda x: x['similarity_score'], reverse=True)
            
            # Group photos by dog and calculate average similarity per dog
            dog_similarities = {}
            for result in results:
                dog_id = result['dog_id']
                if dog_id not in dog_similarities:
                    dog_similarities[dog_id] = []
                dog_similarities[dog_id].append(result)
            
            # Calculate average similarity for each dog and filter by threshold
            threshold = 0.7096
            filtered_dogs = []
            
            for dog_id, dog_results in dog_similarities.items():
                avg_similarity = sum(r['similarity_score'] for r in dog_results) / len(dog_results)
                
                if avg_similarity >= threshold:
                    filtered_dogs.append({
                        'dog_id': dog_id,
                        'avg_similarity': avg_similarity,
                        'photos': dog_results
                    })
            
            # Sort dogs by average similarity (highest first)
            filtered_dogs = sorted(filtered_dogs, key=lambda x: x['avg_similarity'], reverse=True)
            
            # Build response with dogs that meet threshold
            results_by_dog = {}
            for dog_data in filtered_dogs:
                dog = db.query(Dog).filter(Dog.id == dog_data['dog_id']).first()
                if not dog:
                    continue

                results_by_dog[dog.id] = {
                    "id": dog.id,
                    "name": dog.name,
                    "breed": dog.breed,
                    "age": dog.age,
                    "description": dog.description,
                    "average_similarity": dog_data['avg_similarity'],
                    "images": []
                }

                for result in dog_data['photos']:
                    results_by_dog[dog.id]["images"].append({
                        "filename": result["filename"],
                        "path": result["file_path"],
                        "photo_id": result["photo_id"],
                        "similarity_score": result["similarity_score"]
                    })

            results_list = list(results_by_dog.values())
            response_data = {
                "message": "Search completed",
                "query": str(filtered_dogs[0]["dog_id"]) if filtered_dogs else "",
                "search_column": "id",
                "threshold": threshold,
                "results": results_list,
                "count": len(results_list)
            }
            
            print(f"[INFO] Search completed with {len(response_data['results'])} results")
            return JSONResponse(
                status_code=200,
                content=response_data
            )
            
        finally:
            db.close()
    
    except Exception as e:
        print(f"[ERROR] Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e
    
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()