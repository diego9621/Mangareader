from PySide6.QtCore import QObject, Signal, QRunnable
from app.services.anilist_service import trending as anilist_trending, search as anilist_search

class DiscoverSignals(QObject):
    done = Signal(list, str)

class DiscoverWorker(QRunnable):
    def __init__(self, mode: str, query: str, signals: DiscoverSignals, page: int = 1, per_page: int = 24):
        super().__init__()
        self.mode = mode
        self.query = query
        self.signals = signals
        self.page = page
        self.per_page = per_page

    def run(self):
        try:
            items = anilist_search(self.query, self.page, self.per_page) if self.mode == "search" else anilist_trending(self.page, self.per_page)
            self.signals.done.emit(items, "")
        except Exception as e:
            self.signals.done.emit([], str(e))
