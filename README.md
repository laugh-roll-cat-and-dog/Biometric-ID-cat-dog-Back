# Biometric ID Cat/Dog Backend

A FastAPI-based backend service for managing dog photos and biometric identification.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── c

uvicorn main:app --host 0.0.0.0 --port 8000 --reloadonfig/
│   │   ├── __init__.py
│   │   ├── settings.py       # Application settings and configuration
│   │   └── database.py       # Database connection setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dog.py           # Dog model
│   │   └── dog_photo.py     # DogPhoto model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   └── upload.py        # Photo upload endpoints
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py  # File handling utilities
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
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
