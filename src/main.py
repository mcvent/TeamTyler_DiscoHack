"""Точка входа в приложение."""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from gui.main_window import MainWindow


def main() -> None:
    """Запуск приложения."""

    app = QApplication(sys.argv)
    app.setApplicationName("Cloud Manager")
    app.setOrganizationName("Hackathon Team")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()