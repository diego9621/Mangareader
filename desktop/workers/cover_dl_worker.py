from PySide6.QtCore import QObject, Signal, QRunnable
from app.services.cover_dl_service import ensure_cover

class CoverDlSignals(QObject):
    done = Signal(str, str)

class CoverDlWorker(QRunnable):
    def __init__(self, key: str, url: str, signals: CoverDlSignals):
        super().__init__()
        self.key = key
        self.url = url
        self.signals = signals
    
    def run(self):
        try:
            p = ensure_cover(self.url)
            self.signals.done.emit(self.key, str(p) if p else "")
        except Exception:
            self.signals.done.emit(self.key, "")