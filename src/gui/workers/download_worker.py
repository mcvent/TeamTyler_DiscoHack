"""Воркер для скачивания файлов в фоне."""
from PyQt6.QtCore import QThread, pyqtSignal
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from api.common.base_provider import BaseCloudProvider


class DownloadWorker(QThread):
    """Фоновое скачивание файла."""

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, provider: BaseCloudProvider, remote_path: str,
                 local_path: str):
        super().__init__()
        self.provider = provider
        self.remote_path = remote_path
        self.local_path = local_path

    def run(self) -> None:
        """Выполнение скачивания."""
        try:
            def progress_callback(current: int, total: int):
                self.progress.emit(current, total)

            success = self.provider.download_file(
                self.remote_path,
                self.local_path,
                progress_callback
            )
            self.finished.emit(success, self.local_path)
        except Exception as e:
            self.error.emit(str(e))