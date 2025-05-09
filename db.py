from sqlmodel import SQLModel, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./confideai.db")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    # importujemy wszystkie modele, żeby je zarejestrować
    from models import User, ScanJob, ScanResult
    SQLModel.metadata.create_all(engine)
