from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PIL import Image
from PIL.ImageQt import ImageQt

from app.core.reader import list_pages
from app.services.progress_services import load_progress, save_progress


class ReaderController:
    def __init__(self, scroll, image_label, page_slider, reader_info, set_title):
        self.scroll = scroll
        self.image_label = image_label
        self.page_slider = page_slider
        self.reader_info = reader_info
        self.set_title = set_title

        self.current_manga_dir: Path | None = None
        self.current_chapter_dir: Path | None = None
        self.pages: list[Path] = []
        self.page_idx = 0
        self.original_pixmap: QPixmap | None = None
        self.fit_mode = "width"
        self.direction = "LTR"

    def load_chapter(self, manga_dir: Path, chapter_dir: Path):
        self.current_manga_dir = manga_dir
        self.current_chapter_dir = chapter_dir
        self.pages = list_pages(chapter_dir)

        if not self.pages:
            self.page_idx = 0
            self.image_label.setText("No images found in chapter")
            self._sync_slider()
            self._update_info()
            return

        idx = load_progress(str(chapter_dir))
        idx = 0 if idx is None else idx
        self.page_idx = min(max(idx, 0), len(self.pages) - 1)
        self._sync_slider()
        self.show_page()

    def set_fit(self, fit_mode: str):
        self.fit_mode = fit_mode
        self.apply_pixmap()
        self._update_info()

    def set_direction(self, direction: str):
        self.direction = direction

    def set_page(self, idx: int):
        if not self.pages:
            return
        idx = min(max(idx, 0), len(self.pages) - 1)
        if idx == self.page_idx:
            return
        self.page_idx = idx
        self.show_page()

    def next_page(self):
        if self.pages and self.page_idx < len(self.pages) - 1:
            self.page_idx += 1
            self.show_page()

    def prev_page(self):
        if self.pages and self.page_idx > 0:
            self.page_idx -= 1
            self.show_page()

    def show_page(self):
        if not self.pages:
            return
        p = self.pages[self.page_idx]
        img = Image.open(p).convert("RGB")
        self.original_pixmap = QPixmap.fromImage(ImageQt(img))
        self.apply_pixmap()
        self._sync_slider(set_value=True)
        self._update_info()
        if self.current_chapter_dir:
            save_progress(str(self.current_chapter_dir), self.page_idx)
        self.set_title(f"Mangareader — {p.parent.parent.name} / {p.parent.name} — {self.page_idx+1}/{len(self.pages)}")

    def apply_pixmap(self):
        if not self.original_pixmap:
            return

        vw = max(1, self.scroll.viewport().width())
        vh = max(1, self.scroll.viewport().height())
        ow = self.original_pixmap.width()
        oh = self.original_pixmap.height()
        scale_h = vh / max(1, oh)

        if self.fit_mode == "height":
            if scale_h * ow < vw * 0.65:
                target = self.original_pixmap.scaledToWidth(vw, Qt.SmoothTransformation)
            else:
                target = self.original_pixmap.scaledToHeight(vh, Qt.SmoothTransformation)
        else:
            target = self.original_pixmap.scaledToWidth(vw, Qt.SmoothTransformation)

        self.image_label.setPixmap(target)
        self.image_label.adjustSize()

    def _sync_slider(self, set_value: bool = False):
        self.page_slider.blockSignals(True)
        self.page_slider.setMinimum(1)
        self.page_slider.setMaximum(max(1, len(self.pages)))
        if set_value:
            self.page_slider.setValue(self.page_idx + 1)
        self.page_slider.blockSignals(False)

    def _update_info(self):
        if not self.current_manga_dir or not self.current_chapter_dir or not self.pages:
            self.reader_info.setText("No chapter loaded")
            return
        self.reader_info.setText(
            f"{self.current_manga_dir.name}\n{self.current_chapter_dir.name}\nPage {self.page_idx+1} / {len(self.pages)}\nDirection: {self.direction}\nFit: {self.fit_mode}"
        )