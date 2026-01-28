import sys
from PySide6.QtWidgets import QApplication
from desktop.ui import MainWindow
from app.db.init_db import init_db

def main():
    init_db()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()