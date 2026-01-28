from pathlib import Path
from sqlmodel import select
from app.core.config import MANGA_DIR
from app.core.filesystem import list_dirs
from app.db.session import get_session
from app.models.manga import Manga

def sync_library():
    with get_session() as session:
        existing = {m.path for m in session.exec(select(Manga)).all()}

        for name in list_dirs(MANGA_DIR):
            path = str(MANGA_DIR / name)
            if path not in existing:
                session.add(Manga(path=path, title=name))
        session.commit()

def get_library():
    sync_library()
    with get_session() as session:
        return session.exec(select(Manga))
