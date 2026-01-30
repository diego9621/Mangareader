from pathlib import Path
from PySide6.QtCore import QObject, Signal, QRunnable
from app.services.cover_service import build_cover

class CoverSignals(QObject):
    done = Signal(str, str)

class CoverWorker(QRunnable):
    def __init__(self, title: str, manga_dir: Path, first_chapter: str, signals: CoverSignals):
        super().__init__()
        self.title = title
        self.manga_dir = manga_dir
        self.first_chapter = first_chapter
        self.signals = signals

    def run(self):
        try:
            p = build_cover(self.manga_dir, self.first_chapter)
            if p:
                self.signals.done.emit(self.title, str(p))
        except Exception:
            return