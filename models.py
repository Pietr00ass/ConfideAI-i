from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import JSON, ForeignKey


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, nullable=False, unique=True)
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScanJob(SQLModel, table=True):
    __tablename__ = "scanjob"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relacja do wyników
    results: List["ScanResult"] = Relationship(back_populates="job")


class ScanResult(SQLModel, table=True):
    __tablename__ = "scanresult"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(
        sa_column=Column(ForeignKey("scanjob.id", ondelete="CASCADE")),
        nullable=False,
    )
    agent_name: str = Field(nullable=False)
    matches: List[str] = Field(
        sa_column=Column(JSON, nullable=False),
        default_factory=list
    )

    # relacja zwrotna
    job: Optional[ScanJob] = Relationship(back_populates="results")
