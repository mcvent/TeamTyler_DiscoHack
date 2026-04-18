"""Адресная строка с хлебными крошками и поиском."""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon


class AddressBar(QWidget):
    """Виджет адресной строки."""

    path_changed = pyqtSignal(str)
    refresh_clicked = pyqtSignal()
    search_requested = pyqtSignal(str)
    go_up_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Инициализация адресной строки."""
        super().__init__(parent)
        self._current_path = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self.up_btn = QPushButton()
        self.up_btn.setIcon(QIcon.fromTheme("go-up"))
        self.up_btn.setToolTip("На уровень выше")
        self.up_btn.setFixedSize(32, 32)
        self.up_btn.clicked.connect(self.go_up_clicked.emit)
        layout.addWidget(self.up_btn)

        # Адресная строка
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Введите путь...")
        self.path_edit.returnPressed.connect(self._on_path_entered)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.path_edit, stretch=2)

        # Кнопка поиска
        self.search_btn = QPushButton()
        self.search_btn.setIcon(QIcon.fromTheme("system-search"))
        self.search_btn.setToolTip("Поиск")
        self.search_btn.setFixedSize(32, 32)
        self.search_btn.clicked.connect(self._on_search_clicked)
        layout.addWidget(self.search_btn)

    def set_path(self, path: str) -> None:
        """Установка текущего пути."""
        self._current_path = path
        self.path_edit.setText(path)

    def _on_path_entered(self) -> None:
        """Обработка ввода пути."""
        new_path = self.path_edit.text()
        if new_path != self._current_path:
            self.path_changed.emit(new_path)

    def _on_search_clicked(self) -> None:
        """Обработка клика по кнопке поиска."""
        search_text, ok = QInputDialog.getText(
            self,
            "Поиск файлов",
            "Введите имя файла или папки:"
        )
        if ok and search_text:
            self.search_requested.emit(search_text)

    def set_navigation_state(self, can_go_back: bool, can_go_forward: bool) -> None:
        """Обновление состояния кнопок навигации."""
        self.back_btn.setEnabled(can_go_back)
        self.forward_btn.setEnabled(can_go_forward)