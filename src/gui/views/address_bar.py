"""Адресная строка с хлебными крошками."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon


class AddressBar(QWidget):
    """Виджет адресной строки."""

    path_changed = pyqtSignal(str)  # Запрошен переход по пути
    refresh_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Инициализация адресной строки."""
        super().__init__(parent)
        self._current_path = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Кнопки навигации
        # self.back_btn = QPushButton()
        # self.back_btn.setIcon(QIcon.fromTheme("go-previous"))
        # self.back_btn.setToolTip("Назад")
        # self.back_btn.setFixedSize(32, 32)
        # self.back_btn.setEnabled(False)
        # layout.addWidget(self.back_btn)
        #
        # self.forward_btn = QPushButton()
        # self.forward_btn.setIcon(QIcon.fromTheme("go-next"))
        # self.forward_btn.setToolTip("Вперёд")
        # self.forward_btn.setFixedSize(32, 32)
        # self.forward_btn.setEnabled(False)
        # layout.addWidget(self.forward_btn)
        #
        # self.up_btn = QPushButton()
        # self.up_btn.setIcon(QIcon.fromTheme("go-up"))
        # self.up_btn.setToolTip("На уровень выше")
        # self.up_btn.setFixedSize(32, 32)
        # layout.addWidget(self.up_btn)

        # Адресная строка
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Введите путь...")
        self.path_edit.returnPressed.connect(self._on_path_entered)
        layout.addWidget(self.path_edit)

        # Кнопка обновления
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_btn.setToolTip("Обновить")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.clicked.connect(self.refresh_clicked.emit)
        layout.addWidget(self.refresh_btn)

        # Кнопка поиска
        self.search_btn = QPushButton()
        self.search_btn.setIcon(QIcon.fromTheme("system-search"))
        self.search_btn.setToolTip("Поиск")
        self.search_btn.setFixedSize(32, 32)
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

    def set_navigation_state(self, can_go_back: bool, can_go_forward: bool) -> None:
        """Обновление состояния кнопок навигации."""
        self.back_btn.setEnabled(can_go_back)
        self.forward_btn.setEnabled(can_go_forward)
