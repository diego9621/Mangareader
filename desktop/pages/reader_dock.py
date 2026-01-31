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
        self.fit_height_btn = QRadioButton("Height")
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

    def set_page_range(self, total_pages: int):
        total = max(1, int(total_pages or 1))
        self.page_slider.blockSignals(True)
        self.page_slider.setMinimum(1)
        self.page_slider.setMaximum(total)
        self.page_slider.setValue(1)
        self.page_slider.blockSignals(False)

    def set_page(self, page_idx: int):
        v = int(page_idx) + 1
        self.page_slider.blockSignals(True)
        self.page_slider.setValue(max(self.page_slider.minimum(), min(self.page_slider.maximum(), v)))
        self.page_slider.blockSignals(False)

    def set_info(self, text: str):
        self.reader_info.setText(text or "")

    def set_fit(self, fit: str):
        if fit == "height":
            self.fit_height_btn.setChecked(True)
        else:
            self.fit_width_btn.setChecked(True)

    def set_direction(self, direction: str):
        if direction == "RTL":
            self.dir_rtl_btn.setChecked(True)
        else:
            self.dir_ltr_btn.setChecked(True)
