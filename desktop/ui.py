from app.services.progress_services import load_progress, save_progress
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QListWidget, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QScrollArea
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PIL import Image
from PIL.ImageQt import ImageQt

from app.core.config import MANGA_DIR
from app.core.filesystem import list_dirs
from app.core.reader import list_chapters, list_pages

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mangareader")
        self.resize(1200, 800)

        self.manga_list = QListWidget()
        self.chapter_list = QListWidget()
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.image_label)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("manga"))
        left_layout.addWidget(self.manga_list)

        mid = QWidget()
        mid_layout = QVBoxLayout(mid)
        mid_layout.addWidget(QLabel("Chapters"))
        mid_layout.addWidget(self.chapter_list)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(mid)
        splitter.addWidget(self.scroll)
        splitter.setStretchFactor(2, 1)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

        self.current_manga_dir: Path | None = None
        self.current_chapter_dir: Path | None = None
        self.pages: list[Path] = []
        self.page_idx = 0

        self.manga_list.addItems(list_dirs(MANGA_DIR))
        self.manga_list.currentTextChanged.connect(self.on_manga_selected)
        self.chapter_list.currentTextChanged.connect(self.on_chapter_selected)

        if self.manga_list.count():
            self.manga_list.setCurrentRow(0)
    
    def on_manga_selected(self, manga_name: str):
        self.current_manga_dir = MANGA_DIR / manga_name
        self.chapter_list.clear()
        chapters = list_chapters(self.current_manga_dir)
        self.chapter_list.addItems(chapters)
        if self.chapter_list.count():
            self.chapter_list.setCurrentRow(0)
        else:
            self.pages = []
            self.page_idx = 0
            self.image_label.setText("No chapters found")

    def on_chapter_selected(self, chapter_name: str):
       if not self.current_manga_dir:
           return
       self.current_chapter_dir = self.current_chapter_dir / chapter_name
       self.pages = list_pages(self.current_chapter_dir)
       self.page_idx = load_progress(str(self.current_chapter_dir))
       if self.pages:
           self.show_page()
       else:
           self.image_label.setText("No images found in chapter")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_Space):
            self.next_page()
            return
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_Backspace):
            self.prev_page()
            return
        super().keyPressEvent(event)

    def next_page(self):
        if not self.pages:
            return
        if self.page_idx > 0:
            self.page_idx -= 1
            self.show_page()

    def show_page(self):
        p = self.pages[self.page_idx]
        img = Image.open(p).convert("RGB")
        qimg = ImageQt(img)
        pix = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pix)
        save_progress(str(p.parent), self.page_idx)
        self.setWindowTitle(f"Mangareader - {p.parent.parent.name} / {p.parent.name} - {self.page_idx+1}/{len(self.pages)}")