from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QRadioButton, QButtonGroup, QSlider

class ReaderDock(QWidget):
    fitChanged = Signal(str)
    directionChanged = Signal(str)
    pageChanged = Signal(int)

    def __init__(self):
        super().__init__()

        fit_box = QGroupBox("Fit")
        fit_l = QVBoxLayout(fit_box)
        self.fit_width_btn = QRadioButton("Width")
        self.fit_height_btn = QRadioButton("Heigth")
        self.fit_width_btn.setChecked(True)
        fit_l.addWidget(self.fit_width_btn)
        fit_l.addWidget(self.fit_height_btn)

        self.fit_group = QButtonGroup(self)
        self.fit_group.addButton(self.fit_width_btn)
        self.fit_group.addButton(self.fit_height_btn)

        dir_box = QGroupBox("Direction")
        dir_l = QVBoxLayout(dir_box)
        self.dir_ltr_btn = QRadioButton("Left -> Right")
        self.dir_rtl_btn = QRadioButton("Right -> Left")
        self.dir_ltr_btn.setChecked(True)
        dir_l.addWidget(self.dir_ltr_btn)
        dir_l.addWidget(self.dir_rtl_btn)

        self.dir_group = QButtonGroup(self)
        self.dir_group.addButton(self.dir_ltr_btn)
        self.dir_group.addButton(self.dir_rtl_btn)

        self.page_slider = QSlider(Qt.Orientation.Horizontal)
        self.page_slider.setMinimum(1)
        self.page_slider.setMaximum(1)
        self.page_slider.setValue(1)

        self.reader_info = QLabel("No chapter loaded")
        self.reader_info.setWordWrap(True)

        root = QVBoxLayout(self)
        root.addWidget(fit_box)
        root.addWidget(dir_box)
        root.addWidget(QLabel("Page"))
        root.addWidget(self.page_slider)
        root.addWidget(self.reader_info)
        root.addStretch(1)

        self.fit_width_btn.toggled.connect(self._emit_fit)
        self.fit_height_btn.toggled.connect(self._emit_fit)
        self.dir_ltr_btn.toggled.connect(self._emit_dir)
        self.dir_rtl_btn.toggled.connect(self._emit_dir)
        self.page_slider.valueChanged.connect(self.pageChanged.emit)

    def _emit_fit(self):
        self.fitChanged.emit("width" if self.fit_width_btn.isChecked() else "height")

    def _emit_dir(self):
        self.directionChanged.emit("RTL" if self.dir_rtl_btn.isChecked() else "LTR")