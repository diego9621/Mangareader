from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QWidget, QListWidget, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QScrollArea, QFileDialog, QLineEdit, QPushButton, QStackedWidget
from PySide6.QtWidgets import QDockWidget, QRadioButton, QButtonGroup, QSlider, QFormLayout, QGroupBox
from PySide6.QtWidgets import QListWidgetItem, QToolButton
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QFont
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
from app.services.library_service import sync_library, get_library, mark_opened

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
        self.apply_theme()
        self.setWindowTitle("Mangareader")
        self.rows = []
        self.resize(1200, 800)

        mode_bar = QWidget()
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_library = QToolButton()
        self.btn_library.setText("Library")
        self.btn_library.setCheckable(True)
        self.btn_library.setChecked(True)

        self.btn_favorites = QToolButton()
        self.btn_favorites.setText("Favorites")
        self.btn_favorites.setCheckable(True)

        self.btn_continue = QToolButton()
        self.btn_continue.setText("Continue")
        self.btn_continue.setCheckable(True)
        self.btn_library.setChecked(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.btn_library)
        self.mode_group.addButton(self.btn_favorites)
        self.mode_group.addButton(self.btn_continue)
        self.btn_library.setChecked(True)

        mode_layout.addWidget(self.btn_library)
        mode_layout.addWidget(self.btn_favorites)
        mode_layout.addWidget(self.btn_continue)
        mode_layout.addStretch(1)


        self.search = QLineEdit()
        self.search.setPlaceholderText("Search titles...")
        self.search.textChanged.connect(self.apply_filter)
        header = QWidget()
        header.setFixedHeight(52)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(10)

        app_title = QLabel("Mangareader")
        app_title.setStyleSheet("font-weight:900; font-size:16px;")

        self.search.setFixedWidth(280)

        header_layout.addWidget(app_title)
        header_layout.addSpacing(8)
        header_layout.addWidget(mode_bar)
        header_layout.addStretch(1)
        header_layout.addWidget(self.search)
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
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.image_label.setStyleSheet("padding: 20px; background: transparent;")
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.image_label)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        left_layout.addWidget(header)
        left_layout.addWidget(self.manga_list)

        self.detail_cover = QLabel()
        self.detail_cover.setFixedSize(240, 330)
        self.detail_cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_cover.setStyleSheet("background:#f2f2f2; border-radius:10px;")

        self.detail_title = QLabel("Select a manga")
        self.detail_title.setWordWrap(True)
        self.detail_title.setStyleSheet("font-weight:800; font-size:14px;")

        self.detail_sub = QLabel("")
        self.detail_sub.setWordWrap(True)
        self.detail_sub.setStyleSheet("color:#bdbdbd;")

        self.chapters_preview = QListWidget()
        self.chapters_preview.setObjectName("ChaptersPreview")
        self.chapters_preview.setSpacing(2)
        self.chapters_preview.setUniformItemSizes(True)
        self.chapters_preview.itemActivated.connect(self.on_detail_chapter_open)

        self.btn_open = QPushButton("Open")
        self.btn_open.clicked.connect(self.open_selected_manga)

        detail_page = QWidget()
        detail_layout = QVBoxLayout(detail_page)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(12)
        detail_layout.addWidget(QLabel("Details"))
        detail_layout.addWidget(self.detail_cover, alignment=Qt.AlignmentFlag.AlignTop)
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_sub)
        detail_layout.addWidget(self.btn_open)
        detail_layout.addWidget(QLabel("Chapters"))
        detail_layout.addWidget(self.chapters_preview)
        detail_layout.addStretch(1)

        chapters_page = QWidget()
        chapters_layout = QVBoxLayout(chapters_page)
        chapters_layout.setContentsMargins(10, 10, 10, 10)
        chapters_layout.setSpacing(10)
        t2 = QLabel("Chapters")
        t2.setStyleSheet("font-weight:700;")
        chapters_layout.addWidget(t2)
        chapters_layout.addWidget(self.chapter_list)

        self.mid_stack = QStackedWidget()
        self.mid_stack.addWidget(detail_page)
        self.mid_stack.addWidget(chapters_page)

        self.splitter = QSplitter()
        self.splitter.addWidget(left)
        self.splitter.addWidget(self.mid_stack)
        self.splitter.addWidget(self.scroll)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 4)

        self.left_panel = left
        self.mid_panel = self.mid_stack
        self.reader_panel = self.scroll
        self.ui_mode = "library"
        self.library_mode = "library"
        self.favorites_mode = "favorites"
        self.continue_mode = "continue"


        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
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
        self.reader_dock.setVisible(False)
        self.current_manga_dir: Path | None = None
        self.current_chapter_dir: Path | None = None
        self.pages: list[Path] = []
        self.page_idx = 0
        self.original_pixmap = None
        self.fit_mode = "width"
        self.reading_direction = "LTR"

        self.manga_by_title: dict[str, Path] = {}
        self.all_manga: list[str] = []
        self.manga_list.currentItemChanged.connect(self.on_manga_highlighted)
        self.manga_list.itemActivated.connect(self.open_selected_manga)
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

        self.btn_library.toggled.connect(lambda checked: checked and self.set_library_mode("library"))
        self.btn_favorites.toggled.connect(lambda checked: checked and self.set_library_mode("favorites"))
        self.btn_continue.toggled.connect(lambda checked: checked and self.set_library_mode("continue"))
        self.setStyleSheet("""
        QToolButton { padding: 6px 12px; border-radius: 8px; background: transparent; }
        QToolButton:checked { background: #e6e6e6; font-weight: 800; }
        QToolButton:hover { background: #f0f0f0; }
        QListWidget { outline: 0; }
        """)

    def apply_theme(self):
        app = QApplication.instance()
        if app:
            app.setStyle("Fusion")
            app.setFont(QFont("SF Pro Display", 12))

            pal = QPalette()
            pal.setColor(QPalette.Window, QColor("#121212"))
            pal.setColor(QPalette.Base, QColor("#161616"))
            pal.setColor(QPalette.AlternateBase, QColor("#1b1b1b"))
            pal.setColor(QPalette.Text, QColor("#eaeaea"))
            pal.setColor(QPalette.WindowText, QColor("#eaeaea"))
            pal.setColor(QPalette.Button, QColor("#1c1c1c"))
            pal.setColor(QPalette.ButtonText, QColor("#eaeaea"))
            pal.setColor(QPalette.Highlight, QColor("#3b82f6"))
            pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
            app.setPalette(pal)

        self.setStyleSheet("""
            QMainWindow { background: #121212; }
            QWidget { color: #eaeaea; font-size: 12px; }
            QLabel { color: #eaeaea; }
            QSplitter::handle { background: #0f0f0f; width: 8px; }
            QScrollArea { border: 0; background: #0f0f0f; }
            QListWidget { background: #141414; border: 1px solid #222; border-radius: 14px; padding: 8px; outline: 0; }
            QListWidget::item { border-radius: 12px; padding: 10px; }
            QListWidget::item:hover { background: rgba(255,255,255,0.06); }
            QListWidget::item:selected { background: rgba(59,130,246,0.25); border: 1px solid rgba(59,130,246,0.45); }
            QLineEdit { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 9px 12px; }
            QLineEdit:focus { border: 1px solid rgba(59,130,246,0.7); }
            QPushButton { background: #1f2937; border: 1px solid #2b3441; border-radius: 12px; padding: 10px 12px; font-weight: 700; }
            QPushButton:hover { background: #263244; }
            QPushButton:pressed { background: #1b2433; }
            QToolButton { background: transparent; border: 1px solid transparent; border-radius: 12px; padding: 8px 12px; font-weight: 700; }
            QToolButton:hover { background: rgba(255,255,255,0.06); }
            QToolButton:checked { background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.10); }
            QGroupBox { border: 1px solid #2a2a2a; border-radius: 14px; margin-top: 10px; padding: 10px; }
            QGroupBox:title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #bdbdbd; }
            QDockWidget { titlebar-close-icon: none; titlebar-normal-icon: none; }
            QDockWidget::title { background: #161616; padding: 8px; border-bottom: 1px solid #222; }
            QSlider::groove:horizontal { height: 6px; background: #2a2a2a; border-radius: 3px; }
            QSlider::handle:horizontal { width: 16px; margin: -6px 0; border-radius: 8px; background: #3b82f6; }
            QRadioButton { spacing: 10px; }
            QRadioButton::indicator { width: 16px; height: 16px; }
            QRadioButton::indicator:unchecked { border: 1px solid #3a3a3a; border-radius: 8px; background: #141414; }
            QRadioButton::indicator:checked { border: 1px solid rgba(59,130,246,0.9); border-radius: 8px; background: rgba(59,130,246,0.9); }
            #ChaptersPreview {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 14px;
                padding: 6px;
            }
            #ChaptersPreview::item {
                border-radius: 12px;
                padding: 0px;
                margin: 2px 0px;
            }
            #ChaptersPreview::item:hover {
                background: rgba(255,255,255,0.05);
            }
            #ChaptersPreview::item:selected {
                background: rgba(59,130,246,0.22);
                border: 1px solid rgba(59,130,246,0.35);
            }
            #ProgBadge {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 999px;
            }
            #ProgBadgeText {
                color: #d6d6d6;
                font-weight: 700;
            }
        """)
    def make_chapter_row_widget(self, chapter: str, cur: int, total: int):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(10)

        name = QLabel(chapter)
        name.setStyleSheet("font-weight:700;")

        badge = QFrame()
        badge.setObjectName("ProgBadge")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(10, 4, 10, 4)
        bl.setSpacing(0)

        t = QLabel(f"p{cur}/{total}")
        t.setObjectName("ProgBadgeText")
        bl.addWidget(t)

        l.addWidget(name)
        l.addStretch(1)
        l.addWidget(badge)
        return w
    
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

    def set_library_mode(self, mode: str):
        self.library_mode = mode
        self.apply_filter()

    def set_ui_mode(self, mode: str):
        self.ui_mode = mode
        is_library = mode == "library"

        if is_library:
            self.reader_dock.setVisible(False)
            self.left_panel.setVisible(True)
            self.mid_panel.setVisible(True)
            self.reader_panel.setVisible(False)
            self.mid_stack.setCurrentIndex(0)
            self.splitter.setSizes([780, 420, 0])
        else:
            self.reader_dock.setVisible(True)
            self.left_panel.setVisible(False)
            self.mid_panel.setVisible(True)
            self.reader_panel.setVisible(True)
            self.mid_stack.setCurrentIndex(1)
            self.splitter.setSizes([0, 320, 1200])

    def reload_library(self):
        rows = sync_library()
        self.rows = rows if rows else get_library()
        self.apply_filter()

    def apply_filter(self):
        q = (self.search.text() or "").strip().lower()
        rows = list(self.rows)

        if self.library_mode == "favorites":
            rows = [m for m in rows if getattr(m, "is_favorite", False)]
        elif self.library_mode == "continue":
            rows = [m for m in rows if getattr(m, "last_opened", None)]
            rows.sort(key=lambda m: m.last_opened, reverse=True)
        else:
            rows.sort(key=lambda m: m.title.lower())
        if q:
            rows = [m for m in rows if q in m.title.lower()]
        
        self.manga_by_title = {m.title: Path(m.path) for m in rows}
        self.manga_list.blockSignals(True)
        self.manga_list.clear()
             
        for m in rows:
            title = m.title
            manga_dir = Path(m.path)
            label = f"* {title}" if getattr(m, "is_favorite", False) else title
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, title)

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
        if self.manga_list.count():
            self.manga_list.setCurrentRow(0)
        else:
            self.detail_title.setText("No results")
            self.detail_cover.clear()
            self.detail_meta.setText("")

    def apply_pixmap(self):
        if not self.original_pixmap:
            return

        vw = max(1, self.scroll.viewport().width())
        vh = max(1, self.scroll.viewport().height())

        ow = self.original_pixmap.width()
        oh = self.original_pixmap.height()

        scale_w = vw / ow
        scale_h = vh / oh

        if self.fit_mode == "height":
            if scale_h * ow < vw * 0.65:
                target = self.original_pixmap.scaledToWidth(vw, Qt.TransformationMode.SmoothTransformation)
            else:
                target = self.original_pixmap.scaledToHeight(vh, Qt.TransformationMode.SmoothTransformation)
        else:
            target = self.original_pixmap.scaledToWidth(vw, Qt.TransformationMode.SmoothTransformation)

        self.image_label.setPixmap(target)
        self.image_label.adjustSize()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_pixmap()

    def on_manga_highlighted(self, current, previous):
        if not current:
            return
        title = current.data(Qt.ItemDataRole.UserRole) or current.text()
        if title.startswith("* "):
            title = title[2:]
        self.update_detail_pane(title)

    def update_detail_pane(self, title: str):
        mdir = self.manga_by_title.get(title)
        self.detail_title.setText(title)

        self.detail_cover.clear()
        self.detail_sub.setText("")
        self.chapters_preview.clear()

        if not mdir:
            return

        cover = cover_path_for_manga_dir(mdir)
        if cover.exists():
            pix = QPixmap(str(cover))
            if not pix.isNull():
                self.detail_cover.setPixmap(
                    pix.scaled(
                        self.detail_cover.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        self.refresh_detail_chapters(title)

    def open_selected_manga(self):
        item = self.manga_list.currentItem()
        if not item:
            return
        title = item.data(Qt.ItemDataRole.UserRole) or item.text()
        if title.startswith("* "):
            title = title[2:]
        self.open_manga(title)

    def open_manga(self, title: str):
        self.current_manga_dir = self.manga_by_title.get(title)
        if not self.current_manga_dir:
            return
        self.set_ui_mode("reading")
        self.mid_stack.setCurrentIndex(1)
        self.fit_width_btn.setChecked(True)
        self.fit_mode = "width"
        mark_opened(title)
        self.reload_library()
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
        if event.key() == Qt.Key.Key_C:
            self.mid_panel.setVisible(not self.mid_panel.isVisible())
            if self.mid_panel.isVisible():
                self.splitter.setSizes([0, 320, 1200])
            else:
                self.splitter.setSizes([0, 0, 1200])
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

    def on_detail_chapter_open(self, item: QListWidgetItem):
        chapter = item.data(Qt.ItemDataRole.UserRole)
        if not chapter:
            return
        title = self.detail_title.text()
        self.open_manga(title)
        for i in range(self.chapter_list.count()):
            if self.chapter_list.item(i).text() == chapter:
                self.chapter_list.setCurrentRow(i)
                break

    def refresh_detail_chapters(self, title: str):
        mdir = self.manga_by_title.get(title)
        self.chapters_preview.clear()
        if not mdir:
            self.detail_sub.setText("")
            return

        chapters = list_chapters(mdir)
        if not chapters:
            self.detail_sub.setText("No chapters found")
            return

        best = None

        for ch in chapters:
            pages = list_pages(mdir / ch)
            total = max(len(pages), 1)
            idx = load_progress(str(mdir / ch))
            idx = 0 if idx is None else max(0, min(idx, total - 1))
            cur = idx + 1

            it = QListWidgetItem()
            it.setData(Qt.ItemDataRole.UserRole, ch)
            it.setSizeHint(QSize(0, 44))

            w = self.make_chapter_row_widget(ch, cur, total)
            self.chapters_preview.addItem(it)
            self.chapters_preview.setItemWidget(it, w)

            if best is None:
                best = (cur / total, ch, cur, total)
            else:
                if (cur / total) < best[0]:
                    best = (cur / total, ch, cur, total)

        if best:
            _, ch, cur, total = best
            self.detail_sub.setText(f"Continue: {ch}  •  p{cur}/{total}")
        else:
            self.detail_sub.setText("")

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