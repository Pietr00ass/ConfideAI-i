# db.py
import os
from sqlmodel import SQLModel, create_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    with engine.begin() as conn:
        conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE;'))
        conn.execute(text('DROP TABLE IF EXISTS scanjob CASCADE;'))
        conn.execute(text('DROP TABLE IF EXISTS scanresult CASCADE;'))
    SQLModel.metadata.create_all(bind=engine)
