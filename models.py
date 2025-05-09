from sqlmodel import SQLModel, Field, Column
from typing import Optional List
from datetime import datetime
from sqlalchemy import JSON

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class ScanJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScanResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="scanjob.id")
    agent_name: str
    matches: List[str] = Field(sa_column=Column(JSON), default_factory=list)
