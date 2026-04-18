"""Таблица/иконки с файлами и папками."""
from typing import List, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QListWidget, QListWidgetItem,
    QStackedWidget
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QModelIndex, QSize
from PyQt6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem

from api.common.models import CloudFile
from api.common.base_provider import BaseCloudProvider


class FileTableModel(QStandardItemModel):
    """Модель для отображения файлов в таблице."""

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
                name_item.setIcon(self._get_file_icon(item.name))
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

    def _get_file_icon(self, filename: str) -> QIcon:
        """Получить иконку по расширению файла."""
        ext = Path(filename).suffix.lower()
        icon_map = {
            '.jpg': QIcon.fromTheme("image-x-generic"),
            '.jpeg': QIcon.fromTheme("image-x-generic"),
            '.png': QIcon.fromTheme("image-x-generic"),
            '.gif': QIcon.fromTheme("image-x-generic"),
            '.pdf': QIcon.fromTheme("application-pdf"),
            '.doc': QIcon.fromTheme("application-msword"),
            '.docx': QIcon.fromTheme("application-msword"),
            '.xls': QIcon.fromTheme("application-vnd.ms-excel"),
            '.xlsx': QIcon.fromTheme("application-vnd.ms-excel"),
            '.mp3': QIcon.fromTheme("audio-x-generic"),
            '.mp4': QIcon.fromTheme("video-x-generic"),
        }
        return icon_map.get(ext, QIcon.fromTheme("text-x-generic"))

    def get_item(self, row: int) -> Optional[CloudFile]:
        """Получить элемент по строке."""
        if 0 <= row < len(self._items):
            return self._items[row]
        return None


class FileTableView(QWidget):
    """Виджет таблицы/иконок файлов."""

    file_double_clicked = pyqtSignal(CloudFile)
    delete_requested = pyqtSignal(list)
    download_requested = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_provider: Optional[BaseCloudProvider] = None
        self._current_items: List[CloudFile] = []
        self._view_mode = "table"
        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Стек для переключения между видами
        self.stacked_widget = QStackedWidget()

        # ============ ИКОНКИ ============
        self.icon_view = QListWidget()
        self.icon_view.setViewMode(QListWidget.ViewMode.IconMode)
        self.icon_view.setIconSize(QSize(64, 64))
        self.icon_view.setGridSize(QSize(100, 100))
        self.icon_view.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.icon_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.icon_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.icon_view.setSpacing(10)

        self.icon_view.doubleClicked.connect(self._on_icon_double_click)
        self.icon_view.customContextMenuRequested.connect(self._show_context_menu)

        self.stacked_widget.addWidget(self.icon_view)

        # ============ ТАБЛИЦА ============
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

        self.table_model = FileTableModel()
        self.table_view.setModel(self.table_model)

        self.table_view.doubleClicked.connect(self._on_table_double_click)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

        self.stacked_widget.addWidget(self.table_view)



        layout.addWidget(self.stacked_widget)

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

    def set_view_mode(self, mode: str) -> None:
        """Переключение между таблицей и иконками."""
        self._view_mode = mode
        if mode == "table":
            self.stacked_widget.setCurrentIndex(0)
        else:
            self.stacked_widget.setCurrentIndex(1)
            self._update_icon_view()

    def _update_icon_view(self) -> None:
        """Обновить отображение иконок."""
        self.icon_view.clear()
        for item in self._current_items:
            list_item = QListWidgetItem(item.name)
            list_item.setData(Qt.ItemDataRole.UserRole, item)

            if item.is_dir:
                list_item.setIcon(QIcon.fromTheme("folder"))
            else:
                ext = Path(item.name).suffix.lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    list_item.setIcon(QIcon.fromTheme("image-x-generic"))
                elif ext == '.pdf':
                    list_item.setIcon(QIcon.fromTheme("application-pdf"))
                else:
                    list_item.setIcon(QIcon.fromTheme("text-x-generic"))

            # Добавляем размер под иконкой
            if not item.is_dir:
                size_text = self._format_size(item.size)
                list_item.setToolTip(f"{item.name}\nРазмер: {size_text}")
            else:
                list_item.setToolTip(f"{item.name}\nПапка")

            self.icon_view.addItem(list_item)

    def _format_size(self, size: int) -> str:
        """Форматирование размера."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def set_files(self, files: List[CloudFile], provider: BaseCloudProvider) -> None:
        """Установка файлов."""
        self._current_provider = provider
        self._current_items = files
        self.table_model.set_items(files)
        self._update_icon_view()

        # Настройка ширины колонок
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def get_selected_items(self) -> List[CloudFile]:
        """Получить выбранные элементы."""
        items = []

        if self._view_mode == "table":
            for index in self.table_view.selectionModel().selectedRows(0):
                item = self.table_model.get_item(index.row())
                if item:
                    items.append(item)
        else:
            for list_item in self.icon_view.selectedItems():
                item = list_item.data(Qt.ItemDataRole.UserRole)
                if item:
                    items.append(item)

        return items

    def _on_table_double_click(self, index: QModelIndex) -> None:
        """Обработка двойного клика в таблице."""
        item = self.table_model.get_item(index.row())
        if item:
            self.file_double_clicked.emit(item)

    def _on_icon_double_click(self, index) -> None:
        """Обработка двойного клика в иконках."""
        list_item = self.icon_view.itemFromIndex(index)
        if list_item:
            item = list_item.data(Qt.ItemDataRole.UserRole)
            if item:
                self.file_double_clicked.emit(item)

    def _show_context_menu(self, pos: QPoint) -> None:
        """Показ контекстного меню."""
        has_selection = len(self.get_selected_items()) > 0
        self.download_action.setEnabled(has_selection)
        self.delete_action.setEnabled(has_selection)

        if self._view_mode == "table":
            self.context_menu.exec(self.table_view.viewport().mapToGlobal(pos))
        else:
            self.context_menu.exec(self.icon_view.viewport().mapToGlobal(pos))

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