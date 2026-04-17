"""Воркер для рекурсивного поиска файлов."""
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal

from api.common.base_provider import BaseCloudProvider
from api.common.models import CloudFile


class SearchWorker(QThread):
    """Фоновый поиск файлов."""

    finished = pyqtSignal(list)  # List[CloudFile]
    error = pyqtSignal(str)

    def __init__(self, provider: BaseCloudProvider, path: str, query: str):
        super().__init__()
        self.provider = provider
        self.path = path
        self.query = query

    def run(self) -> None:
        """Выполнение поиска."""
        try:
            if hasattr(self.provider, 'search_files'):
                results = self.provider.search_files(self.path, self.query, recursive=True)
            else:
                # Fallback: простой поиск в текущей папке
                results = self.provider.list_files(self.path)
                query_lower = self.query.lower()
                results = [f for f in results if query_lower in f.name.lower()]

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))