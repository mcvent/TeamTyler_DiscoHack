from abc import ABC, abstractmethod
from typing import List, Optional
from .models import CloudFile

class BaseCloudProvider(ABC):

    @abstractmethod
    def login(self, token: str) -> bool:
        pass

    @abstractmethod
    def list_files(self, path: str = "/") -> List[CloudFile]:
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str, progress_callback=None) -> bool:
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str, progress_callback=None) -> bool:
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        pass

    @abstractmethod
    def move_file(self, src: str, dst: str) -> bool:
        pass

    @abstractmethod
    def create_folder(self, remote_path: str) -> bool:
        pass

    @abstractmethod
    def get_public_link(self, remote_path: str) -> Optional[str]:
        pass

    @abstractmethod
    def delete_public_link(self, remote_path: str) -> bool:
        pass

    @abstractmethod
    def get_thumbnail(self, remote_path: str, size: str = "S") -> Optional[bytes]:
        pass

    @abstractmethod
    def move_file(self, src: str, dst: str) -> bool:
        pass

    @abstractmethod
    def rename_file(self, old_path: str, new_path: str) -> bool:
        pass