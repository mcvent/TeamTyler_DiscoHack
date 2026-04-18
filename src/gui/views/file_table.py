"""Таблица с файлами и папками."""
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView,
    QAbstractItemView, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QModelIndex
from PyQt6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem

from api.common.models import CloudFile
from api.common.base_provider import BaseCloudProvider


class FileTableModel(QStandardItemModel):
    """Модель для отображения файлов."""

    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(["Имя", "Размер", "Тип"])
        self._items: List[CloudFile] = []

    def set_items(self, items: List[CloudFile]) -> None:
        """Установка элементов."""
        self._items = items
        self.removeRows(0, self.rowCount())

        for item in items:
            name_item = QStandardItem(item.name)
            name_item.setData(item, Qt.ItemDataRole.UserRole)
            name_item.setEditable(False)

            if item.is_dir:
                name_item.setIcon(QIcon.fromTheme("folder"))
                size_str = ""
                type_str = "Папка"
            else:
                name_item.setIcon(QIcon.fromTheme("text-x-generic"))
                size_str = self._format_size(item.size)
                type_str = item.mime_type or "Файл"

            size_item = QStandardItem(size_str)
            size_item.setEditable(False)

            type_item = QStandardItem(type_str)
            type_item.setEditable(False)

            self.appendRow([name_item, size_item, type_item])

    def _format_size(self, size: int) -> str:
        """Форматирование размера."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def get_item(self, row: int) -> Optional[CloudFile]:
        """Получить элемент по строке."""
        if 0 <= row < len(self._items):
            return self._items[row]
        return None


class FileTableView(QWidget):
    """Виджет таблицы файлов."""

    file_double_clicked = pyqtSignal(CloudFile)
    delete_requested = pyqtSignal(list)
    download_requested = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_provider: Optional[BaseCloudProvider] = None
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_view.setAlternatingRowColors(False)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.model = FileTableModel()
        self.table_view.setModel(self.model)

        self.table_view.doubleClicked.connect(self._on_double_click)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table_view)

    def _setup_context_menu(self) -> None:
        """Настройка контекстного меню."""
        self.context_menu = QMenu(self)

        self.download_action = QAction(QIcon.fromTheme("document-save"), "Скачать", self)
        self.download_action.triggered.connect(self._on_download)

        self.delete_action = QAction(QIcon.fromTheme("edit-delete"), "Удалить", self)
        self.delete_action.triggered.connect(self._on_delete)

        self.context_menu.addAction(self.download_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)

    def set_files(self, files: List[CloudFile], provider: BaseCloudProvider) -> None:
        """Установка файлов."""
        self._current_provider = provider
        self.model.set_items(files)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def get_selected_items(self) -> List[CloudFile]:
        """Получить выбранные элементы."""
        items = []
        for index in self.table_view.selectionModel().selectedRows(0):
            item = self.model.get_item(index.row())
            if item:
                items.append(item)
        return items

    def _on_double_click(self, index: QModelIndex) -> None:
        """Обработка двойного клика."""
        item = self.model.get_item(index.row())
        if item:
            self.file_double_clicked.emit(item)

    def _show_context_menu(self, pos: QPoint) -> None:
        """Показ контекстного меню."""
        has_selection = len(self.get_selected_items()) > 0
        self.download_action.setEnabled(has_selection)
        self.delete_action.setEnabled(has_selection)
        self.context_menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def _on_download(self) -> None:
        """Скачивание."""
        items = self.get_selected_items()
        if items:
            self.download_requested.emit(items)

    def _on_delete(self) -> None:
        """Удаление."""
        items = self.get_selected_items()
        if items:
            self.delete_requested.emit(items)