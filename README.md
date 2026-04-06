# Biometric ID Cat/Dog Backend

A FastAPI-based backend service for managing dog photos and biometric identification.

## Project Structure

```text
.
├── .gitignore
├── Dockerfile
├── Jenkinsfile
├── README.md
├── app/
│   ├── __init__.py
│   ├── attention/
│   │   ├── BAM.py
│   │   ├── DAM.py
│   │   ├── SAM.py
│   │   └── SEblock.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── settings.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dog.py
│   │   └── dog_photo.py
│   ├── network/
│   │   └── network.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── search.py
│   │   ├── searchbyimage.py
│   │   └── upload.py
│   └── utils/
│       ├── __init__.py
│       ├── crop.py
│       ├── embedding.py
│       ├── file_handler.py
│       ├── image_utils.py
│       └── model_loader.py
├── app.py
├── cam_result.png
├── cam_utils.py
├── deployment.yaml
├── docker-compose.yml
├── init.sql
├── main.py
└── requirements.txt
```

## Features

- Upload multiple photos for a single dog
- Automatic image type detection and validation
- PostgreSQL database storage for dog information
- File size validation (8 MB limit)
- RESTful API with automatic documentation

## Installation

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure database settings in `app/config/settings.py`

4. Run the application:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Health Check
- `GET /` - Test database connection
- `GET /health` - Health check

### Upload
- `POST /upload/photo` - Upload dog photos
  - Parameters:
    - `images`: List of image files (required)
    - `name`: Dog name (required)
    - `breed`: Dog breed (required)
    - `age`: Dog age (required)
    - `description`: Dog description (required)

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Schema

### dogs table
- `id`: Primary key
- `name`: Dog name
- `breed`: Dog breed
- `age`: Dog age
- `description`: Dog description
- `created_at`: Timestamp

### dog_photos table
- `id`: Primary key
- `dog_id`: Foreign key to dogs table
- `filename`: File name
- `file_path`: Full file path
- `file_size_bytes`: File size
- `file_extension`: Image extension
- `uploaded_at`: Timestamp

## Configuration

Edit `app/config/settings.py` to configure:
- Database URL
- Upload directory path
- File size limits
- CORS settings
