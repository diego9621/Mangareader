from PySide6.QtWidgets import QLayout

def clear_layout_widgets(layout: QLayout):
    while layout.count():
        it = layout.takeAt(0)
        w = it.widget()
        if w:
            w.setParent(None)
            w.deleteLater()