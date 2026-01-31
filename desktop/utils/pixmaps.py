from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

def pixmap_cover_crop(path: str, size: QSize) -> QPixmap:
    pix = QPixmap(path)
    if pix.isNull():
        return QPixmap()
    pix.setDevicePixelRatio(1.0)
    pix = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
    x = max(0, (pix.width() - size.width()) // 2)
    y = max(0, (pix.height() - size.height()) // 2)
    pix = pix.copy(x, y, size.width(), size.height())
    pix.setDevicePixelRatio(1.0)
    return pix
