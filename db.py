from sqlmodel import SQLModel, create_engine
from models import User
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./confideai.db")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
