"""Главное окно приложения."""
import sys
from pathlib import Path
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QSizePolicy, QInputDialog, QLabel, QProgressBar
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
        self._search_mode = False
        self._pre_search_path = ""

        self._init_providers()
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._load_stylesheet()
        self._update_auth_status()
        self._update_sync_status()


        # Начальная загрузка
        self._navigate_to_provider('local', self._providers['local'].get_mounts_root())

        cloud_provider = self._providers.get('cloud')
        if cloud_provider and hasattr(cloud_provider, '_bridge'):
            if cloud_provider._bridge.has_token() and cloud_provider._bridge._sync_watcher:
                cloud_provider._bridge._sync_watcher.refresh_callback = self._on_sync_refresh
    def _init_providers(self) -> None:
        """Инициализация провайдеров."""
        self._providers['local'] = LocalFileSystemProvider()

        cloud_path = Path.home() / 'YandexDisk'
        cloud_path.mkdir(parents=True, exist_ok=True)
        cloud_bridge = CloudBridge(cloud_path)

        cloud_adapter = CloudProviderAdapter(cloud_bridge)

        # Устанавливаем callback позже, когда UI будет готов
        if cloud_bridge.has_token():
            # Сохраняем callback для later
            self._pending_sync_callback = True

        self._providers['cloud'] = cloud_adapter


    def _setup_ui(self) -> None:
        """Настройка основного UI."""
        self.setWindowTitle("Cloud Manager")
        self.setMinimumSize(1400, 600)
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
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


        account_menu = menubar.addMenu("&Аккаунт")

        self.login_action = QAction("Войти в Яндекс.Диск", self)
        self.login_action.triggered.connect(self._on_login)
        account_menu.addAction(self.login_action)

        self.logout_action = QAction("Выйти из Яндекс.Диска", self)
        self.logout_action.triggered.connect(self._on_logout)
        self.logout_action.setEnabled(False)
        account_menu.addAction(self.logout_action)

        account_menu.addSeparator()

        # Статус в меню
        self.status_action = QAction("Статус: не авторизован", self)
        self.status_action.setEnabled(False)
        account_menu.addAction(self.status_action)

        # Справка
        help_menu = menubar.addMenu("&Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """Настройка панели инструментов."""
        toolbar = QToolBar("Панель инструментов")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
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

        # Кнопка переключения вида
        self.toggle_view_btn = QAction(QIcon.fromTheme("view-list-icons"), "Вид иконками", self)
        self.toggle_view_btn.setCheckable(True)
        self.toggle_view_btn.triggered.connect(self._toggle_view)
        toolbar.addAction(self.toggle_view_btn)

    def _toggle_view(self, checked):
        if checked:
            self.file_table.set_view_mode("icons")
            self.toggle_view_btn.setIcon(QIcon.fromTheme("view-list-details"))
            self.toggle_view_btn.setText("Вид таблицей")
        else:
            self.file_table.set_view_mode("table")
            self.toggle_view_btn.setIcon(QIcon.fromTheme("view-list-icons"))
            self.toggle_view_btn.setText("Вид иконками")

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

        self.sync_label = QLabel("Синхр: выкл")
        self.sync_label.setStyleSheet("color: #757575; padding: 0 8px;")
        self.status_bar.addPermanentWidget(self.sync_label)

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

        # Если мы в режиме поиска, выход из него
        if hasattr(self, '_search_mode') and self._search_mode:
            self._search_mode = False
            self._current_path = self._pre_search_path
            self._load_directory(self._current_path)
            self.address_bar.set_path(self._current_path)
            self.status_bar.showMessage(f"Выход из поиска")
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
        """Скачивание выбранных файлов в папку Downloads."""
        selected = self.file_table.get_selected_items()
        if not selected:
            QMessageBox.information(self, "Инфо", "Выберите файлы для скачивания")
            return

        cloud_provider = self._providers.get('cloud')
        if not cloud_provider or not hasattr(cloud_provider, '_bridge'):
            QMessageBox.warning(self, "Ошибка", "Облачный провайдер не доступен")
            return

        progress = ProgressDialog("Скачивание файлов", self)
        progress.set_cancellable(False)
        progress.show()

        success_count = 0
        for i, file_item in enumerate(selected):
            if file_item.is_dir:
                continue

            progress.set_status(f"Скачивание: {file_item.name}", f"{i + 1} из {len(selected)}")

            try:
                if cloud_provider._bridge.download_file(file_item.path, None):
                    success_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось скачать {file_item.name}: {e}")

        progress.operation_finished(True)

        downloads_path = cloud_provider._bridge.downloads_path
        self.status_bar.showMessage(f"Скачано {success_count} из {len(selected)} файлов в {downloads_path}")
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
        self.progress_bar.setVisible(False)
        self.address_bar.search_btn.setEnabled(True)

        if results:
            # Сохраняем исходный путь для кнопки "вверх"
            self._search_mode = True
            self._search_results = results
            self._pre_search_path = self._current_path  # Запоминаем путь до поиска

            self.file_table.set_files(results, self._current_provider)
            self.items_label.setText(f"Найдено: {len(results)}")
            self.status_bar.showMessage(f"Найдено {len(results)} элементов")
            self.address_bar.set_path(f"Результаты поиска ({len(results)})")

            # Кнопка "вверх" должна возвращать к папке, где был поиск
            self.address_bar.up_btn.setEnabled(True)
        else:
            QMessageBox.information(self, "Поиск", "Ничего не найдено")
            self.status_bar.showMessage("Ничего не найдено")

    def _on_search_error(self, error: str) -> None:
        """Обработка ошибки поиска."""
        self.progress_bar.setVisible(False)
        self.address_bar.search_btn.setEnabled(True)
        self.status_bar.showMessage(f" Ошибка поиска: {error}")
        QMessageBox.warning(self, "Ошибка поиска", error)

    def _on_login(self) -> None:
        """Вход в Яндекс.Диск."""
        from gui.dialogs.login_dialog import LoginDialog

        dialog = LoginDialog(self)
        if dialog.exec():
            token = dialog.get_token()
            if token:
                from api.providers.yadisk.auth_manager import AuthManager
                AuthManager.save_token(token)

                cloud_provider = self._providers.get('cloud')
                if cloud_provider and hasattr(cloud_provider, 'setup_token'):
                    # Передаём callback для обновления
                    cloud_provider.setup_token(token, self._on_sync_refresh)

                self._update_auth_status()
                self.side_bar.refresh_tree()
                self._update_sync_status()

                QMessageBox.information(self, "Успех", "Вход выполнен успешно")

    def _on_sync_refresh(self) -> None:
        """Callback для обновления GUI при синхронизации."""
        # Обновляем только если сейчас в облаке
        cloud_provider = self._providers.get('cloud')
        if self._current_provider == cloud_provider and self._current_path:
            # Используем тот же механизм, что и кнопка обновления
            self._load_directory(self._current_path)

    def _update_sync_status(self) -> None:
        """Обновление индикатора синхронизации."""
        cloud_provider = self._providers.get('cloud')
        if cloud_provider and hasattr(cloud_provider, '_bridge'):
            if cloud_provider._bridge.is_sync_running():
                self.sync_label.setText("Синхр: вкл")
                self.sync_label.setStyleSheet("color: #4caf50; padding: 0 8px;")
            else:
                self.sync_label.setText("Синхр: выкл")
                self.sync_label.setStyleSheet("color: #757575; padding: 0 8px;")
        else:
            self.sync_label.setText("Синхр: выкл")
            self.sync_label.setStyleSheet("color: #757575; padding: 0 8px;")

    def _update_auth_status(self) -> None:
        """Обновление статуса авторизации в меню."""
        if not hasattr(self, 'status_action'):
            return

        cloud_provider = self._providers.get('cloud')
        is_authorized = False

        if cloud_provider and hasattr(cloud_provider, 'has_token'):
            is_authorized = cloud_provider.has_token()

        if is_authorized:
            self.status_action.setText("Статус: авторизован")
            self.login_action.setEnabled(False)
            self.logout_action.setEnabled(True)
        else:
            self.status_action.setText("Статус: не авторизован")
            self.login_action.setEnabled(True)
            self.logout_action.setEnabled(False)

    def _on_logout(self) -> None:
        """Выход из Яндекс.Диска."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Выйти из аккаунта Яндекс.Диска?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            cloud_provider = self._providers.get('cloud')

            # Останавливаем синхронизацию перед выходом
            if cloud_provider and hasattr(cloud_provider, '_bridge'):
                cloud_provider._bridge.stop_sync()

            if hasattr(self, 'sync_label'):
                self.sync_label.setText("Синхр: выкл")
                self.sync_label.setStyleSheet("color: #757575; padding: 0 8px;")
            # Удаляем токен из keyring
            try:
                import keyring
                keyring.delete_password("DiscoHack", "yandex_token")
            except Exception as e:
                print(f"Ошибка удаления из keyring: {e}")

            # Удаляем файл с токеном
            token_file = Path.home() / '.core-disko' / 'yandex.token'
            if token_file.exists():
                token_file.unlink()

            # Сбрасываем провайдер
            if cloud_provider:
                if hasattr(cloud_provider, '_bridge'):
                    cloud_provider._bridge.provider = None

            # Обновляем UI
            self._update_auth_status()
            self.side_bar.refresh_tree()

            # Если сейчас в облаке, переключаемся на локальные диски
            if self._current_provider == cloud_provider:
                local_provider = self._providers.get('local')
                if local_provider:
                    self._current_provider = local_provider
                    self._current_path = local_provider.get_root_path()
                    self._load_directory(self._current_path)
                    self.address_bar.set_path(self._current_path)

            self.status_bar.showMessage("Выход выполнен")
            QMessageBox.information(self, "Успех", "Выход выполнен")