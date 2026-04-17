"""Левая панель навигации с деревом облачных хранилищ."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QLabel,
    QHeaderView, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon


class SideBar(QWidget):
    """Боковая панель с деревом хранилищ и папок."""

    # Сигналы-заглушки для будущей интеграции
    folder_selected = pyqtSignal(str)  # Путь к выбранной папке
    add_storage_clicked = pyqtSignal()  # Клик по кнопке добавления хранилища

    def __init__(self, parent: QWidget | None = None) -> None:
        """Инициализация боковой панели."""
        super().__init__(parent)
        self._setup_ui()
        self._setup_stub_data()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Заголовок с кнопкой добавления
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 8)

        title = QLabel(" Смонтированные диски")
        title.setStyleSheet("font-weight: bold; font-size: 13px;color: #424242;")
        header_layout.addWidget(title)

        add_btn = QPushButton()
        add_btn.setText("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setToolTip("Добавить облачное хранилище")
        add_btn.setStyleSheet("""
                    QPushButton {
                        color: white;
                        border: none;
                        font-size: 18px;
                        font-weight: bold;
                        padding: 0px;
                        margin: 0px;
                    }
                """)
        add_btn.clicked.connect(self.add_storage_clicked.emit)
        header_layout.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(header_widget)

        # Дерево
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setIndentation(16)
        self.tree_view.setAnimated(True)
        self.tree_view.setExpandsOnDoubleClick(True)

        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)

        # Сигнал выбора
        self.tree_view.clicked.connect(self._on_item_clicked)

        layout.addWidget(self.tree_view)

    def _setup_stub_data(self) -> None:
        """Добавление заглушечных данных для демонстрации."""
        # Яндекс.Диск
        yandex_item = QStandardItem("Яндекс.Диск")
        yandex_item.setIcon(self._get_icon("cloud"))
        yandex_item.setData("yandex://", Qt.ItemDataRole.UserRole)

        docs_item = QStandardItem("Документы")
        docs_item.setIcon(self._get_icon("folder"))
        docs_item.setData("yandex:///Документы", Qt.ItemDataRole.UserRole)

        photos_item = QStandardItem("Фотографии")
        photos_item.setIcon(self._get_icon("folder"))
        photos_item.setData("yandex:///Фотографии", Qt.ItemDataRole.UserRole)

        yandex_item.appendRow(docs_item)
        yandex_item.appendRow(photos_item)

        self.model.appendRow(yandex_item)

        self.tree_view.expandAll()

    def _get_icon(self, icon_type: str) -> QIcon:
        """Возвращает иконку из темы системы."""
        theme_icons = {
            "cloud": QIcon.fromTheme("network-server"),
            "folder": QIcon.fromTheme("folder"),
            "folder-open": QIcon.fromTheme("folder-open"),
        }
        return theme_icons.get(icon_type, QIcon())

    def _on_item_clicked(self, index) -> None:
        """Обработка клика по элементу дерева."""
        item = self.model.itemFromIndex(index)
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                self.folder_selected.emit(path)

    def update_space_info(self, used: int, total: int) -> None:
        """Обновление информации о свободном месте."""
        if total > 0:
            free_gb = (total - used) / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            self.space_label.setText(f"Свободно: {free_gb:.1f} ГБ / {total_gb:.1f} ГБ")
        else:
            self.space_label.setText("Свободно: — / —")