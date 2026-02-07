from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.config.database import Base


class Dog(Base):
    """Database model for dogs table (basic dog info)"""
    __tablename__ = 'dogs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    breed = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
