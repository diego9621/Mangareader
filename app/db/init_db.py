from sqlmodel import SQLModel
from app.db.session import engine
from app.models import Manga, Progress, Settings, Chapter, Page, DownloadQueue

def init_db():

    SQLModel.metadata.create_all(engine)
