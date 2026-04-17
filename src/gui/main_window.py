"""Главное окно приложения."""
import sys
from pathlib import Path
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QSizePolicy, QInputDialog, QLabel
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.common.base_provider import BaseCloudProvider
from api.common.models import CloudFile
from api.common.exceptions import CloudError, CloudNotFoundError

from core.local.local_provider import LocalFileSystemProvider
from core.local.cloud_bridge import CloudBridge
from core.local.cloud_provider_adapter import CloudProviderAdapter

from .views.side_bar import SideBar
from .views.file_table import FileTableView
from .views.address_bar import AddressBar
from .workers import ListDirectoryWorker, DownloadWorker, UploadWorker, SearchWorker
from .dialogs.progress_dialog import ProgressDialog

from PyQt6.QtWidgets import QProgressBar
class MainWindow(QMainWindow):
    """Главное окно облачного менеджера."""

    def __init__(self) -> None:
        """Инициализация главного окна."""
        super().__init__()
        self._current_provider: Optional[BaseCloudProvider] = None
        self._current_path: str = ""
        self._providers: Dict[str, BaseCloudProvider] = {}
        self._list_worker: Optional[ListDirectoryWorker] = None

        self._init_providers()
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._load_stylesheet()

        # Начальная загрузка
        self._navigate_to_provider('local', self._providers['local'].get_mounts_root())

    def _init_providers(self) -> None:
        """Инициализация провайдеров."""
        # Локальная ФС
        self._providers['local'] = LocalFileSystemProvider()

        # Яндекс.Диск через CloudBridge
        cloud_path = Path.home() / 'YandexDisk'
        cloud_path.mkdir(parents=True, exist_ok=True)
        cloud_bridge = CloudBridge(cloud_path)
        self._providers['cloud'] = CloudProviderAdapter(cloud_bridge)

    def _setup_ui(self) -> None:
        """Настройка основного UI."""
        self.setWindowTitle("Cloud Manager")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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
        main_layout.addWidget(splitter, stretch=1)

        # Передаём провайдеры в боковую панель
        self.side_bar.set_providers(self._providers)

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

        delete_action = QAction(QIcon.fromTheme("edit-delete"), "Удалить", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self._on_delete)
        file_menu.addAction(delete_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

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

        toolbar.addSeparator()

        # Адресная строка
        self.address_bar = AddressBar()
        self.address_bar.setMaximumWidth(600)
        toolbar.addWidget(self.address_bar)

        toolbar.addSeparator()

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

        # Прогресс-бар для длительных операций
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.items_label = QLabel("Элементов: 0")
        self.status_bar.addPermanentWidget(self.items_label)

    def _connect_signals(self) -> None:
        """Подключение сигналов."""
        self.side_bar.provider_selected.connect(self._on_provider_selected)
        self.address_bar.search_requested.connect(self._on_search)
        self.address_bar.path_changed.connect(self._on_path_changed)
        self.address_bar.refresh_clicked.connect(self._on_refresh)
        self.address_bar.go_up_clicked.connect(self._on_go_up)
        self.file_table.file_double_clicked.connect(self._on_file_double_clicked)
        self.file_table.delete_requested.connect(self._on_files_delete)
        self.file_table.download_requested.connect(self._on_files_download)

    def _load_stylesheet(self) -> None:
        """Загрузка стилей."""
        try:
            style_path = Path(__file__).parent / "resources" / "style.qss"
            if style_path.exists():
                with open(style_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())

        except Exception:
            pass

    # ============ Навигация ============

    def _navigate_to_provider(self, provider_key: str, path: str) -> None:
        """Переход к провайдеру и пути."""
        self._current_provider = self._providers.get(provider_key)
        if not self._current_provider:
            return

        self._current_path = path
        self._load_directory(path)

    def _load_directory(self, path: str) -> None:
        """Загрузка содержимого директории."""
        if not self._current_provider:
            return

        self.status_bar.showMessage(f"Загрузка {path}...")

        # Отменяем предыдущий воркер
        if self._list_worker and self._list_worker.isRunning():
            self._list_worker.terminate()
            self._list_worker.wait()

        self._list_worker = ListDirectoryWorker(self._current_provider, path)
        self._list_worker.finished.connect(self._on_directory_loaded)
        self._list_worker.error.connect(self._on_directory_error)
        self._list_worker.start()

    def _on_directory_loaded(self, files: list) -> None:
        """Обработка загрузки директории."""
        self.file_table.set_files(files, self._current_provider)
        self.address_bar.set_path(self._current_path)
        self.items_label.setText(f"Элементов: {len(files)}")
        self.status_bar.showMessage(f"Загружено {len(files)} элементов")


    def _on_directory_error(self, error: str) -> None:
        """Обработка ошибки загрузки."""
        self.status_bar.showMessage(f"Ошибка: {error}")
        self.items_label.setText("Элементов: 0")

    # ============ Обработчики сигналов ============

    def _on_provider_selected(self, provider: BaseCloudProvider, path: str) -> None:
        """Выбор провайдера в боковой панели."""
        self._current_provider = provider
        self._current_path = path
        self._load_directory(path)

    def _on_path_changed(self, path: str) -> None:
        """Изменение пути в адресной строке."""
        self._current_path = path
        self._load_directory(path)

    def _on_refresh(self) -> None:
        """Обновление текущей папки."""
        if self._current_provider and self._current_path:
            self._load_directory(self._current_path)

    def _on_search(self, query: str) -> None:
        """Поиск файлов рекурсивно."""
        if not self._current_provider or not self._current_path:
            return

        if not query:
            self._load_directory(self._current_path)
            return

        # Показываем прогресс-бар
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Бесконечный прогресс
        self.status_bar.showMessage(f"🔍 Поиск '{query}'...")

        # Блокируем кнопку поиска
        self.address_bar.search_btn.setEnabled(False)

        # Запускаем поиск в отдельном потоке
        self._search_worker = SearchWorker(self._current_provider, self._current_path, query)
        self._search_worker.finished.connect(self._on_search_finished)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()

    def _on_go_up(self) -> None:
        """Переход на уровень выше."""
        if not self._current_provider:
            return

        parent_path = None

        if hasattr(self._current_provider, 'get_parent_path'):
            parent_path = self._current_provider.get_parent_path(self._current_path)

        if parent_path and parent_path != self._current_path:
            self._current_path = parent_path
            self._load_directory(parent_path)
            self.address_bar.set_path(parent_path)

    def _on_file_double_clicked(self, file_item: CloudFile) -> None:
        """Двойной клик по файлу/папке."""
        if file_item.is_dir:
            self._current_path = file_item.path
            self._load_directory(file_item.path)
        else:
            self._open_file(file_item)

    def _on_new_folder(self) -> None:
        """Создание новой папки."""
        if not self._current_provider:
            return

        name, ok = QInputDialog.getText(self, "Новая папка", "Имя папки:")
        if ok and name:
            try:
                path = self._current_path.rstrip('/') + '/' + name
                self._current_provider.create_folder(path)
                self._on_refresh()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось создать папку: {e}")

    def _on_upload(self) -> None:
        """Загрузка файлов."""
        if not self._current_provider:
            return

        files, _ = QFileDialog.getOpenFileNames(self, "Выберите файлы для загрузки")
        if not files:
            return

        progress = ProgressDialog("Загрузка файлов", self)
        progress.set_cancellable(False)
        progress.show()

        success_count = 0
        for i, file_path in enumerate(files):
            remote_path = self._current_path.rstrip('/') + '/' + Path(file_path).name
            progress.set_status(f"Загрузка: {Path(file_path).name}", f"{i+1} из {len(files)}")

            try:
                self._current_provider.upload_file(file_path, remote_path)
                success_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить {file_path}: {e}")

        progress.operation_finished(True)
        self.status_bar.showMessage(f"Загружено {success_count} из {len(files)} файлов")
        self._on_refresh()

    def _on_download(self) -> None:
        """Скачивание выбранных файлов."""
        selected = self.file_table.get_selected_items()
        if not selected:
            QMessageBox.information(self, "Инфо", "Выберите файлы для скачивания")
            return

        dest_dir = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if not dest_dir:
            return

        progress = ProgressDialog("Скачивание файлов", self)
        progress.set_cancellable(False)
        progress.show()

        success_count = 0
        for i, file_item in enumerate(selected):
            if file_item.is_dir:
                continue

            progress.set_status(f"Скачивание: {file_item.name}", f"{i+1} из {len(selected)}")
            local_path = Path(dest_dir) / file_item.name

            try:
                self._current_provider.download_file(file_item.path, str(local_path))
                success_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось скачать {file_item.name}: {e}")

        progress.operation_finished(True)
        self.status_bar.showMessage(f"Скачано {success_count} из {len(selected)} файлов")

    def _on_files_download(self, files: list) -> None:
        """Скачивание файлов через сигнал."""
        self._on_download()

    def _on_delete(self) -> None:
        """Удаление выбранных файлов."""
        selected = self.file_table.get_selected_items()
        if not selected:
            QMessageBox.information(self, "Инфо", "Выберите файлы для удаления")
            return

        names = [f.name for f in selected]
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить выбранные элементы?\n\n{', '.join(names[:5])}"
            + (f"\n... и ещё {len(names)-5}" if len(names) > 5 else ""),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        success_count = 0
        for file_item in selected:
            try:
                self._current_provider.delete_file(file_item.path)
                success_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось удалить {file_item.name}: {e}")

        self.status_bar.showMessage(f"Удалено {success_count} из {len(selected)} элементов")
        self._on_refresh()

    def _on_files_delete(self, files: list) -> None:
        """Удаление файлов через сигнал."""
        self._on_delete()

    def _open_file(self, file_item: CloudFile) -> None:
        """Открытие файла."""
        if hasattr(self._current_provider, 'open_file'):
            success = self._current_provider.open_file(file_item.path)
            if not success:
                QMessageBox.warning(self, "Ошибка", f"Не удалось открыть {file_item.name}")
        else:
            QMessageBox.information(self, "Инфо", f"Открытие: {file_item.name}")

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

    def _on_search_finished(self, results: list) -> None:
        """Обработка завершения поиска."""
        # Скрываем прогресс-бар
        self.progress_bar.setVisible(False)
        self.address_bar.search_btn.setEnabled(True)

        if results:
            self.file_table.set_files(results, self._current_provider)
            self.items_label.setText(f"Найдено: {len(results)}")
            self.status_bar.showMessage(f" Найдено {len(results)} элементов по запросу")
            self.address_bar.set_path(f"🔍 Результаты поиска ({len(results)})")
        else:
            QMessageBox.information(self, "Поиск", "Ничего не найдено")
            self.status_bar.showMessage(" Ничего не найдено")

    def _on_search_error(self, error: str) -> None:
        """Обработка ошибки поиска."""
        self.progress_bar.setVisible(False)
        self.address_bar.search_btn.setEnabled(True)
        self.status_bar.showMessage(f" Ошибка поиска: {error}")
        QMessageBox.warning(self, "Ошибка поиска", error)