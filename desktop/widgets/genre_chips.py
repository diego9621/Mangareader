from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel
from .flow_layout import FlowLayout

class GenreChips(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.flow = FlowLayout(self, spacing=8)
        self.setLayout(self.flow)
    
    def set_genres(self, genres: list[str]):
        set.clear()
        for g in genres[:10]:
            chip = QLabel(g)
            chip.setObjectName("Chip")
            chip.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setVisible(bool(genres))
    
    def clear(self):
        while self.flow.count():
            item = self.flow.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()