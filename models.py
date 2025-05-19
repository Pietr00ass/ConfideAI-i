from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password: str
    is_active: bool = Field(default=False, index=True)
    name: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    two_factor_secret: Optional[str] = Field(default=None)
    is_2fa_enabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relacja do wyników analiz
    results: List["AnalysisResult"] = Relationship(back_populates="user")

class AnalysisResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Przechowujemy listy wrażliwych danych w kolumnie JSON
    emails: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    pesel_numbers: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    credit_cards: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))

    # Predykcje ML jako słownik JSON (opcjonalne)
    ml_predictions: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))

    # Podsumowanie analizy (tekst generowany przez AI)
    summary: Optional[str] = Field(default=None)

    # Relacja do użytkownika
    user: Optional[User] = Relationship(back_populates="results")
