from pathlib import Path
from sqlmodel import select
from app.core.config import MANGA_DIR
from app.core.filesystem import list_dirs
from app.db.session import get_session
from app.models.manga import Manga
from app.services.settings_service import get_library_root
from datetime import datetime

def sync_library():
    root = get_library_root()
    if not root:
        return []

    root_path = Path(root)
    manga_names = list_dirs(root_path)

    with get_session() as session:
        existing = {m.path for m in session.exec(select(Manga)).all()}
        for name in manga_names:
            p = str(root_path / name)
            if p not in existing:
                session.add(Manga(path=p, title=name))
        session.commit()
        return session.exec(select(Manga).order_by(Manga.title)).all()

def get_library():
    with get_session() as session:
        return session.exec(select(Manga).order_by(Manga.title)).all()

def toggle_favorite(manga_title: str):
    with get_session() as session:
        m = session.exec(select(Manga).where(Manga.title == manga_title)).first()
        if not m:
            return
        m.last_opened = datetime.utcnow()
        m.open_count += 1
        session.commit()

def mark_opened(title: str):
    with get_session() as session:
        m = session.exec(select(Manga). where(Manga.title == title)).first() 
        if not m:
            return
        m.last_opened = datetime.utcnow()
        m.open_count = (m.open_count or 0)
        session.commit() 
