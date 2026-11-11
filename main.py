import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from resources.theme import FONT_FAMILY
from views.obd_main_window import ObdMainWindow


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont(FONT_FAMILY, 10))
    window = ObdMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()