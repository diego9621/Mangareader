from sqlmodel import SQLModel, create_engine, Session
from app.core.config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

def get_session():
    return Session(engine)
