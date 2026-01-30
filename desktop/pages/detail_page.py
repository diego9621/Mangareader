from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QListWidget
from desktop.widgets import FlowLayout
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QProgressBar
from PySide6.QtCore import QSize

class DetailPage(QWidget):
    continueClicked = Signal()
    openClicked = Signal()
    openLinkClicked = Signal()
    chapterActivated = Signal(object)

    def __init__(self):
        super().__init__()

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

        self.detail_meta = QLabel("")
        self.detail_meta.setWordWrap(True)
        self.detail_meta.setStyleSheet("color:#d6d6d6; font-weight:700;")

        self.genre_box = QWidget()
        self.genre_flow = FlowLayout(self.genre_box, margin=0, spacing=8)
        self.genre_box.setLayout(self.genre_flow)
        self.genre_box.setVisible(False)

        self.detail_desc = QLabel("")
        self.detail_desc.setWordWrap(True)
        self.detail_desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.detail_desc.setStyleSheet("color:#cfcfcf; line-height:1.25;")

        desc_wrap = QWidget()
        desc_l = QVBoxLayout(desc_wrap)
        desc_l.setContentsMargins(0, 0, 0, 0)
        desc_l.addWidget(self.detail_desc)

        self.detail_desc_scroll = QScrollArea()
        self.detail_desc_scroll.setWidgetResizable(True)
        self.detail_desc_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.detail_desc_scroll.setWidget(desc_wrap)
        self.detail_desc_scroll.setMinimumHeight(140)

        self.btn_continue = QPushButton("Continue")
        self.btn_open = QPushButton("Open")
        self.btn_open_link = QPushButton("Open Link")
        self.btn_continue.setObjectName("PrimaryCTA")
        self.btn_open.setObjectName("SecondaryCTA")
        self.btn_open_link.setObjectName("SecondaryCTA")

        self.btn_continue.clicked.connect(self.continueClicked.emit)
        self.btn_open.clicked.connect(self.openClicked.emit)
        self.btn_open_link.clicked.connect(self.openLinkClicked.emit)

        btn_row = QWidget()
        btn_row_l = QHBoxLayout(btn_row)
        btn_row_l.setContentsMargins(0, 0, 0, 0)
        btn_row_l.setSpacing(10)
        btn_row_l.addWidget(self.btn_continue, 1)
        btn_row_l.addWidget(self.btn_open, 1)
        btn_row_l.addWidget(self.btn_open_link, 1)

        self.chapters_preview = QListWidget()
        self.chapters_preview.setObjectName("ChaptersPreview")
        self.chapters_preview.setSpacing(4)
        self.chapters_preview.setUniformItemSizes(True)
        self.chapters_preview.itemActivated.connect(self.chapterActivated.emit)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        root.addWidget(QLabel("Details"))
        root.addWidget(self.detail_cover, alignment=Qt.AlignmentFlag.AlignTop)
        root.addWidget(self.detail_title)
        root.addWidget(self.detail_sub)
        root.addWidget(self.detail_meta)
        root.addWidget(self.genre_box)
        root.addWidget(self.detail_desc_scroll, 1)
        root.addWidget(btn_row)
        root.addWidget(QLabel("Chapters"))
        root.addWidget(self.chapters_preview)
        root.addStretch(1)

    def clear(self):
        self.detail_cover.clear()
        self.detail_sub.setText("")
        self.detail_meta.setText("")
        self.detail_desc.setText("")
        self.set_genres([])

    def set_genres(self, genres):
        while self.genre_flow.count():
            it = self.genre_flow.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        for g in (genres or [])[:10]:
            lab = QLabel(g)
            lab.setObjectName("Chip")
            lab.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            self.genre_flow.addWidget(lab)
        self.genre_box.setVisible(bool(genres))


    def make_chapter_row_widget(self, chapter: str, cur: int, total: int) -> QWidget:
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