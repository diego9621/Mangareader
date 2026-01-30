from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QFrame

class MangaCard(QWidget):
    clicked = Signal()
    openRequested = Signal()
    continueRequested = Signal()

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)
        self.setFixedWidth(180)

        self.cover = QLabel()
        self.cover.setFixedSize(160, 220)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setStyleSheet("border-radius:14px; background: rgba(255,255,255,0.06);")

        self.title_lbl = QLabel(title)
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.title_lbl.setMaximumHeight(44)
        self.title_lbl.setStyleSheet("font-weight:700;")

        self.overlay = QFrame(self.cover)
        self.overlay.setVisible(False)
        self.overlay.setGeometry(0, 0, 160, 220)
        self.overlay.setStyleSheet("border-radius:14px; background: rgba(0,0,0,0.55);")

        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(10, 10, 10, 10)
        overlay_layout.addStretch(1)

        self.btn_continue = QPushButton("Continue")
        self.btn_open = QPushButton("Open")
        self.btn_continue.setObjectName("CardPrimary")
        self.btn_open.setObjectName("CardSecondary")

        self.btn_continue.clicked.connect(self.continueRequested.emit)
        self.btn_open.clicked.connect(self.openRequested.emit)

        overlay_layout.addWidget(self.btn_continue)
        overlay_layout.addWidget(self.btn_open)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)
        root.addWidget(self.cover, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(self.title_lbl)

    def set_cover_pixmap(self, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            self.cover.setPixmap(
                pixmap.scaled(
                    self.cover.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

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