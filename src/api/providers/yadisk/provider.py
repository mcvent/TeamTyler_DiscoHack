import time
from typing import List, Optional, Dict
from loguru import logger
from .client import YandexDiskClient
from ...common.base_provider import BaseCloudProvider
from ...common.models import CloudFile


class YandexDiskProvider(BaseCloudProvider):
    """Реализация провайдера с кешированием метаданных."""

    def __init__(self, token: str = None):
        self.client = YandexDiskClient(token)
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 30

    def login(self, token: str) -> bool:
        self.client.api.token = token
        try:
            is_valid = self.client.api.check_token()
            if is_valid:
                logger.info("Успешный вход в Яндекс.Диск")
            return is_valid
        except Exception:
            return False

    def list_files(self, path: str = "/") -> List[CloudFile]:
        now = time.time()
        if path in self._cache:
            ts, data = self._cache[path]
            if now - ts < self._cache_ttl:
                return data

        resources = self.client.list_dir(path)
        result = [
            CloudFile(
                name=res.name,
                path=res.path.replace("disk:", ""),
                is_dir=res.type == "dir",
                size=res.size or 0,
                modified_at=res.modified,
                mime_type=res.mime_type,
                file_id=res.resource_id
            ) for res in resources
        ]

        self._cache[path] = (now, result)
        return result

    def upload_file(self, local_path: str, remote_path: str, progress_callback=None) -> bool:
        logger.info(f"Загрузка файла: {local_path} -> {remote_path}")
        self.client.upload(local_path, remote_path, callback=progress_callback)
        return True

    def download_file(self, remote_path: str, local_path: str, progress_callback=None) -> bool:
        logger.info(f"Скачивание файла: {remote_path} -> {local_path}")
        self.client.download(remote_path, local_path, callback=progress_callback)
        return True

    def delete_file(self, remote_path: str) -> bool:
        self.client.delete(remote_path)
        return True

    def move_file(self, src: str, dst: str) -> bool:
        self.client.move(src, dst)
        return True

    def create_folder(self, remote_path: str) -> bool:
        self.client.mkdir(remote_path)
        return True

    def get_public_link(self, remote_path: str) -> Optional[str]:
        return self.client.publish(remote_path)

    def delete_public_link(self, remote_path: str) -> bool:
        self.client.unpublish(remote_path)
        return True

    def get_thumbnail(self, remote_path: str, size: str = "S") -> Optional[bytes]:
        return self.client.get_preview(remote_path, size)