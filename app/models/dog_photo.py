from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON
from app.config.database import Base
from pgvector.sqlalchemy import Vector


class DogPhoto(Base):
    """Database model for dog photos (multiple photos per dog)"""
    __tablename__ = 'dog_photos'
    
    id = Column(Integer, primary_key=True)
    dog_id = Column(Integer, nullable=False)
    filename = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_extension = Column(String(10), nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    embedding = Column(Vector(1024), nullable=False)  # Vector embedding for biometric identification
    cropped_nose_path = Column(String(500), nullable=True)  # Path to cropped nose image
    nose_embedding = Column(Vector(1024), nullable=True)  # Embedding of cropped nose
