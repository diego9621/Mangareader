from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtGui import QPixmap

from app.core.reader import list_chapters, list_pages
from app.services.cover_service import cover_path_for_manga_dir
from app.services.progress_services import load_progress


class DetailController:
    def __init__(self, detail_page, open_manga_callback, get_manga_by_title, make_chapter_row_widget=None):
        self.detail_page = detail_page
        self.open_manga = open_manga_callback
        self.get_manga_by_title = get_manga_by_title
        self.make_row = make_chapter_row_widget or getattr(detail_page, "make_chapter_row_widget", None)

    def show_library_title(self, title: str):
        m = self.get_manga_by_title().get(title)
        self.detail_page.detail_title.setText(title)
        self.detail_page.detail_sub.setText("")
        self.detail_page.detail_meta.setText("")
        self.detail_page.detail_desc.setText("")
        self.detail_page.set_genres([])
        self.detail_page.chapters_preview.clear()
        self.detail_page.detail_cover.clear()
        self.detail_page.btn_open_link.setVisible(False)

        if not m:
            return

        cover = cover_path_for_manga_dir(m)
        if cover.exists():
            pix = QPixmap(str(cover))
            if not pix.isNull():
                self.detail_page.detail_cover.setPixmap(
                    pix.scaled(self.detail_page.detail_cover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        self.refresh_detail_chapters(title)

    def compute_continue_target(self, manga_dir: Path):
        chapters = list_chapters(manga_dir)
        if not chapters:
            return None

        best_ch = chapters[0]
        best_idx = 0
        best_total = max(len(list_pages(manga_dir / best_ch)), 1)

        for ch in chapters:
            pages = list_pages(manga_dir / ch)
            total = max(len(pages), 1)
            idx = load_progress(str(manga_dir / ch))
            idx = 0 if idx is None else max(0, min(idx, total - 1))
            if idx > best_idx:
                best_ch, best_idx, best_total = ch, idx, total

        return best_ch, best_idx, best_total

    def refresh_detail_chapters(self, title: str):
        mdir = self.get_manga_by_title().get(title)
        self.detail_page.chapters_preview.clear()

        if not mdir:
            self.detail_page.detail_sub.setText("")
            return

        chapters = list_chapters(mdir)
        if not chapters:
            self.detail_page.detail_sub.setText("No chapters found")
            return

        cont = self.compute_continue_target(mdir)
        if cont:
            ch, idx, total = cont
            self.detail_page.detail_sub.setText(f"Continue: {ch}  •  p{idx+1}/{total}")
        else:
            self.detail_page.detail_sub.setText("")

        for ch in chapters:
            pages = list_pages(mdir / ch)
            total = max(len(pages), 1)
            idx = load_progress(str(mdir / ch))
            idx = 0 if idx is None else max(0, min(idx, total - 1))
            cur = idx + 1

            it = QListWidgetItem()
            it.setData(Qt.UserRole, ch)
            it.setSizeHint(QSize(0, 56))

            if self.make_row:
                w = self.make_row(ch, cur, total)
                self.detail_page.chapters_preview.addItem(it)
                self.detail_page.chapters_preview.setItemWidget(it, w)
            else:
                it.setText(f"{ch}  (p{cur}/{total})")
                self.detail_page.chapters_preview.addItem(it)

    def on_chapter_preview_activated(self, item: QListWidgetItem):
        ch = item.data(Qt.UserRole)
        if not ch:
            return
        title = self.detail_page.detail_title.text()
        if title:
            self.open_manga(title, chapter=ch)