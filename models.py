from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, ForeignKey


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScanJob(SQLModel, table=True):
    __tablename__ = "scanjob"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field()  # nie trzeba nullable=True, bo to pole obowiązkowe
    created_at: datetime = Field(default_factory=datetime.utcnow)

    results: List["ScanResult"] = Relationship(back_populates="job")


class ScanResult(SQLModel, table=True):
    __tablename__ = "scanresult"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(  # usuwamy nullable=..., pozostawiamy tylko sa_column
        sa_column=Column(ForeignKey("scanjob.id", ondelete="CASCADE"))
    )
    agent_name: str = Field()
    matches: List[str] = Field(  # tu też usuwamy nullable z Field
        sa_column=Column(JSON, nullable=False),
        default_factory=list
    )

    job: Optional[ScanJob] = Relationship(back_populates="results")
