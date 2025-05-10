from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship  # Poprawny import

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password: str  # Pole dla hasła
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relacja do ScanJob
    jobs: List["ScanJob"] = Relationship(back_populates="user")


class ScanJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relacja do ScanResult
    results: List["ScanResult"] = Relationship(back_populates="job")
    
    # Relacja z User
    user: "User" = Relationship(back_populates="jobs")


class ScanResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="scanjob.id")
    agent_name: str
    matches: List[str]  # Możesz używać tego w kontekście JSON lub innego typu

    # Relacja do ScanJob
    job: "ScanJob" = Relationship(back_populates="results")
