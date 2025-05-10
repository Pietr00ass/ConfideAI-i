from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship 
from sqlalchemy import Column, JSON, ForeignKey

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password: str  # Pole dla hasła
    is_active: bool = Field(default=False, index=True) 
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
