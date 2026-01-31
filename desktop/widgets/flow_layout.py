from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtWidgets import QLayout


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=8):
        super().__init__(parent)
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        l, t, r, b = self.getContentsMargins()
        s += QSize(l + r, t + b)
        return s

    def _do_layout(self, rect, test_only):
        sp = self.spacing()
        l, t, r, b = self.getContentsMargins()
        effective = rect.adjusted(l, t, -r, -b)

        x = effective.x()
        y = effective.y()
        right = effective.right()
        line_h = 0

        for it in self._items:
            hint = it.sizeHint()
            next_x = x + hint.width() + sp
            if next_x - sp > right and line_h > 0:
                x = effective.x()
                y += line_h + sp
                next_x = x + hint.width() + sp
                line_h = 0
            if not test_only:
                it.setGeometry(QRect(QPoint(x, y), hint))
            x = next_x
            line_h = max(line_h, hint.height())

        return (y + line_h - rect.y()) + t + b
