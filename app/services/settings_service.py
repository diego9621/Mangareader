from sqlmodel import select
from app.db.session import get_session
from app.models.settings import Settings

def get_library_root() -> str | None:
    with get_session() as session:
        row = session.exec(select(Settings).where(Settings.id == 1)).first()
        return row.library_root if row else None

def set_library_root(path: str):
    with get_session() as session:
        row = session.exec(select(Settings).where(Settings.id == 1)).first()
        if row:
            row.library_root = path
        else:
            session.add(Settings(id=1, library_root=path))
        session.commit()
        