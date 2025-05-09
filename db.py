# db.py
import os
from sqlmodel import SQLModel, create_engine
from models import User, ScanJob, ScanResult

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./confideai.db")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)
