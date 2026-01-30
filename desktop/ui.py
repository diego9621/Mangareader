from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt, QSize, QUrl, QTimer, QThreadPool
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QListWidgetItem, QLabel, QHBoxLayout, QVBoxLayout,
    QSplitter, QScrollArea, QFileDialog, QLineEdit, QStackedWidget, QDockWidget,
    QRadioButton, QButtonGroup, QSlider, QGroupBox, QToolButton
)
from app.core.config import MANGA_DIR
from app.core.reader import list_chapters
from app.services.settings_service import set_library_root, get_library_root
from app.services.library_service import mark_opened
from app.services.cover_service import cover_path_for_manga_dir
from desktop.theme.palette import apply_palette
from desktop.theme.stylesheet import apply_stylesheet
from desktop.pages.detail_page import DetailPage
from desktop.pages.chapters_page import ChaptersPage
from desktop.workers.cover_dl_worker import CoverDlSignals
from desktop.workers.discover_worker import DiscoverSignals
from desktop.workers import CoverSignals
from desktop.controllers.detail_controller import DetailController
from desktop.controllers.library_controller import LibraryController
from desktop.controllers.discover_controller import DiscoverController
from desktop.controllers.reader_controller import ReaderController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        apply_palette()
        apply_stylesheet(self)
        self.setWindowTitle("Mangareader")
        self.resize(1200, 800)

        self.threadpool = QThreadPool.globalInstance()

        self.cover_signals = CoverSignals()
        self.discover_signals = DiscoverSignals()
        self.coverdl_signals = CoverDlSignals()

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self.on_search_debounced)

        self._build_ui()
        self._controllers()
        self._wire()

        self.library_controller.reload()
        self.set_ui_mode("library")

    def _build_ui(self):
        self.btn_library = QToolButton(text="Library", checkable=True, checked=True)
        self.btn_favorites = QToolButton(text="Favorites", checkable=True)
        self.btn_continue = QToolButton(text="Continue", checkable=True)
        self.btn_discover = QToolButton(text="Discover", checkable=True)

        mode_bar = QWidget()
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(0, 0, 0, 0)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        for b in (self.btn_discover, self.btn_library, self.btn_favorites, self.btn_continue):
            self.mode_group.addButton(b)
            mode_layout.addWidget(b)
        mode_layout.addStretch(1)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search titles...")
        self.search.setFixedWidth(280)

        header = QWidget()
        header.setFixedHeight(52)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(10)

        app_title = QLabel("Mangareader")
        app_title.setStyleSheet("font-weight:900; font-size:16px;")

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

        self.discover_list = QListWidget()
        self.discover_list.setViewMode(QListWidget.IconMode)
        self.discover_list.setIconSize(QSize(160, 220))
        self.discover_list.setGridSize(QSize(190, 270))
        self.discover_list.setResizeMode(QListWidget.Adjust)
        self.discover_list.setMovement(QListWidget.Static)
        self.discover_list.setSpacing(10)
        self.discover_list.setWordWrap(True)
        self.discover_list.setUniformItemSizes(True)

        self.left_stack = QStackedWidget()
        self.left_stack.addWidget(self.manga_list)
        self.left_stack.addWidget(self.discover_list)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        left_layout.addWidget(header)
        left_layout.addWidget(self.left_stack)

        self.detail_page = DetailPage()
        self.chapters_page = ChaptersPage()

        self.mid_stack = QStackedWidget()
        self.mid_stack.addWidget(self.detail_page)
        self.mid_stack.addWidget(self.chapters_page)

        self.image_label = QLabel("Import a library folder to begin")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("padding: 20px; background: transparent;")

        self.scroll = QScrollArea()
        self.scroll.setAlignment(Qt.AlignCenter)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.image_label)

        self.splitter = QSplitter()
        self.splitter.addWidget(left)
        self.splitter.addWidget(self.mid_stack)
        self.splitter.addWidget(self.scroll)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 4)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.splitter)
        self.setCentralWidget(root)

        menu = self.menuBar().addMenu("Library")
        action = menu.addAction("Import Library Folder…")
        action.triggered.connect(self.import_library_folder)

        self.reader_dock = QDockWidget("Reader", self)
        self.reader_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.reader_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)

        dock_body = QWidget()
        dock_layout = QVBoxLayout(dock_body)

        fit_box = QGroupBox("Fit")
        fit_layout = QVBoxLayout(fit_box)
        self.fit_width_btn = QRadioButton("Width", checked=True)
        self.fit_height_btn = QRadioButton("Height")
        fit_layout.addWidget(self.fit_width_btn)
        fit_layout.addWidget(self.fit_height_btn)

        self.fit_group = QButtonGroup(self)
        self.fit_group.addButton(self.fit_width_btn)
        self.fit_group.addButton(self.fit_height_btn)

        dir_box = QGroupBox("Direction")
        dir_layout = QVBoxLayout(dir_box)
        self.dir_ltr_btn = QRadioButton("Left -> Right", checked=True)
        self.dir_rtl_btn = QRadioButton("Right -> Left")
        dir_layout.addWidget(self.dir_ltr_btn)
        dir_layout.addWidget(self.dir_rtl_btn)

        self.dir_group = QButtonGroup(self)
        self.dir_group.addButton(self.dir_ltr_btn)
        self.dir_group.addButton(self.dir_rtl_btn)

        self.page_slider = QSlider(Qt.Horizontal)
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
        self.addDockWidget(Qt.RightDockWidgetArea, self.reader_dock)
        self.reader_dock.setVisible(False)

    def _controllers(self):
        self.detail_controller = DetailController(
            detail_page=self.detail_page,
            make_chapter_row_widget=self.detail_page.make_chapter_row_widget,
            open_manga_callback=self.open_manga,
            get_manga_by_title=lambda: self.library_controller.manga_by_title,
        )

        self.library_controller = LibraryController(
            threadpool=self.threadpool,
            manga_list=self.manga_list,
            cover_signals=self.cover_signals,
            on_cover_done=self.on_cover_done,
            clear_detail=self.detail_page.clear,
            set_selected_title=self.detail_controller.show_library_title,
        )

        self.discover_controller = DiscoverController(
            threadpool=self.threadpool,
            discover_list=self.discover_list,
            coverdl_signals=self.coverdl_signals,
            discover_signals=self.discover_signals,
            detail_page=self.detail_page,
            open_link_callback=self._open_url,
        )

        self.reader_controller = ReaderController(
            scroll=self.scroll,
            image_label=self.image_label,
            page_slider=self.page_slider,
            reader_info=self.reader_info,
            set_title=self.setWindowTitle,
        )

    def _wire(self):
        self.search.textChanged.connect(self.on_search_text_changed)

        self.btn_library.toggled.connect(lambda x: x and self.set_library_mode("library"))
        self.btn_favorites.toggled.connect(lambda x: x and self.set_library_mode("favorites"))
        self.btn_continue.toggled.connect(lambda x: x and self.set_library_mode("continue"))
        self.btn_discover.toggled.connect(lambda x: x and self.set_library_mode("discover"))

        self.manga_list.currentItemChanged.connect(self.on_manga_selected)
        self.detail_page.chapters_preview.itemActivated.connect(self.detail_controller.on_chapter_preview_activated)

        self.discover_list.currentItemChanged.connect(lambda cur, _: self.discover_controller.on_selected(cur))
        self.discover_list.itemActivated.connect(self.discover_controller.open_selected)

        self.detail_page.btn_continue.clicked.connect(self.continue_selected_manga)
        self.detail_page.btn_open.clicked.connect(self.open_selected_manga)
        self.detail_page.btn_open_link.clicked.connect(self.discover_controller.open_link)

        self.chapters_page.chapter_list.currentTextChanged.connect(self.on_chapter_selected)

        self.fit_width_btn.toggled.connect(lambda x: x and self.reader_controller.set_fit("width"))
        self.fit_height_btn.toggled.connect(lambda x: x and self.reader_controller.set_fit("height"))
        self.dir_ltr_btn.toggled.connect(lambda x: x and self.reader_controller.set_direction("LTR"))
        self.dir_rtl_btn.toggled.connect(lambda x: x and self.reader_controller.set_direction("RTL"))
        self.page_slider.valueChanged.connect(lambda v: self.reader_controller.set_page(v - 1))

    def import_library_folder(self):
        start = get_library_root() or str(MANGA_DIR)
        path = QFileDialog.getExistingDirectory(self, "Select library folder", start)
        if not path:
            return
        set_library_root(path)
        self.library_controller.reload()

    def set_ui_mode(self, mode: str):
        if mode == "library":
            self.reader_dock.setVisible(False)
            self.splitter.setSizes([780, 420, 0])
            self.mid_stack.setCurrentIndex(0)
            self.scroll.setVisible(False)
        else:
            self.reader_dock.setVisible(True)
            self.splitter.setSizes([0, 320, 1200])
            self.mid_stack.setCurrentIndex(1)
            self.scroll.setVisible(True)

    def set_library_mode(self, mode: str):
        if mode == "discover":
            self.left_stack.setCurrentIndex(1)
            q = (self.search.text() or "").strip()
            self.discover_controller.load(q)
            return
        self.left_stack.setCurrentIndex(0)
        self.library_controller.set_mode(mode)
        self.library_controller.set_query(self.search.text())

    def on_search_text_changed(self, _):
        if self.left_stack.currentIndex() == 1:
            self.search_timer.start()
        else:
            self.library_controller.set_query(self.search.text())

    def on_search_debounced(self):
        if self.left_stack.currentIndex() != 1:
            return
        self.discover_controller.load(self.search.text())

    def on_manga_selected(self, current, _):
        if not current:
            return
        title = current.data(Qt.UserRole) or ""
        if title:
            self.detail_controller.show_library_title(title)

    def open_selected_manga(self):
        if self.left_stack.currentIndex() == 1:
            self.discover_controller.open_link()
            return
        it = self.manga_list.currentItem()
        if not it:
            return
        title = it.data(Qt.UserRole) or ""
        if title:
            self.open_manga(title)

    def continue_selected_manga(self):
        if self.left_stack.currentIndex() == 1:
            self.discover_controller.open_link()
            return
        it = self.manga_list.currentItem()
        if not it:
            return
        title = it.data(Qt.UserRole) or ""
        if not title:
            return
        mdir = self.library_controller.manga_by_title.get(title)
        if not mdir:
            return
        target = self.detail_controller.compute_continue_target(mdir)
        if not target:
            self.open_manga(title)
            return
        ch, _, _ = target
        self.open_manga(title, chapter=ch)

    def open_manga(self, title: str, chapter: str | None = None):
        manga_dir = self.library_controller.manga_by_title.get(title)
        if not manga_dir:
            return

        self.set_ui_mode("reading")
        self.fit_width_btn.setChecked(True)
        self.dir_ltr_btn.setChecked(True)

        mark_opened(title)
        self.library_controller.reload()

        self.chapters_page.chapter_list.clear()
        chapters = list_chapters(manga_dir)
        self.chapters_page.chapter_list.addItems(chapters)

        if not self.chapters_page.chapter_list.count():
            self.reader_controller.pages = []
            self.reader_controller.page_idx = 0
            self.image_label.setText("No chapters found")
            return

        if chapter and chapter in chapters:
            for i in range(self.chapters_page.chapter_list.count()):
                if self.chapters_page.chapter_list.item(i).text() == chapter:
                    self.chapters_page.chapter_list.setCurrentRow(i)
                    break
        else:
            self.chapters_page.chapter_list.setCurrentRow(0)

        self.reader_controller.current_manga_dir = manga_dir

    def on_chapter_selected(self, chapter_name: str):
        manga_dir = self.reader_controller.current_manga_dir
        if not manga_dir:
            return
        chapter_dir = manga_dir / chapter_name
        self.reader_controller.load_chapter(manga_dir, chapter_dir)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reader_controller.apply_pixmap()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.set_ui_mode("library")
            return
        if event.key() == Qt.Key_S:
            self.reader_dock.setVisible(not self.reader_dock.isVisible())
            return
        if event.key() == Qt.Key_C:
            self.mid_stack.setVisible(not self.mid_stack.isVisible())
            self.splitter.setSizes([0, 320, 1200] if self.mid_stack.isVisible() else [0, 0, 1200])
            return

        if event.key() in (Qt.Key_Right, Qt.Key_Down, Qt.Key_Space):
            (self.reader_controller.prev_page if self.reader_controller.direction == "RTL" else self.reader_controller.next_page)()
            return
        if event.key() in (Qt.Key_Left, Qt.Key_Up, Qt.Key_Backspace):
            (self.reader_controller.next_page if self.reader_controller.direction == "RTL" else self.reader_controller.prev_page)()
            return
        super().keyPressEvent(event)

    def on_cover_done(self, title: str, cover_path: str):
        pix = QPixmap(cover_path)
        if pix.isNull():
            return
        for i in range(self.manga_list.count()):
            it = self.manga_list.item(i)
            if (it.data(Qt.UserRole) or "") == title:
                it.setIcon(QIcon(cover_path))
                break
        if self.detail_page.detail_title.text() == title:
            self.detail_page.detail_cover.setPixmap(
                pix.scaled(self.detail_page.detail_cover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def _open_url(self, url: str):
        QDesktopServices.openUrl(QUrl(url))