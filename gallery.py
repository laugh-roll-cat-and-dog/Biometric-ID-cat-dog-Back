import uuid
from pathlib import Path
import torch.nn.functional as F
import cv2
from PIL import Image
from app.config.database import SessionLocal
from app.config.settings import settings
from app.models import Dog, DogPhoto
from app.utils.file_handler import detect_image_type
from app.utils.embedding import embed_image
from app.utils.crop import crop_image
import shutil
import os

def upload_to_database(source_dir, dog_name=None, breed="Unknown", age=None, description="Uploaded from gallery"):
    """
    Upload all photos from a gallery folder to database
    
    Args:
        source_dir: Path to gallery folder (e.g., gallery_data/17/gallery)
        dog_name: Name of the dog. If not provided, auto-detects from path (e.g., "17" from .../17/gallery)
        breed: Breed of the dog (default: "Unknown")
        age: Age of the dog (optional)
        description: Description of the dog (default: "Uploaded from gallery")
    """

    pathlist = []
    print(f"Source directory: {source_dir}")
    for file_name in os.listdir(source_dir):
        if not file_name.startswith("."):
            pathlist.append(file_name)
    pathlist.sort(key=int)
    print("list", pathlist)

    source_path = Path(source_dir)
    print(f"Source directory: {source_path}")
    db = SessionLocal()
    
    # if not source_path.exists():
    #     print(f"Error: Directory {source_dir} not found")
    #     db.close()
    #     return
    for dog_name in pathlist:
        print(f"Processing dog: {dog_name}")
        dog_folder = source_path / dog_name / "gallery"
        if not dog_folder.exists():
            print(f"Warning: Gallery folder not found for {dog_name} at {dog_folder}. Skipping.")
            continue
        print("step1")
        # Create dog record in database
        new_dog = Dog(
            name=dog_name,
            breed=dog_name,
            age=1,
            description="Uploaded from gallery"
        )
        print("step2")
        db.add(new_dog)
        db.commit()
        db.refresh(new_dog)
        print(f"Dog record created with ID: {new_dog.id}")
        
        # Create folder structure for this dog
        foldername = f"dog_{new_dog.id}"
        dog_folder_dest = settings.BASE_UPLOAD_DIR / foldername
        dog_folder_dest.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Created/verified dog folder: {dog_folder_dest}")

        nose_folder = settings.BASE_UPLOAD_DIR / foldername / "nose"
        nose_folder.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Created/verified nose folder: {nose_folder}")

        # Process each image in the gallery
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        images = [f for f in (source_path / dog_name / "gallery").iterdir()
                  if f.is_file() and f.suffix.lower() in image_extensions]

        if not images:
            print(f"[WARN] No images found for {dog_name} in {dog_folder}. Skipping.")
            continue

        print(f"[INFO] Found {len(images)} images for {dog_name}")
        dog_id_value = new_dog.id

        for image_file in images:
            try:
                # Copy image to dog folder with unique name
                unique_filename = f"{uuid.uuid4().hex}{image_file.suffix}"
                destination = dog_folder_dest / unique_filename
                shutil.copy2(str(image_file), str(destination))
                bytes_written = destination.stat().st_size
                print(f"[INFO] File copied to: {destination}")

                extension = detect_image_type(destination)
                final_destination = destination.with_suffix(f".{extension}")
                if final_destination != destination:
                    destination.rename(final_destination)
                    destination = final_destination
                    print(f"[INFO] File renamed to final destination: {destination}")

                # Generate embedding for image
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
                    nose_filename = f"{uuid.uuid4().hex}_nose{destination.suffix}"
                    nose_destination = nose_folder / nose_filename
                    shutil.copy2(str(destination), str(nose_destination))
                    nose_emb = embed_image(nose_destination)
                    print(f"[WARN] No nose detected. Copied original image to: {nose_destination}")

                # Save photo record linked to the dog
                new_photo = DogPhoto(
                    dog_id=dog_id_value,
                    filename=destination.name,
                    file_path=str(destination),
                    file_size_bytes=bytes_written,
                    file_extension=extension,
                    embedding=F.normalize(emb[0], p=2, dim=0),
                    cropped_nose_path=str(destination),
                    nose_embedding=F.normalize(emb[0], p=2, dim=0)
                )
                db.add(new_photo)
                db.commit()
                db.refresh(new_photo)
                print(f"[INFO] Photo saved to database with ID: {new_photo.id}")

            except Exception as e:
                db.rollback()
                print(f"[ERROR] Failed to process {image_file.name}: {e}")
    # # Auto-detect dog_name from path if not provided
    # if dog_name is None:
    #     # Extract from path: .../gallery_data/17/gallery -> "17"
    #     path_parts = source_path.parts
    #     if "gallery" in path_parts:
    #         gallery_idx = path_parts.index("gallery")
    #         if gallery_idx > 0:
    #             dog_name = path_parts[gallery_idx - 1]
    #             print(f"Auto-detected dog name from path: {dog_name}")
    #     if dog_name is None:
    #         print("Error: Could not auto-detect dog name from path. Please provide dog_name parameter.")
    #         db.close()
    #         return
    
    # try:
    #     # Check if dog with this name exists, if not create it
    #     existing_dog = db.query(Dog).filter(Dog.name == dog_name).first()
    #     if existing_dog is None:
    #         print(f"Creating new dog record with name: {dog_name}")
    #         dog_record = Dog(
    #             name=dog_name,
    #             breed=breed,
    #             age=age,
    #             description=description
    #         )
    #         db.add(dog_record)
    #         db.commit()
    #         db.refresh(dog_record)
    #         print(f"Dog created with ID: {dog_record.id}")
    #     else:
    #         dog_record = existing_dog
    #         print(f"Using existing dog record - ID: {dog_record.id}, Name: {dog_record.name}")
        
    #     dog_id_value = dog_record.id
        
    #     # Create dog folder structure if not exists
    #     foldername = f"dog_{dog_id_value}"
    #     dog_folder = settings.BASE_UPLOAD_DIR / foldername
    #     dog_folder.mkdir(parents=True, exist_ok=True)
        
    #     nose_folder = dog_folder / "nose"
    #     nose_folder.mkdir(parents=True, exist_ok=True)
    #     print(f"Created/verified dog folder: {dog_folder}")
        
    #     # Get all image files
    #     image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    #     images = [f for f in source_path.iterdir() 
    #               if f.is_file() and f.suffix.lower() in image_extensions]
        
    #     if not images:
    #         print(f"No images found in {source_dir}")
    #         db.close()
    #         return
        
    #     print(f"Found {len(images)} images for dog: {dog_name}")
    #     uploaded_count = 0
        
    #     # Process each image
    #     for image_file in images:
    #         try:
    #             print(f"\nProcessing: {image_file.name}")
                
    #             # Copy image to dog folder with unique name
    #             unique_filename = f"{uuid.uuid4().hex}{image_file.suffix}"
    #             destination = dog_folder / unique_filename
                
    #             # Copy file
    #             shutil.copy2(str(image_file), str(destination))
    #             file_size = destination.stat().st_size
    #             extension = destination.suffix.lstrip('.')
    #             print(f"File copied to: {destination}")
                
    #             # Generate embedding for full image
    #             emb = embed_image(destination)
    #             print(f"Embedding generated")
                
    #             # Crop image to get nose region
    #             nose_crop = crop_image(destination)
    #             print(f"Image processing complete")
                
    #             # Save cropped nose image if detected
    #             nose_destination = None
    #             nose_emb = None
    #             if nose_crop is not None:
    #                 nose_filename = f"{uuid.uuid4().hex}_nose.jpeg"
    #                 nose_destination = nose_folder / nose_filename
                    
    #                 # Convert BGR to RGB and save using PIL
    #                 nose_rgb = cv2.cvtColor(nose_crop, cv2.COLOR_BGR2RGB)
    #                 nose_pil = Image.fromarray(nose_rgb)
    #                 nose_pil.save(str(nose_destination), 'JPEG')
    #                 print(f"Nose saved to: {nose_destination}")
                    
    #                 nose_emb = embed_image(nose_destination)
    #                 print(f"Nose embedding generated")
    #             else:
    #                 print(f"Warning: No nose detected in image")
                
    #             # Save photo record to database
    #             new_photo = DogPhoto(
    #                 dog_id=dog_id_value,
    #                 filename=unique_filename,
    #                 file_path=str(destination),
    #                 file_size_bytes=file_size,
    #                 file_extension=extension,
    #                 embedding=F.normalize(emb[0], p=2, dim=0),
    #                 cropped_nose_path=str(nose_destination) if nose_destination else None,
    #                 nose_embedding=F.normalize(nose_emb[0], p=2, dim=0) if nose_emb is not None else None
    #             )
    #             db.add(new_photo)
    #             db.commit()
    #             db.refresh(new_photo)
    #             print(f"Photo saved to database with ID: {new_photo.id}")
    #             uploaded_count += 1
                
    #         except Exception as e:
    #             db.rollback()
    #             print(f"Error uploading {image_file.name}: {e}")
        
    #     print(f"\n✓ Upload complete! {uploaded_count}/{len(images)} images successfully uploaded")
        
    # except Exception as e:
    #     db.rollback()
    #     print(f"Database error: {e}")
    # finally:
    #     db.close()

if __name__ == "__main__":
    # Auto-detects dog name from path (will extract "17" from .../17/gallery)
    gallery_path = "/Users/withwws/Documents/FinalProject/APP dev/Biometric-ID-cat-dog-Back/gallery_data"
    
    upload_to_database(gallery_path)
    
    # Or you can manually specify the name:
    # upload_to_database(gallery_path, dog_name="Buddy", breed="Golden Retriever", age=3)
