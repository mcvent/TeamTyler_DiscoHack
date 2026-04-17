"""Главное окно приложения."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence
# Импорт для статус-бара
from PyQt6.QtWidgets import QLabel

from gui.views.side_bar import SideBar
from gui.views.file_table import FileTableView
from gui.views.address_bar import AddressBar
from gui.dialogs.progress_dialog import ProgressDialog


class MainWindow(QMainWindow):
    """Главное окно облачного менеджера."""

    def __init__(self) -> None:
        """Инициализация главного окна."""
        super().__init__()
        self._current_path = "/"
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._load_stylesheet()

    def _setup_ui(self) -> None:
        """Настройка основного UI."""
        self.setWindowTitle("Cloud Manager")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 800)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Сплиттер для боковой панели и таблицы
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая панель
        self.side_bar = SideBar()
        self.side_bar.setMinimumWidth(240)
        self.side_bar.setMaximumWidth(400)
        splitter.addWidget(self.side_bar)

        # Правая часть (таблица файлов)
        self.file_table = FileTableView()
        splitter.addWidget(self.file_table)

        splitter.setSizes([280, 920])

        # Добавляем сплиттер в layout с stretch=1
        main_layout.addWidget(splitter, stretch=1)

    def _setup_menu(self) -> None:
        """Настройка главного меню."""
        menubar = self.menuBar()

        # Файл
        file_menu = menubar.addMenu("&Файл")

        new_folder_action = QAction(QIcon.fromTheme("folder-new"), "Новая папка", self)
        new_folder_action.setShortcut(QKeySequence.StandardKey.New)
        new_folder_action.triggered.connect(self._on_new_folder)
        file_menu.addAction(new_folder_action)

        file_menu.addSeparator()

        upload_action = QAction(QIcon.fromTheme("document-open"), "Загрузить файлы...", self)
        upload_action.setShortcut(QKeySequence("Ctrl+U"))
        upload_action.triggered.connect(self._on_upload)
        file_menu.addAction(upload_action)

        download_action = QAction(QIcon.fromTheme("document-save"), "Скачать выбранное", self)
        download_action.setShortcut(QKeySequence.StandardKey.Save)
        download_action.triggered.connect(self._on_download)
        file_menu.addAction(download_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Правка
        # edit_menu = menubar.addMenu("&Правка")
        #
        # copy_action = QAction(QIcon.fromTheme("edit-copy"), "Копировать", self)
        # copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        # edit_menu.addAction(copy_action)
        #
        # cut_action = QAction(QIcon.fromTheme("edit-cut"), "Вырезать", self)
        # cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        # edit_menu.addAction(cut_action)
        #
        # paste_action = QAction(QIcon.fromTheme("edit-paste"), "Вставить", self)
        # paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        # edit_menu.addAction(paste_action)
        #
        # edit_menu.addSeparator()
        #
        # delete_action = QAction(QIcon.fromTheme("edit-delete"), "Удалить", self)
        # delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        # delete_action.triggered.connect(self._on_delete)
        # edit_menu.addAction(delete_action)
        #
        # rename_action = QAction("Переименовать", self)
        # rename_action.setShortcut(QKeySequence("F2"))
        # edit_menu.addAction(rename_action)

        # Вид
        view_menu = menubar.addMenu("&Вид")

        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Обновить", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self._on_refresh)
        view_menu.addAction(refresh_action)

        view_menu.addSeparator()

        show_hidden_action = QAction("Показывать скрытые файлы", self)
        show_hidden_action.setCheckable(True)
        view_menu.addAction(show_hidden_action)

        # Сервис
        # service_menu = menubar.addMenu("&Сервис")
        #
        # settings_action = QAction(QIcon.fromTheme("preferences-system"), "Настройки", self)
        # settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        # settings_action.triggered.connect(self._on_settings)
        # service_menu.addAction(settings_action)

        # Справка
        help_menu = menubar.addMenu("&Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """Настройка панели инструментов."""
        toolbar = QToolBar("Основная")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Навигация
        back_action = QAction(QIcon.fromTheme("go-previous"), "Назад", self)
        back_action.setEnabled(False)
        toolbar.addAction(back_action)

        forward_action = QAction(QIcon.fromTheme("go-next"), "Вперёд", self)
        forward_action.setEnabled(False)
        toolbar.addAction(forward_action)

        up_action = QAction(QIcon.fromTheme("go-up"), "Вверх", self)
        toolbar.addAction(up_action)

        toolbar.addSeparator()

        # ВАЖНО: Создаем address_bar и сохраняем как атрибут
        self.address_bar = AddressBar()
        self.address_bar.setMaximumWidth(600)
        toolbar.addWidget(self.address_bar)

        toolbar.addSeparator()

        # Кнопка обновления
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Обновить", self)
        refresh_action.triggered.connect(self._on_refresh)
        toolbar.addAction(refresh_action)

        # Растягиваем тулбар
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)

        # Операции с файлами
        new_folder_action = QAction(QIcon.fromTheme("folder-new"), "Новая папка", self)
        new_folder_action.triggered.connect(self._on_new_folder)
        toolbar.addAction(new_folder_action)

        upload_action = QAction(QIcon.fromTheme("document-open"), "Загрузить", self)
        upload_action.triggered.connect(self._on_upload)
        toolbar.addAction(upload_action)

        download_action = QAction(QIcon.fromTheme("document-save"), "Скачать", self)
        download_action.triggered.connect(self._on_download)
        toolbar.addAction(download_action)

        delete_action = QAction(QIcon.fromTheme("edit-delete"), "Удалить", self)
        delete_action.triggered.connect(self._on_delete)
        toolbar.addAction(delete_action)

    def _setup_statusbar(self) -> None:
        """Настройка статус-бара."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

        # Индикатор количества элементов
        self.items_label = QLabel("Элементов: 6")
        self.status_bar.addPermanentWidget(self.items_label)

    def _connect_signals(self) -> None:
        """Подключение сигналов."""
        # Боковая панель
        self.side_bar.folder_selected.connect(self._on_folder_selected)
        self.side_bar.add_storage_clicked.connect(self._on_add_storage)

        # Адресная строка
        self.address_bar.path_changed.connect(self._on_path_changed)
        self.address_bar.refresh_clicked.connect(self._on_refresh)

        # Таблица файлов
        self.file_table.file_double_clicked.connect(self._on_file_double_clicked)
        self.file_table.delete_requested.connect(self._on_files_delete)
        self.file_table.download_requested.connect(self._on_files_download)

    def _load_stylesheet(self) -> None:
        """Загрузка стилей."""
        try:
            from pathlib import Path
            style_path = Path(__file__).parent / "resources" / "style.qss"
            if style_path.exists():
                with open(style_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
        except Exception:
            pass  # Стили не загружены, используем системные

    # Обработчики событий (заглушки)

    def _on_new_folder(self) -> None:
        """Создание новой папки."""
        QMessageBox.information(self, "Заглушка", "Создание новой папки")

    def _on_upload(self) -> None:
        """Загрузка файлов."""
        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы для загрузки")
        if files:
            QMessageBox.information(self, "Заглушка", f"Загрузка {len(files)} файлов")

    def _on_download(self) -> None:
        """Скачивание файлов."""
        QMessageBox.information(self, "Заглушка", "Скачивание выбранных файлов")

    def _on_delete(self) -> None:
        """Удаление файлов."""
        QMessageBox.information(self, "Заглушка", "Удаление выбранных элементов")

    def _on_refresh(self) -> None:
        """Обновление текущей папки."""
        self.status_bar.showMessage(f"Обновление {self._current_path}...")

    def _on_settings(self) -> None:
        """Открытие настроек."""
        QMessageBox.information(self, "Заглушка", "Открытие окна настроек")

    def _on_about(self) -> None:
        """О программе."""
        QMessageBox.about(
            self,
            "О программе",
            "Cloud Manager\n\n"
            "Нативный клиент для облачных хранилищ\n"
            "Предполагаемая система использования ALT Linux\n\n"
            "Версия 0.1"
        )

    def _on_folder_selected(self, path: str) -> None:
        """Выбор папки в боковой панели."""
        self._current_path = path
        self.address_bar.set_path(path)
        self.status_bar.showMessage(f"Переход в {path}")

    def _on_path_changed(self, path: str) -> None:
        """Изменение пути в адресной строке."""
        self._current_path = path
        self.status_bar.showMessage(f"Переход в {path}")

    def _on_file_double_clicked(self, path: str, is_dir: bool) -> None:
        """Двойной клик по файлу/папке."""
        if is_dir:
            self._current_path = path
            self.address_bar.set_path(path)
            self.status_bar.showMessage(f"Переход в {path}")
        else:
            QMessageBox.information(self, "Заглушка", f"Открытие файла: {path}")

    def _on_files_delete(self, files: list[str]) -> None:
        """Удаление файлов."""
        QMessageBox.information(self, "Заглушка", f"Удаление: {', '.join(files)}")

    def _on_files_download(self, files: list[str]) -> None:
        """Скачивание файлов."""
        QMessageBox.information(self, "Заглушка", f"Скачивание: {', '.join(files)}")

    def _on_add_storage(self) -> None:
        """Добавление облачного хранилища."""
        QMessageBox.information(self, "Заглушка", "Открытие мастера добавления хранилища")
