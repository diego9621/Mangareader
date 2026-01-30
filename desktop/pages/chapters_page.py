from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QListWidget

class ChaptersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.chapter_list = QListWidget()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)
        t = QLabel("Chapters")
        t.setStyleSheet("font-weight:900;")
        root.addWidget(t)
        root.addWidget(self.chapter_list)