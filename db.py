from sqlmodel import SQLModel, create_engine
from models import User
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./confideai.db")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    # najpierw usuń stare tabele zależne
    with engine.connect() as conn:
        conn.execute('DROP TABLE IF EXISTS scanresult CASCADE;')
        conn.execute('DROP TABLE IF EXISTS scanjob CASCADE;')
        conn.execute('DROP TABLE IF EXISTS "user" CASCADE;')
    # potem utwórz na nowo tylko te, które są zdefiniowane w models.py
    SQLModel.metadata.create_all(bind=engine)
