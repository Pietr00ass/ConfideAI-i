# db.py
import os
from sqlmodel import SQLModel, create_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(bind=engine)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
