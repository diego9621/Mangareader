from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QLabel, QHBoxLayout, QVBoxLayout, QSplitter, QScrollArea,
    QFileDialog, QLineEdit, QPushButton, QStackedWidget, QDockWidget, QRadioButton, QButtonGroup,
    QSlider, QGroupBox, QListWidgetItem, QToolButton, QApplication, QFrame, QProgressBar
)
from PySide6.QtGui import QPalette, QColor, QFont, QIcon, QPixmap
from PySide6.QtCore import QSize, QRunnable, QThreadPool, QObject, Signal, Qt

from PIL import Image
from PIL.ImageQt import ImageQt

from app.core.config import MANGA_DIR
from app.core.reader import list_chapters, list_pages
from app.services.cover_service import cover_path_for_manga_dir, build_cover
from app.services.settings_service import set_library_root, get_library_root
from app.services.library_service import sync_library, get_library, mark_opened
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


class MangaCard(QWidget):
    clicked = Signal()
    openRequested = Signal()
    continueRequested = Signal()

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)

        self.cover = QLabel()
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setFixedSize(160, 220)
        self.cover.setStyleSheet("border-radius:14px; background: rgba(255,255,255,0.06);")

        self.title_lbl = QLabel(title)
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.title_lbl.setStyleSheet("font-weight:700;")
        self.title_lbl.setMaximumHeight(44)

        self.overlay = QFrame(self.cover)
        self.overlay.setVisible(False)
        self.overlay.setStyleSheet("border-radius:14px; background: rgba(0,0,0,0.55);")
        self.overlay.setGeometry(0, 0, 160, 220)

        o = QVBoxLayout(self.overlay)
        o.setContentsMargins(10, 10, 10, 10)
        o.addStretch(1)

        self.btn_continue = QPushButton("Continue")
        self.btn_open = QPushButton("Open")
        self.btn_continue.setObjectName("CardPrimary")
        self.btn_open.setObjectName("CardSecondary")

        self.btn_continue.clicked.connect(self.continueRequested.emit)
        self.btn_open.clicked.connect(self.openRequested.emit)

        o.addWidget(self.btn_continue)
        o.addWidget(self.btn_open)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self.title_lbl)

        self.setFixedWidth(180)

    def set_cover_pixmap(self, pix: QPixmap):
        if pix and not pix.isNull():
            self.cover.setPixmap(pix.scaled(self.cover.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))

    def enterEvent(self, event):
        self.overlay.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.overlay.setVisible(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.btn_library)
        self.mode_group.addButton(self.btn_favorites)
        self.mode_group.addButton(self.btn_continue)

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
        self.manga_list.setMovement(QListWidget.Static)
        self.manga_list.setResizeMode(QListWidget.Adjust)
        self.manga_list.setSpacing(12)
        self.manga_list.setUniformItemSizes(True)
        self.manga_list.setWordWrap(True)
        self.manga_list.currentItemChanged.connect(self.on_manga_highlighted)

        self.chapter_list = QListWidget()
        self.chapter_list.currentTextChanged.connect(self.on_chapter_selected)

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
        self.detail_cover.setStyleSheet("background: rgba(255,255,255,0.06); border-radius:14px;")

        self.detail_title = QLabel("Select a manga")
        self.detail_title.setWordWrap(True)
        self.detail_title.setStyleSheet("font-weight:900; font-size:14px;")

        self.detail_sub = QLabel("")
        self.detail_sub.setWordWrap(True)
        self.detail_sub.setStyleSheet("color:#bdbdbd; font-weight:700;")

        self.btn_continue_read = QPushButton("Continue")
        self.btn_open = QPushButton("Open")
        self.btn_continue_read.setObjectName("PrimaryCTA")
        self.btn_open.setObjectName("SecondaryCTA")
        self.btn_continue_read.clicked.connect(self.continue_selected_manga)
        self.btn_open.clicked.connect(self.open_selected_manga)

        btn_row = QWidget()
        btn_row_l = QHBoxLayout(btn_row)
        btn_row_l.setContentsMargins(0, 0, 0, 0)
        btn_row_l.setSpacing(10)
        btn_row_l.addWidget(self.btn_continue_read, 1)
        btn_row_l.addWidget(self.btn_open, 1)

        self.chapters_preview = QListWidget()
        self.chapters_preview.setObjectName("ChaptersPreview")
        self.chapters_preview.setSpacing(4)
        self.chapters_preview.setUniformItemSizes(True)
        self.chapters_preview.itemActivated.connect(self.on_detail_chapter_open)

        detail_page = QWidget()
        detail_layout = QVBoxLayout(detail_page)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(12)
        detail_layout.addWidget(QLabel("Details"))
        detail_layout.addWidget(self.detail_cover, alignment=Qt.AlignmentFlag.AlignTop)
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_sub)
        detail_layout.addWidget(btn_row)
        detail_layout.addWidget(QLabel("Chapters"))
        detail_layout.addWidget(self.chapters_preview)
        detail_layout.addStretch(1)

        chapters_page = QWidget()
        chapters_layout = QVBoxLayout(chapters_page)
        chapters_layout.setContentsMargins(10, 10, 10, 10)
        chapters_layout.setSpacing(10)
        t2 = QLabel("Chapters")
        t2.setStyleSheet("font-weight:900;")
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

        self.fit_group = QButtonGroup(self)
        self.fit_group.addButton(self.fit_width_btn)
        self.fit_group.addButton(self.fit_heigth_btn)

        dir_box = QGroupBox("Direction")
        dir_layout = QVBoxLayout(dir_box)
        self.dir_ltr_btn = QRadioButton("Left -> Right")
        self.dir_rtl_btn = QRadioButton("Right -> Left")
        self.dir_ltr_btn.setChecked(True)
        dir_layout.addWidget(self.dir_ltr_btn)
        dir_layout.addWidget(self.dir_rtl_btn)

        self.dir_group = QButtonGroup(self)
        self.dir_group.addButton(self.dir_ltr_btn)
        self.dir_group.addButton(self.dir_rtl_btn)

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
        self.card_by_title: dict[str, MangaCard] = {}
        self.detail_continue_chapter: str | None = None

        self.reload_library()

        self.fit_width_btn.toggled.connect(self.on_fit_changed)
        self.fit_heigth_btn.toggled.connect(self.on_fit_changed)
        self.dir_ltr_btn.toggled.connect(self.on_direction_changed)
        self.dir_rtl_btn.toggled.connect(self.on_direction_changed)
        self.page_slider.valueChanged.connect(self.on_page_slider_changed)

        self.btn_library.toggled.connect(lambda checked: checked and self.set_library_mode("library"))
        self.btn_favorites.toggled.connect(lambda checked: checked and self.set_library_mode("favorites"))
        self.btn_continue.toggled.connect(lambda checked: checked and self.set_library_mode("continue"))

        self.set_ui_mode("library")

    def apply_theme(self):
        app = QApplication.instance()
        if app:
            app.setStyle("Fusion")
            app.setFont(QFont("SF Pro", 12))

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
            QListWidget { background: #141414; border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 8px; outline: 0; }
            QListWidget::item { border-radius: 12px; padding: 6px; }
            QListWidget::item:selected { background: rgba(59,130,246,0.18); border: 1px solid rgba(59,130,246,0.35); }
            QLineEdit { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 9px 12px; }
            QLineEdit:focus { border: 1px solid rgba(59,130,246,0.7); }
            QPushButton { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); border-radius: 12px; padding: 10px 12px; font-weight: 800; }
            QPushButton:hover { background: rgba(255,255,255,0.10); }
            QPushButton:pressed { background: rgba(255,255,255,0.05); }
            QToolButton { background: transparent; border: 1px solid transparent; border-radius: 12px; padding: 8px 12px; font-weight: 800; }
            QToolButton:hover { background: rgba(255,255,255,0.06); }
            QToolButton:checked { background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.10); }

            #PrimaryCTA { background: rgba(59,130,246,0.95); border: 1px solid rgba(59,130,246,0.95); color: white; }
            #PrimaryCTA:hover { background: rgba(59,130,246,0.85); }
            #SecondaryCTA { background: rgba(255,255,255,0.06); }

            #CardPrimary { background: rgba(59,130,246,0.95); border: 1px solid rgba(59,130,246,0.95); color: white; border-radius: 12px; padding: 9px 10px; font-weight: 900; }
            #CardPrimary:hover { background: rgba(59,130,246,0.85); }
            #CardSecondary { background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 9px 10px; font-weight: 900; }

            QGroupBox { border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; margin-top: 10px; padding: 10px; }
            QGroupBox:title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #bdbdbd; font-weight: 800; }

            QSlider::groove:horizontal { height: 6px; background: rgba(255,255,255,0.10); border-radius: 3px; }
            QSlider::handle:horizontal { width: 16px; margin: -6px 0; border-radius: 8px; background: #3b82f6; }

            QProgressBar { border: 0; background: rgba(255,255,255,0.08); border-radius: 4px; height: 6px; }
            QProgressBar::chunk { background: rgba(59,130,246,0.85); border-radius: 4px; }

            #ChaptersPreview {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 14px;
                padding: 6px;
            }
            #ProgBadge {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 999px;
            }
            #ProgBadgeText {
                color: #d6d6d6;
                font-weight: 900;
            }
        """)

    def import_library_folder(self):
        start = get_library_root() or str(MANGA_DIR)
        path = QFileDialog.getExistingDirectory(self, "Select library folder", start)
        if not path:
            return
        set_library_root(path)
        self.reload_library()

    def on_cover_done(self, title: str, cover_path: str):
        card = self.card_by_title.get(title)
        if not card:
            return
        pix = QPixmap(cover_path)
        if not pix.isNull():
            card.set_cover_pixmap(pix)

        if self.detail_title.text() == title:
            self.detail_cover.setPixmap(pix.scaled(self.detail_cover.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

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
        self.card_by_title.clear()

        for m in rows:
            title = m.title
            manga_dir = Path(m.path)

            it = QListWidgetItem()
            it.setData(Qt.ItemDataRole.UserRole, title)
            it.setSizeHint(QSize(180, 280))
            self.manga_list.addItem(it)

            card = MangaCard(title)
            self.card_by_title[title] = card

            def select_this(item=it):
                self.manga_list.setCurrentItem(item)

            def open_this(t=title):
                self.open_manga(t)

            def continue_this(t=title):
                self.continue_manga(t)

            card.clicked.connect(select_this)
            card.openRequested.connect(open_this)
            card.continueRequested.connect(continue_this)

            cover = cover_path_for_manga_dir(manga_dir)
            if cover.exists():
                pix = QPixmap(str(cover))
                if not pix.isNull():
                    card.set_cover_pixmap(pix)
            else:
                ch = list_chapters(manga_dir)
                if ch:
                    self.threadpool.start(CoverWorker(title, manga_dir, ch[0], self.cover_signals))

            self.manga_list.setItemWidget(it, card)

        self.manga_list.blockSignals(False)

        if self.manga_list.count():
            self.manga_list.setCurrentRow(0)
        else:
            self.detail_title.setText("No results")
            self.detail_cover.clear()
            self.detail_sub.setText("")
            self.chapters_preview.clear()

    def on_manga_highlighted(self, current, previous):
        if not current:
            return
        title = current.data(Qt.ItemDataRole.UserRole) or ""
        self.update_detail_pane(title)

    def update_detail_pane(self, title: str):
        mdir = self.manga_by_title.get(title)
        self.detail_title.setText(title)
        self.detail_cover.clear()
        self.detail_sub.setText("")
        self.chapters_preview.clear()
        self.detail_continue_chapter = None

        if not mdir:
            return

        cover = cover_path_for_manga_dir(mdir)
        if cover.exists():
            pix = QPixmap(str(cover))
            if not pix.isNull():
                self.detail_cover.setPixmap(pix.scaled(self.detail_cover.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.refresh_detail_chapters(title)

    def compute_continue_target(self, title: str):
        mdir = self.manga_by_title.get(title)
        if not mdir:
            return None

        chapters = list_chapters(mdir)
        if not chapters:
            return None

        best_ch = chapters[0]
        best_idx = 0
        best_total = max(len(list_pages(mdir / best_ch)), 1)

        for ch in chapters:
            pages = list_pages(mdir / ch)
            total = max(len(pages), 1)
            idx = load_progress(str(mdir / ch))
            idx = 0 if idx is None else max(0, min(idx, total - 1))
            if idx > best_idx:
                best_ch, best_idx, best_total = ch, idx, total

        return best_ch, best_idx, best_total

    def continue_selected_manga(self):
        item = self.manga_list.currentItem()
        if not item:
            return
        title = item.data(Qt.ItemDataRole.UserRole) or ""
        if title:
            self.continue_manga(title)

    def continue_manga(self, title: str):
        target = self.compute_continue_target(title)
        if not target:
            self.open_manga(title)
            return
        ch, _, _ = target
        self.open_manga(title, chapter=ch)

    def open_selected_manga(self):
        item = self.manga_list.currentItem()
        if not item:
            return
        title = item.data(Qt.ItemDataRole.UserRole) or ""
        if title:
            self.open_manga(title)

    def open_manga(self, title: str, chapter: str | None = None):
        self.current_manga_dir = self.manga_by_title.get(title)
        if not self.current_manga_dir:
            return

        self.set_ui_mode("reading")
        self.fit_width_btn.setChecked(True)
        self.fit_mode = "width"

        mark_opened(title)
        self.reload_library()

        self.chapter_list.clear()
        chapters = list_chapters(self.current_manga_dir)
        self.chapter_list.addItems(chapters)

        if not self.chapter_list.count():
            self.pages = []
            self.page_idx = 0
            self.image_label.setText("No chapters found")
            return

        if chapter and chapter in chapters:
            for i in range(self.chapter_list.count()):
                if self.chapter_list.item(i).text() == chapter:
                    self.chapter_list.setCurrentRow(i)
                    break
        else:
            self.chapter_list.setCurrentRow(0)

    def make_chapter_row_widget(self, chapter: str, cur: int, total: int):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 8, 10, 8)
        l.setSpacing(6)

        top = QWidget()
        tl = QHBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(10)

        name = QLabel(chapter)
        name.setStyleSheet("font-weight:900;")

        badge = QFrame()
        badge.setObjectName("ProgBadge")
        bl = QHBoxLayout(badge)
        bl.setContentsMargins(10, 4, 10, 4)
        bl.setSpacing(0)

        t = QLabel(f"p{cur}/{total}")
        t.setObjectName("ProgBadgeText")
        bl.addWidget(t)

        tl.addWidget(name)
        tl.addStretch(1)
        tl.addWidget(badge)

        pb = QProgressBar()
        pb.setRange(0, total)
        pb.setValue(cur)
        pb.setTextVisible(False)
        pb.setFixedHeight(6)

        l.addWidget(top)
        l.addWidget(pb)

        return w

    def on_detail_chapter_open(self, item: QListWidgetItem):
        chapter = item.data(Qt.ItemDataRole.UserRole)
        if not chapter:
            return
        title = self.detail_title.text()
        self.open_manga(title, chapter=chapter)

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

        cont = self.compute_continue_target(title)
        if cont:
            ch, idx, total = cont
            self.detail_continue_chapter = ch
            self.detail_sub.setText(f"Continue: {ch}  •  p{idx+1}/{total}")
        else:
            self.detail_sub.setText("")

        for ch in chapters:
            pages = list_pages(mdir / ch)
            total = max(len(pages), 1)
            idx = load_progress(str(mdir / ch))
            idx = 0 if idx is None else max(0, min(idx, total - 1))
            cur = idx + 1

            it = QListWidgetItem()
            it.setData(Qt.ItemDataRole.UserRole, ch)
            it.setSizeHint(QSize(0, 56))

            w = self.make_chapter_row_widget(ch, cur, total)
            self.chapters_preview.addItem(it)
            self.chapters_preview.setItemWidget(it, w)

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
        idx = 0 if idx is None else idx
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