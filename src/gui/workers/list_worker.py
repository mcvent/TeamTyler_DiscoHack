"""Воркер для получения списка файлов в фоне."""
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from api.common.base_provider import BaseCloudProvider
from api.common.models import CloudFile
from api.common.exceptions import CloudError


class ListDirectoryWorker(QThread):
    """Фоновое получение содержимого директории."""

    finished = pyqtSignal(list)  # List[CloudFile]
    error = pyqtSignal(str)

    def __init__(self, provider: BaseCloudProvider, path: str):
        super().__init__()
        self.provider = provider
        self.path = path

    def run(self) -> None:
        """Выполнение операции в фоне."""
        try:
            items = self.provider.list_files(self.path)
            self.finished.emit(items)
        except CloudError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Неизвестная ошибка: {e}")