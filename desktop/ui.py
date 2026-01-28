from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QListWidget, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QScrollArea, QFileDialog, QLineEdit
from PySide6.QtWidgets import QDockWidget, QRadioButton, QButtonGroup, QSlider, QFormLayout, QGroupBox
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import QSize, QRunnable, QThreadPool, QObject, Signal
from PySide6.QtGui import QIcon
from app.services.cover_service import cover_path_for_manga_dir, build_cover
from app.core.reader import list_chapters
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PIL import Image
from PIL.ImageQt import ImageQt

from app.core.config import MANGA_DIR
from app.core.reader import list_chapters, list_pages
from app.services.settings_service import set_library_root, get_library_root
from app.services.library_service import sync_library, get_library
from app.services.progress_services import load_progress, save_progress

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
        p = build_cover(self.manga_dir, self.first_chapter)
        if p:
            self.signals.done.emit(self.title, str(p))
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mangareader")
        self.resize(1200, 800)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search titles...")
        self.search.textChanged.connect(self.apply_filter)

        self.manga_list = QListWidget()
        self.manga_list.setViewMode(QListWidget.IconMode)
        self.manga_list.setIconSize(QSize(160, 220))
        self.manga_list.setGridSize(QSize(190, 270))
        self.manga_list.setResizeMode(QListWidget.Adjust)
        self.manga_list.setMovement(QListWidget.Static)
        self.manga_list.setSpacing(10)
        self.manga_list.setWordWrap(True)
        self.chapter_list = QListWidget()

        self.image_label = QLabel("Import a library folder to begin")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.image_label)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        t1 = QLabel("Library")
        t1.setStyleSheet("font-weight:600;")
        left_layout.addWidget(t1)
        left_layout.addWidget(self.search)
        left_layout.addWidget(self.manga_list)

        mid = QWidget()
        mid_layout = QVBoxLayout(mid)
        t2 = QLabel("Chapters")
        t2.setStyleSheet("font-weight:600;")
        mid_layout.addWidget(t2)
        mid_layout.addWidget(self.chapter_list)

        self.splitter = QSplitter()
        self.splitter.addWidget(left)
        self.splitter.addWidget(mid)
        self.splitter.addWidget(self.scroll)
        self.splitter.setStretchFactor(2, 1)

        self.left_panel = left
        self.mid_panel = mid
        self.reader_panel = self.scroll
        self.ui_mode = "library"

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.addWidget(self.splitter)
        self.setCentralWidget(root)
        self.threadpool = QThreadPool.globalInstance()
        self.cover_signals = CoverSignals()
        self.cover_signals.done.connect(self.on_cover_done)

        menu = self.menuBar().addMenu("Library")
        action = menu.addAction("Import Library Folder…")
        action.triggered.connect(self.import_library_folder)

        self.reader_dock = QDockWidget("Reader", self)
        self.reader_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.reader_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

        dock_body = QWidget()
        dock_layout = QVBoxLayout(dock_body)

        fit_box = QGroupBox("Fit")
        fit_layout = QVBoxLayout(fit_box)
        self.fit_width_btn = QRadioButton("Width")
        self.fit_heigth_btn = QRadioButton("Heigth")
        self.fit_width_btn.setChecked(True)
        fit_layout.addWidget(self.fit_width_btn)
        fit_layout.addWidget(self.fit_heigth_btn)

        fit_group = QButtonGroup(self)
        fit_group.addButton(self.fit_width_btn)
        fit_group.addButton(self.fit_heigth_btn)
        dir_box = QGroupBox("Direction")
        dir_layout = QVBoxLayout(dir_box)
        self.dir_ltr_btn = QRadioButton("Left -> Right")
        self.dir_rtl_btn = QRadioButton("Right -> Left")
        self.dir_ltr_btn.setChecked(True)
        dir_layout.addWidget(self.dir_ltr_btn)
        dir_layout.addWidget(self.dir_rtl_btn)
        
        dir_group = QButtonGroup(self)
        dir_group.addButton(self.dir_ltr_btn)
        dir_group.addButton(self.dir_rtl_btn)

        self.page_slider = QSlider(Qt.Orientation.Horizontal)
        self.page_slider.setMinimum(1)
        self.page_slider.setMaximum(1)
        self.page_slider.setValue(1)

        self.reader_info = QLabel("No chapter loaded")
        self.reader_info.setWordWrap(True)

        dock_layout.addWidget(fit_box)
        dock_layout.addWidget(dir_box)
        dock_layout.addWidget(QLabel("Page"))
        dock_layout.addWidget(self.page_slider)
        dock_layout.addWidget(self.reader_info)
        dock_layout.addStretch(1)

        self.reader_dock.setWidget(dock_body)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.reader_dock)

        self.current_manga_dir: Path | None = None
        self.current_chapter_dir: Path | None = None
        self.pages: list[Path] = []
        self.page_idx = 0
        self.original_pixmap = None
        self.fit_mode = "width"
        self.reading_direction = "LTR"

        self.manga_by_title: dict[str, Path] = {}
        self.all_manga: list[str] = []

        self.manga_list.currentTextChanged.connect(self.on_manga_selected)
        self.chapter_list.currentTextChanged.connect(self.on_chapter_selected)
        self.manga_list.setUniformItemSizes(True)
        self.chapter_list.setUniformItemSizes(True)
        self.manga_list.setSpacing(1)
        self.chapter_list.setSpacing(1)

        self.reload_library()
        self.fit_width_btn.toggled.connect(self.on_fit_changed)
        self.fit_heigth_btn.toggled.connect(self.on_fit_changed)
        self.dir_ltr_btn.toggled.connect(self.on_direction_changed)
        self.dir_rtl_btn.toggled.connect(self.on_direction_changed)
        self.page_slider.valueChanged.connect(self.on_page_slider_changed)
        self.set_ui_mode("library")

    def import_library_folder(self):
        start = get_library_root() or str(MANGA_DIR)
        path = QFileDialog.getExistingDirectory(self, "Select library folder", start)
        if not path:
            return
        set_library_root(path)
        self.reload_library()
    
    def on_cover_done(self, title: str, cover_path: str): 
        for i in range(self.manga_list.count()):
            it = self.manga_list.item(i)
            if it.data(Qt.ItemDataRole.UserRole) == title:
                it.setIcon(QIcon(cover_path))
                break

    def set_ui_mode(self, mode: str):
        self.ui_mode = mode
        is_library = mode == "library"
        self.mid_panel.setVisible(not is_library)
        self.reader_panel.setVisible(not is_library)
        self.reader_dock.setVisible(not is_library)
        if is_library:
            self.splitter.setSizes([900, 0, 0])
        else:
            self.splitter.setSizes([260, 260, 900])
    def reload_library(self):
        rows = sync_library()
        rows = rows if rows else get_library()
        self.manga_by_title = {m.title: Path(m.path) for m in rows} if rows else {}
        self.all_manga = list(self.manga_by_title.keys())
        self.apply_filter()

    def apply_filter(self):
        q = (self.search.text() or "").strip().lower()
        titles = self.all_manga if not q else [t for t in self.all_manga if q in t.lower()]
        placeholder = QIcon()
        self.manga_list.blockSignals(True)
        self.manga_list.clear()

        for title in titles:
            manga_dir = self.manga_by_title.get(title)
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, title)

            if manga_dir:
                cover = cover_path_for_manga_dir(manga_dir)
                if cover.exists():
                    item.setIcon(QIcon(str(cover)))
                else:
                    ch = list_chapters(manga_dir)
                    if ch:
                        w = CoverWorker(title, manga_dir, ch[0], self.cover_signals)
                        self.threadpool.start(w)
            self.manga_list.addItem(item)
        self.manga_list.blockSignals(False)


    def apply_pixmap(self):
        if not self.original_pixmap:
            return
        vw = self.scroll.viewport().width()
        vh = self.scroll.viewport().height()
        if vw <= 1 or vh <= 1:
            self.image_label.setPixmap(self.original_pixmap)
            return
        if self.fit_mode == "height":
            target = self.original_pixmap.scaledToHeight(vh, Qt.TransformationMode.SmoothTransformation)
        else:
            target = self.original_pixmap.scaledToWidth(vw, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(target)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_pixmap()

    def on_manga_selected(self, manga_name: str):
        self.current_manga_dir = self.manga_by_title.get(manga_name)
        if not self.current_manga_dir:
            return
        self.set_ui_mode("reading")
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
        self.current_chapter_dir = self.current_manga_dir / chapter_name
        self.pages = list_pages(self.current_chapter_dir)
        if not self.pages:
            self.page_idx = 0
            self.image_label.setText("No images found in chapter")
            return
        idx = load_progress(str(self.current_chapter_dir))
        self.page_idx = min(max(idx, 0), len(self.pages) - 1)
        self.page_slider.blockSignals(True)
        self.page_slider.setMinimum(1)
        self.page_slider.setMaximum(len(self.pages))
        self.page_slider.setValue(self.page_idx + 1)
        self.page_slider.blockSignals(False)
        self.update_reader_info()
        self.show_page()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.set_ui_mode("library")
            return
        if event.key() == Qt.Key.Key_S:
            self.reader_dock.setVisible(not self.reader_dock.isVisible())
            return
        
        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_Space):
            if self.reading_direction == "RTL":
                self.prev_page()
            else:
                self.next_page()
            return
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_Backspace):
            if self.reading_direction == "RTL":
                self.next_page()
            else:
                self.prev_page()
            return
        super().keyPressEvent(event)

    def next_page(self):
        if not self.pages:
            return
        if self.page_idx < len(self.pages) - 1:
            self.page_idx += 1
            self.show_page()

    def prev_page(self):
        if not self.pages:
            return
        if self.page_idx > 0:
            self.page_idx -= 1
            self.show_page()
    
    def on_fit_changed(self):
        self.fit_mode = "width" if self.fit_width_btn.isChecked() else "height"
        self.apply_pixmap()
        self.update_reader_info()
    
    def on_direction_changed(self):
        self.reading_direction = "RTL" if self.dir_rtl_btn.isChecked() else "LTR"
    
    def update_reader_info(self):
        if not self.current_manga_dir or not self.current_chapter_dir or not self.pages:
            self.reader_info.setText("No chapter loaded")
            return
        fit = "width" if self.fit_width_btn.isChecked() else "height"
        direction = "RTL" if self.dir_rtl_btn.isChecked() else "LTR"
        self.reader_info.setText(
            f"{self.current_manga_dir.name}\n{self.current_chapter_dir.name}\nPage {self.page_idx+1} / {len(self.pages)}\nDirection: {direction}\nFit: {fit}"
        )
        
    def on_page_slider_changed(self, value: int):
        if not self.pages:
            return
        idx = value - 1
        if idx == self.page_idx:
            return
        self.page_idx = idx
        self.show_page()

    def show_page(self):
        p = self.pages[self.page_idx]
        img = Image.open(p).convert("RGB")
        pix = QPixmap.fromImage(ImageQt(img))
        self.original_pixmap = pix
        self.apply_pixmap()
        self.page_slider.blockSignals(True)
        self.page_slider.setValue(self.page_idx + 1)
        self.page_slider.blockSignals(False)
        self.update_reader_info()
        if self.current_chapter_dir:
            save_progress(str(self.current_chapter_dir), self.page_idx)
        self.setWindowTitle(f"Mangareader — {p.parent.parent.name} / {p.parent.name} — {self.page_idx+1}/{len(self.pages)}")