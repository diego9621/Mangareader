from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from app.core.reader import list_chapters
from app.services.cover_service import cover_path_for_manga_dir
from app.services.library_service import get_library, sync_library
from desktop.workers import CoverWorker, CoverSignals


class LibraryController:
    def __init__(
        self,
        threadpool: QThreadPool,
        manga_list: QListWidget,
        cover_signals: CoverSignals,
        on_cover_done,
        clear_detail,
        set_selected_title,
    ):
        self.threadpool = threadpool
        self.manga_list = manga_list
        self.cover_signals = cover_signals
        self.cover_signals.done.connect(on_cover_done)
        self.clear_detail = clear_detail
        self.set_selected_title = set_selected_title
        self.rows = []
        self.manga_by_title: dict[str, Path] = {}
        self.mode = "library"
        self.query = ""

    def reload(self):
        rows = sync_library()
        self.rows = rows if rows else get_library()
        self.apply_filter()

    def set_mode(self, mode: str):
        self.mode = mode
        self.apply_filter()

    def set_query(self, q: str):
        self.query = (q or "").strip().lower()
        self.apply_filter()

    def apply_filter(self):
        rows = list(self.rows)

        if self.mode == "favorites":
            rows = [m for m in rows if getattr(m, "is_favorite", False)]
        elif self.mode == "continue":
            rows = [m for m in rows if getattr(m, "last_opened", None)]
            rows.sort(key=lambda m: m.last_opened, reverse=True)
        else:
            rows.sort(key=lambda m: m.title.lower())

        if self.query:
            rows = [m for m in rows if self.query in m.title.lower()]


        self.manga_by_title = {}
        for m in rows:
            if m.path:  
                self.manga_by_title[m.title] = Path(m.path)
            else:  
                self.manga_by_title[m.title] = None

        self.manga_list.blockSignals(True)
        self.manga_list.clear()

        for m in rows:
            title = m.title
            label = f"* {title}" if getattr(m, "is_favorite", False) else title


            source = getattr(m, "source", "local")
            if source != "local":
                label = f"🌐 {label}"  

            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, title)


            if m.path:  
                manga_dir = Path(m.path)
                cover = cover_path_for_manga_dir(manga_dir)
                if cover.exists():
                    it.setIcon(QIcon(str(cover)))
                else:
                    ch = list_chapters(manga_dir)
                    if ch:
                        self.threadpool.start(CoverWorker(title, manga_dir, ch[0], self.cover_signals))
            else:  
                cover_url = getattr(m, "cover_url", None)
                if cover_url:


                    pass

            self.manga_list.addItem(it)

        self.manga_list.blockSignals(False)

        if self.manga_list.count():
            self.manga_list.setCurrentRow(0)
            it = self.manga_list.currentItem()
            if it:
                self.set_selected_title(it.data(Qt.UserRole) or "")
        else:
            self.clear_detail()
