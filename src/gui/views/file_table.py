"""Таблица с файлами и папками."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView,
    QAbstractItemView, QMenu, QStyledItemDelegate,
    QLineEdit
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QModelIndex
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QStandardItemModel, QStandardItem


class RenameDelegate(QStyledItemDelegate):
    """Делегат для редактирования имени файла с выделением имени без расширения."""

    def createEditor(self, parent, option, index):
        """Создание редактора с выделением имени файла."""
        editor = QLineEdit(parent)

        # Убираем рамку и отступы
        editor.setFrame(False)
        editor.setTextMargins(8, 0, 0, 0)
        editor.setContentsMargins(8, 0, 0, 0)

        # Стиль для полного совпадения с ячейкой
        editor.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #1976d2;
                border-radius: 2px;
                padding: 0px;
                margin: 0px;
            }
        """)

        full_name = index.data()

        if '.' in full_name:
            base_name = full_name.rsplit('.', 1)[0]
            editor.setText(full_name)
            editor.setSelection(0, len(base_name))
        else:
            editor.setText(full_name)
            editor.selectAll()

        return editor

    def setEditorData(self, editor, index):
        """Установка данных в редактор."""
        value = index.data(Qt.ItemDataRole.EditRole)
        if value:
            editor.setText(str(value))

    def setModelData(self, editor, model, index):
        """Сохранение данных из редактора в модель."""
        new_name = editor.text().strip()
        old_name = index.data()

        if new_name and new_name != old_name:
            model.setData(index, new_name, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        """Обновление геометрии редактора."""
        editor.setGeometry(option.rect)


class FileTableView(QWidget):
    """Виджет таблицы файлов."""

    # Сигналы
    file_double_clicked = pyqtSignal(str, bool)  # путь, is_dir
    file_selected = pyqtSignal(list)  # список выбранных путей
    delete_requested = pyqtSignal(list)
    download_requested = pyqtSignal(list)
    rename_requested = pyqtSignal(str, str)  # old_path, new_name
    properties_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Инициализация таблицы файлов."""
        super().__init__(parent)
        self._setup_ui()
        self._setup_context_menu()
        self._setup_stub_data()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Отключаем все автоматические триггеры редактирования
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Устанавливаем делегат для редактирования имени
        self.rename_delegate = RenameDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(0, self.rename_delegate)

        # Сигналы
        self.table_view.doubleClicked.connect(self._on_double_click)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table_view)

    def _setup_stub_data(self) -> None:
        """Настройка заглушечных данных."""
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Имя", "Размер", "Изменён", "Тип"])

        items = [
            ("..", "", "", "Папка"),
            ("Документы", "", "12.04.2026", "Папка"),
            ("Изображения", "", "10.04.2026", "Папка"),
            ("отчет.pdf", "2.4 МБ", "15.04.2026", "PDF Документ"),
            ("презентация.pptx", "5.1 МБ", "14.04.2026", "Презентация"),
            ("данные.xlsx", "856 КБ", "13.04.2026", "Таблица"),
        ]

        for name, size, modified, ftype in items:
            name_item = QStandardItem(QIcon.fromTheme("folder" if ftype == "Папка" else "text-x-generic"), name)
            name_item.setEditable(True)

            size_item = QStandardItem(size)
            size_item.setEditable(False)

            modified_item = QStandardItem(modified)
            modified_item.setEditable(False)

            type_item = QStandardItem(ftype)
            type_item.setEditable(False)

            name_item.setData(f"/mock/path/{name}", Qt.ItemDataRole.UserRole)

            model.appendRow([name_item, size_item, modified_item, type_item])

        # Подключаем сигнал изменения данных
        model.dataChanged.connect(self._on_data_changed)

        self.table_view.setModel(model)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def _setup_context_menu(self) -> None:
        """Настройка контекстного меню."""
        self.context_menu = QMenu(self)

        self.download_action = QAction(QIcon.fromTheme("document-save"), "Скачать", self)
        self.download_action.setShortcut(QKeySequence.StandardKey.Save)
        self.download_action.triggered.connect(self._on_download)

        self.delete_action = QAction(QIcon.fromTheme("edit-delete"), "Удалить", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self._on_delete)

        self.rename_action = QAction(QIcon.fromTheme("edit-rename"), "Переименовать", self)
        self.rename_action.triggered.connect(self._on_rename_action)

        self.properties_action = QAction(QIcon.fromTheme("document-properties"), "Свойства", self)
        self.properties_action.triggered.connect(self._on_properties)

        self.context_menu.addAction(self.download_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)
        self.context_menu.addAction(self.rename_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.properties_action)

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш."""
        if event.key() == Qt.Key.Key_Delete:
            self._on_delete()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Открыть выбранный элемент по Enter
            self._open_selected()
        else:
            super().keyPressEvent(event)

    def _on_double_click(self, index: QModelIndex) -> None:
        """Обработка двойного клика - открытие файла/папки."""
        self._open_item(index)

    def _open_selected(self) -> None:
        """Открытие выбранного элемента."""
        indexes = self.table_view.selectionModel().selectedRows(0)
        if indexes:
            self._open_item(indexes[0])

    def _open_item(self, index: QModelIndex) -> None:
        """Открытие элемента по индексу."""
        model = self.table_view.model()
        name_index = model.index(index.row(), 0)
        name = model.data(name_index)
        ftype = model.data(model.index(index.row(), 3))
        path = model.data(name_index, Qt.ItemDataRole.UserRole)

        is_dir = ftype == "Папка"
        if name == "..":
            self.file_double_clicked.emit("..", True)
        else:
            self.file_double_clicked.emit(path, is_dir)

    def _start_rename_current(self) -> None:
        """Запуск редактирования текущего элемента."""
        indexes = self.table_view.selectionModel().selectedRows(0)
        if indexes:
            # Редактируем только колонку с именем
            self.table_view.edit(indexes[0])

    def _on_data_changed(self, top_left: QModelIndex, bottom_right: QModelIndex) -> None:
        """Обработка изменения данных в модели (после редактирования)."""
        if top_left.column() == 0:
            old_path = top_left.data(Qt.ItemDataRole.UserRole)
            new_name = top_left.data()
            self.rename_requested.emit(old_path, new_name)

    def _show_context_menu(self, pos: QPoint) -> None:
        """Показ контекстного меню."""
        has_selection = len(self.table_view.selectionModel().selectedRows()) > 0
        single_selection = len(self.table_view.selectionModel().selectedRows()) == 1

        self.download_action.setEnabled(has_selection)
        self.delete_action.setEnabled(has_selection)
        self.rename_action.setEnabled(single_selection)
        self.properties_action.setEnabled(single_selection)

        self.context_menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def _get_selected_items(self) -> list[str]:
        """Получение списка выбранных элементов."""
        selected = []
        for index in self.table_view.selectionModel().selectedRows(0):
            selected.append(self.table_view.model().data(index))
        return selected

    def _get_selected_paths(self) -> list[str]:
        """Получение путей выбранных элементов."""
        paths = []
        for index in self.table_view.selectionModel().selectedRows(0):
            path = self.table_view.model().data(index, Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths

    def _on_download(self) -> None:
        """Обработка скачивания."""
        selected = self._get_selected_items()
        if selected:
            self.download_requested.emit(selected)

    def _on_delete(self) -> None:
        """Обработка удаления."""
        selected = self._get_selected_items()
        if selected:
            self.delete_requested.emit(selected)

    def _on_rename_action(self) -> None:
        """Обработка действия переименования из меню."""
        self._start_rename_current()

    def _on_properties(self) -> None:
        """Обработка показа свойств."""
        paths = self._get_selected_paths()
        if len(paths) == 1:
            self.properties_requested.emit(paths[0])