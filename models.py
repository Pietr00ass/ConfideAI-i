from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, ForeignKey

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # relacja do zadań skanowania
    jobs: List["ScanJob"] = Relationship(back_populates="user")

class ScanJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    results: List["ScanResult"] = Relationship(back_populates="job")

class ScanResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="scanjob.id")
    agent_name: str
    matches: List[str] = Field(sa_column=Column(JSON, nullable=False), default_factory=list)
    job: ScanJob = Relationship(back_populates="results")
