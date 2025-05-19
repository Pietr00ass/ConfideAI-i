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
    avatar_url: Optional[str] = None
    two_factor_secret: Optional[str] = None
    is_2fa_enabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AnalysisResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    emails: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    pesel_numbers: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    credit_cards: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    ml_predictions: Optional[str] = None
    summary: str | None = Field(default=None)


