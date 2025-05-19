from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, ForeignKey

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

    # relacja zwrotna do wyników analiz
    results: List["AnalysisResult"] = Relationship(back_populates="user")


class AnalysisResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # JSON-owe kolumny z listami wrażliwych danych
    emails: List[str] = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=list
    )
    pesel_numbers: List[str] = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=list
    )
    credit_cards: List[str] = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=list
    )

    # predykcje ML jako słownik (opcjonalnie)
    ml_predictions: Optional[Dict[str, Any]] = Field(
        sa_column=Column(JSON, nullable=True),
        default=None
    )

    # tekstowe podsumowanie wygenerowane przez AI
    summary: Optional[str] = Field(default=None)

    # relacja do właściciela wyniku
    user: Optional[User] = Relationship(back_populates="results")
