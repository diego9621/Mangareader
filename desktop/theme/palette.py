from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtWidgets import QApplication

def apply_palette():
    app = QApplication.instance()
    if not app:
        return
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
    pal.setColor(QPalette.Highlight, QColor("#ef5050"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)
