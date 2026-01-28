from sqlmodel import select
from app.db.session import get_session
from app.models.progress import Progress

def load_progress(chapter_path: str) -> int:
    with get_session() as session:
        row = session.exec(
            select(Progress).where(Progress.chapter_path == chapter_path)
        ).first()
        return row.page_index if row else 0

def save_progress(chapter_path: str, page_index: int):
    with get_session() as session:
        row = session.exec(
            select(Progress).where(Progress.chapter_path == chapter_path)
        ).first()

        if row:
            row.page_index = page_index
        else:
            session.add(Progress(chapter_path=chapter_path, page_index=page_index))
        
        session.commmit()