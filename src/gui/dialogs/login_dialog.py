"""Диалог входа в Яндекс.Диск."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QWidget, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class OAuthWorker(QThread):
    """Фоновый поток для OAuth авторизации."""

    finished = pyqtSignal(str)  # token или пустая строка при ошибке
    error = pyqtSignal(str)

    def __init__(self, client_id: str, client_secret: str):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret

    def run(self) -> None:
        """Запуск OAuth процесса."""
        try:
            from api.providers.yadisk.auth import get_token_via_oauth
            token = get_token_via_oauth(self.client_id, self.client_secret)
            if token:
                self.finished.emit(token)
            else:
                self.error.emit("Не удалось получить токен")
        except Exception as e:
            self.error.emit(str(e))


class LoginDialog(QDialog):
    """Диалог входа в Яндекс.Диск."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._token: str | None = None
        self._worker: OAuthWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Настройка UI."""
        self.setWindowTitle("Вход в Яндекс.Диск")

        self.setFixedSize(600, 200)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        title = QLabel("Подключение к Яндекс.Диску")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)


        # Прогресс-бар
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #757575;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Кнопки
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.login_btn = QPushButton("Войти")
        self.login_btn.clicked.connect(self._start_login)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addWidget(button_widget)

    def _start_login(self) -> None:
        """Запуск процесса входа."""
        # Меняем размер окна на время ожидания (уменьшаем)
        self.setFixedSize(600, 250)

        self.login_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setText("Ожидание авторизации в браузере...")

        # ID приложения Яндекс
        CLIENT_ID = "2600deefcdbd4986b124f735c17e4c62"
        CLIENT_SECRET = "c9f3a79ed4234bde9107dacc3f815c58"

        self._worker = OAuthWorker(CLIENT_ID, CLIENT_SECRET)
        self._worker.finished.connect(self._on_login_success)
        self._worker.error.connect(self._on_login_error)
        self._worker.start()

    def _on_login_success(self, token: str) -> None:
        """Успешный вход."""
        # Возвращаем исходный размер окна
        self.setFixedSize(600, 200)
        self._token = token
        self.accept()

    def _on_login_error(self, error: str) -> None:
        """Ошибка входа."""
        # Возвращаем исходный размер окна
        self.setFixedSize(600, 200)
        self.progress.setVisible(False)
        self.status_label.setText(f"Ошибка: {error}")
        self.status_label.setStyleSheet("color: #d32f2f;")
        self.login_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)

    def get_token(self) -> str | None:
        """Получить токен после успешного входа."""
        return self._token