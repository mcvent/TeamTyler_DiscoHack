"""Левая панель навигации с провайдерами."""
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QLabel,
    QPushButton, QHBoxLayout, QInputDialog, QMessageBox, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from gui.workers import ListDirectoryWorker, DownloadWorker, UploadWorker, SearchWorker

from api.common.base_provider import BaseCloudProvider


class SideBar(QWidget):
    """Боковая панель с деревом провайдеров."""

    provider_selected = pyqtSignal(object, str)  # provider, path
    add_storage_clicked = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Инициализация боковой панели."""
        super().__init__(parent)
        self._providers: Dict[str, BaseCloudProvider] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setMinimumWidth(200)

        # Заголовок
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 8)

        title = QLabel("Файловые системы")
        title.setStyleSheet("font-weight: bold; font-size: 18px;")
        header_layout.addWidget(title)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setToolTip("Обновить")
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(header_widget)

        # Дерево
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setIndentation(0)
        self.tree_view.setAnimated(True)
        self.tree_view.setRootIsDecorated(False)

        self.tree_view.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.clicked.connect(self._on_item_clicked)
        self.tree_view.doubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.tree_view)

    def set_providers(self, providers: Dict[str, BaseCloudProvider]) -> None:
        """Установка провайдеров."""
        self._providers = providers
        self._build_tree()

    def _on_refresh_clicked(self) -> None:
        """Обработка клика по кнопке обновления."""
        # Обновляем кэш локального провайдера
        if 'local' in self._providers and hasattr(self._providers['local'], 'refresh'):
            self._providers['local'].refresh()

        # Сохраняем текущий выбор
        current_index = self.tree_view.currentIndex()
        if current_index.isValid():
            item = self.model.itemFromIndex(current_index)
            self._last_selected_provider = item.data(Qt.ItemDataRole.UserRole)
            self._last_selected_path = item.data(Qt.ItemDataRole.UserRole + 1)

        # Перестраиваем дерево (теперь с восстановлением выбора)
        self._build_tree()

        # Эмитим сигнал для обновления текущей папки в main_window
        self.refresh_requested.emit()

    def _build_tree(self) -> None:
        """Построение дерева."""
        self.model.clear()

        # Сохраняем текущий выбранный провайдер и путь
        current_provider = None
        current_path = None
        if hasattr(self, '_last_selected_provider'):
            current_provider = self._last_selected_provider
            current_path = self._last_selected_path

        for key, provider in self._providers.items():
            name = provider.get_provider_name() if hasattr(provider, 'get_provider_name') else key
            provider_item = QStandardItem(name)
            provider_item.setData(provider, Qt.ItemDataRole.UserRole)
            provider_item.setEditable(False)

            root_path = provider.get_root_path() if hasattr(provider, 'get_root_path') else "/"
            provider_item.setData(root_path, Qt.ItemDataRole.UserRole + 1)

            if key == "local":
                provider_item.setIcon(QIcon.fromTheme("drive-harddisk"))
            else:
                if hasattr(provider, 'has_token') and not provider.has_token():
                    provider_item.setIcon(QIcon.fromTheme("folder-remote"))
                    # provider_item.setText(f"{name} (не подключен)")
                else:
                    provider_item.setIcon(QIcon.fromTheme("folder-remote"))

            self.model.appendRow(provider_item)

            # Если это был текущий провайдер, запоминаем его item
            if current_provider == provider:
                self._last_provider_item = provider_item

        self.tree_view.expandAll()

        # Восстанавливаем выбор и обновляем таблицу
        if current_provider and current_path:
            # Находим item для текущего провайдера
            for row in range(self.model.rowCount()):
                item = self.model.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == current_provider:
                    index = self.model.indexFromItem(item)
                    self.tree_view.setCurrentIndex(index)
                    # Эмитим сигнал для обновления таблицы
                    self.provider_selected.emit(current_provider, current_path)
                    break

    def _on_item_clicked(self, index) -> None:
        """Обработка клика."""
        item = self.model.itemFromIndex(index)
        if not item:
            return

        provider = item.data(Qt.ItemDataRole.UserRole)
        path = item.data(Qt.ItemDataRole.UserRole + 1)

        if provider and path:
            # Сохраняем текущий выбор
            self._last_selected_provider = provider
            self._last_selected_path = path
            self.provider_selected.emit(provider, path)

    def _on_item_double_clicked(self, index) -> None:
        """Обработка двойного клика - загрузка содержимого."""
        item = self.model.itemFromIndex(index)
        if not item:
            return

        provider = item.data(Qt.ItemDataRole.UserRole)
        path = item.data(Qt.ItemDataRole.UserRole + 1)

        if not provider or not path:
            return

        # Очищаем старые дочерние элементы
        item.removeRows(0, item.rowCount())

        try:
            items = provider.list_files(path)

            for file_item in items:
                if not file_item.is_dir:
                    continue

                child = QStandardItem(file_item.name)
                child.setData(provider, Qt.ItemDataRole.UserRole)
                child.setData(file_item.path, Qt.ItemDataRole.UserRole + 1)
                child.setIcon(QIcon.fromTheme("folder"))
                child.setEditable(False)  # ⚠️ Запрещаем редактирование дочерних элементов

                dummy = QStandardItem("")
                dummy.setEnabled(False)
                dummy.setEditable(False)  # ⚠️ Запрещаем редактирование заглушки
                child.appendRow(dummy)

                item.appendRow(child)

        except Exception as e:
            error_item = QStandardItem(f"Ошибка: {e}")
            error_item.setEnabled(False)
            error_item.setEditable(False)
            item.appendRow(error_item)

        # Эмитим сигнал выбора, чтобы основная панель тоже обновилась
        self.provider_selected.emit(provider, path)

    def refresh_tree(self) -> None:
        """Публичный метод обновления дерева."""
        self._on_refresh_clicked()
