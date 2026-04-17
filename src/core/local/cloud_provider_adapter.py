"""Адаптер CloudBridge -> BaseCloudProvider."""
from typing import List, Optional
from pathlib import Path

from api.common.base_provider import BaseCloudProvider
from api.common.models import CloudFile


class CloudProviderAdapter(BaseCloudProvider):
    """Адаптер для CloudBridge, реализующий интерфейс BaseCloudProvider."""

    def __init__(self, cloud_bridge):
        self._bridge = cloud_bridge

    def login(self, token: str) -> bool:
        self._bridge.save_token(token)
        return self._bridge.has_token()

    def list_files(self, path: str = "/") -> List[CloudFile]:
        if not self._bridge.has_token():
            return []

        # Сохраняем текущий путь
        old_path = self._bridge.current_path

        # Нормализуем путь
        clean_path = path
        if clean_path == "" or clean_path == "/":
            clean_path = "/"

        self._bridge.current_path = clean_path
        items = self._bridge.list_directory()
        self._bridge.current_path = old_path

        result = []
        for item in items:
            if item['name'].startswith('⚠️') or item['name'].startswith('Ошибка'):
                continue

            result.append(CloudFile(
                name=item['name'],
                path=item['path'],
                is_dir=item['is_dir'],
                size=0 if item['is_dir'] else self._parse_size(item['size']),
                modified_at=None,
                mime_type=None,
                file_id=item['path']
            ))

        return result

    def _parse_size(self, size_str: str) -> int:
        """Парсинг размера."""
        if not size_str:
            return 0
        try:
            parts = size_str.split()
            if len(parts) != 2:
                return 0
            value = float(parts[0])
            unit = parts[1].upper()
            multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
            return int(value * multipliers.get(unit, 1))
        except (ValueError, IndexError):
            return 0

    def upload_file(self, local_path: str, remote_path: str,
                    progress_callback=None) -> bool:
        return self._bridge.upload_file(Path(local_path), remote_path)

    def download_file(self, remote_path: str, local_path: str,
                      progress_callback=None) -> bool:
        return self._bridge.download_file(remote_path, Path(local_path))

    def delete_file(self, remote_path: str) -> bool:
        filename = Path(remote_path).name
        parent = str(Path(remote_path).parent)

        old_path = self._bridge.current_path
        self._bridge.current_path = parent if parent != '.' else '/'
        result = self._bridge.delete_file(filename)
        self._bridge.current_path = old_path
        return result

    def move_file(self, src: str, dst: str) -> bool:
        return False  # Не реализовано

    def create_folder(self, remote_path: str) -> bool:
        folder_name = Path(remote_path).name
        parent = str(Path(remote_path).parent)

        old_path = self._bridge.current_path
        self._bridge.current_path = parent if parent != '.' else '/'
        result = self._bridge.create_folder(folder_name)
        self._bridge.current_path = old_path
        return result

    def get_public_link(self, remote_path: str) -> Optional[str]:
        return None

    def delete_public_link(self, remote_path: str) -> bool:
        return False

    def get_thumbnail(self, remote_path: str, size: str = "S") -> Optional[bytes]:
        return None

    # ============ Методы для UI ============

    def get_provider_name(self) -> str:
        if self._bridge.has_token():
            return "☁️ Яндекс.Диск"
        return "☁️ Яндекс.Диск (не подключен)"

    def get_root_path(self) -> str:
        return "/"

    def get_parent_path(self, path: str) -> Optional[str]:
        """Получить родительский путь для облака."""
        if path in ["", "/"]:
            return None

        # Убираем начальный и конечный слеши
        clean_path = path.strip('/')

        if not clean_path:
            return "/"

        parts = clean_path.split('/')
        if len(parts) == 1:
            return "/"  # Для /DiscoHack_App возвращаем "/"

        # Для /Folder/Subfolder возвращаем /Folder
        parent = '/'.join(parts[:-1])
        return f"/{parent}"

    def has_token(self) -> bool:
        return self._bridge.has_token()

    def setup_token(self, token: str) -> bool:
        self._bridge.save_token(token)
        return self._bridge.has_token()

    def open_file(self, path: str) -> bool:
        """Открыть файл из облака."""
        filename = Path(path).name
        parent = str(Path(path).parent)

        old_path = self._bridge.current_path
        self._bridge.current_path = parent if parent != '.' else '/'
        result = self._bridge.open_file(filename)
        self._bridge.current_path = old_path
        return result

    def is_directory(self, path: str) -> bool:
        """Проверить, является ли путь директорией."""
        if path == "/":
            return True

        old_path = self._bridge.current_path
        self._bridge.current_path = path

        try:
            # Пробуем получить список - если получилось, значит директория
            self._bridge.list_directory()
            result = True
        except Exception:
            result = False

        self._bridge.current_path = old_path
        return result