# db.py
import os
from sqlmodel import SQLModel, create_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    # ręczne usuwanie starych tabel wraz z zależnościami
    with engine.begin() as conn:
        # kolejność nie ma znaczenia dzięki CASCADE
        conn.execute(text('DROP TABLE IF EXISTS scanresult CASCADE;'))
        conn.execute(text('DROP TABLE IF EXISTS scanjob CASCADE;'))
        conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE;'))
    # teraz twórz tylko te tabele, które są w kodzie (User)
    SQLModel.metadata.create_all(bind=engine)
