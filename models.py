# models.py
from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, ForeignKey


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # jeśli chcesz mieć relację user → scanjobs:
    jobs: List["ScanJob"] = Relationship(back_populates="user")


class ScanJob(SQLModel, table=True):
    __tablename__ = "scanjob"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    filename: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="jobs")
    results: List["ScanResult"] = Relationship(back_populates="job")


class ScanResult(SQLModel, table=True):
    __tablename__ = "scanresult"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(
        sa_column=Column(ForeignKey("scanjob.id", ondelete="CASCADE"))
    )
    agent_name: str = Field(nullable=False)
    matches: List[str] = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=list
    )

    job: Optional[ScanJob] = Relationship(back_populates="results")
