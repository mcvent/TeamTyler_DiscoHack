# local/cloud_bridge.py
"""
Мост между консольным проводником и облачным API
Обеспечивает работу с облаком как с обычной папкой
"""

import sys
import subprocess
from pathlib import Path

# Добавляем путь к api модулю
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.manager import CloudManager
from api.providers.yadisk.provider import YandexDiskProvider
from api.common.exceptions import CloudAuthError, CloudNotFoundError


class CloudBridge:
    """Мост для работы с облачным диском как с обычной папкой"""

    def __init__(self, local_path: Path):
        """
        Args:
            local_path: Локальная папка, где будут кэшироваться файлы (например, /home/user/YandexDisk)
        """
        self.local_path = local_path
        self.manager = CloudManager()
        self.provider = None
        self.current_path = "/"  # Текущий путь в облаке
        self._init_provider()

    def _init_provider(self):
        """Инициализация провайдера Яндекс Диска"""
        # Регистрируем провайдера
        self.manager.register_provider("yandex", YandexDiskProvider)

        # Пытаемся получить токен из файла
        token = self._load_token()

        if token:
            try:
                provider = YandexDiskProvider()
                if provider.login(token):
                    self.provider = provider
                    print("✅ Яндекс Диск подключен")
                else:
                    print("❌ Не удалось подключиться к Яндекс Диску")
            except Exception as e:
                print(f"❌ Ошибка подключения: {e}")
        else:
            print("⚠️ Токен не найден. Выполните: token_setup")

    def _load_token(self) -> str:
        """Загрузить токен из файла"""
        token_file = Path.home() / '.core-disko' / 'yandex.token'
        if token_file.exists():
            return token_file.read_text().strip()
        return None

    def save_token(self, token: str):
        """Сохранить токен"""
        token_file = Path.home() / '.core-disko' / 'yandex.token'
        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(token.strip())
        token_file.chmod(0o600)  # Только владелец может читать

        # Переподключаем провайдера
        self._init_provider()

    def has_token(self) -> bool:
        """Проверить наличие токена и подключения"""
        return self.provider is not None

    def _format_size(self, size: int) -> str:
        """Форматирование размера"""
        if size == 0:
            return ""

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def list_directory(self, path: str = None) -> list:
        """
        Получить содержимое облачной папки (без скачивания файлов)

        Returns:
            Список словарей с ключами: name, type, size, is_dir, downloaded, path
        """
        if not self.provider:
            return [{
                'name': '⚠️ Токен не настроен. Выполните: token_setup',
                'type': '[???]',
                'size': '',
                'is_dir': False,
                'downloaded': False,
                'path': ''
            }]

        target_path = path if path else self.current_path

        try:
            files = self.provider.list_files(target_path)

            result = []
            for f in files:
                # Проверяем, скачан ли файл локально
                local_file = self.local_path / f.path.lstrip('/')

                result.append({
                    'name': f.name,
                    'type': '[DIR]' if f.is_dir else '[FILE]',
                    'size': self._format_size(f.size) if not f.is_dir else '',
                    'is_dir': f.is_dir,
                    'downloaded': local_file.exists() if not f.is_dir else False,
                    'path': f.path
                })

            # Сортировка: папки первые
            result.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return result

        except CloudNotFoundError:
            return [{
                'name': 'Папка не найдена',
                'type': '[???]',
                'size': '',
                'is_dir': False,
                'downloaded': False,
                'path': ''
            }]
        except Exception as e:
            return [{
                'name': f'Ошибка: {e}',
                'type': '[???]',
                'size': '',
                'is_dir': False,
                'downloaded': False,
                'path': ''
            }]

    def change_directory(self, path: str) -> bool:
        """
        Переход в другую облачную папку

        Args:
            path: Путь для перехода (/, .., Documents, /Documents/Subfolder)

        Returns:
            True если успешно, False если ошибка
        """
        if not self.provider:
            return False

        # Переход в корень
        if path == '/' or path == '':
            self.current_path = '/'
            return True

        # Переход на уровень выше
        if path == '..':
            if self.current_path == '/':
                return True
            # Поднимаемся на уровень выше
            parts = self.current_path.rstrip('/').split('/')
            if len(parts) <= 2:
                self.current_path = '/'
            else:
                self.current_path = '/' + '/'.join(parts[:-1])
            return True

        # Переход в подпапку
        # Нормализуем путь
        if path.startswith('/'):
            new_path = path
        else:
            new_path = self.current_path.rstrip('/') + '/' + path.lstrip('/')

        new_path = new_path.replace('//', '/')

        # Проверяем, что папка существует
        try:
            files = self.provider.list_files(new_path)
            # Если успешно получили список - папка существует
            self.current_path = new_path
            return True
        except CloudNotFoundError:
            return False
        except Exception:
            return False

    def get_current_path(self) -> str:
        """Вернуть текущий путь в облаке"""
        return self.current_path if self.current_path != '/' else '/'

    def download_file(self, remote_path: str, local_path: Path = None) -> bool:
        """
        Скачать файл из облака

        Args:
            remote_path: Путь к файлу в облаке
            local_path: Локальный путь для сохранения (опционально)

        Returns:
            True если успешно, False если ошибка
        """
        if not self.provider:
            print("❌ Облако не подключено")
            return False

        if local_path is None:
            local_path = self.local_path / remote_path.lstrip('/')

        # Создаём родительские папки
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Если файл уже есть, не скачиваем
        if local_path.exists():
            print(f"✅ Файл уже скачан: {local_path}")
            return True

        try:
            print(f"📥 Скачивание {remote_path}...")
            self.provider.download_file(remote_path, str(local_path))
            print(f"✅ Скачано: {local_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка скачивания: {e}")
            return False

    def open_file(self, filename: str) -> bool:
        """
        Открыть файл из облака (скачать если нужно)

        Args:
            filename: Имя файла в текущей облачной папке

        Returns:
            True если успешно, False если ошибка
        """
        if not self.provider:
            print("❌ Облако не подключено")
            return False

        # Полный путь в облаке
        remote_path = self.current_path.rstrip('/') + '/' + filename.lstrip('/')
        remote_path = remote_path.replace('//', '/')

        # Локальный путь
        local_file = self.local_path / remote_path.lstrip('/')

        # Скачиваем если нет
        if not local_file.exists():
            if not self.download_file(remote_path, local_file):
                return False

        # Открываем файл
        try:
            subprocess.run(['xdg-open', str(local_file)], check=True)
            return True
        except FileNotFoundError:
            print("❌ xdg-open не найден. Установите: sudo apt install xdg-utils")
            return False
        except Exception as e:
            print(f"❌ Не удалось открыть {filename}: {e}")
            return False

    def upload_file(self, local_path: Path, remote_path: str = None) -> bool:
        """
        Загрузить файл в облако
        """
        if not self.provider:
            print("❌ Облако не подключено")
            return False

        if remote_path is None:
            remote_path = self.current_path.rstrip('/') + '/' + local_path.name

        try:
            print(f"📤 Загрузка {local_path} -> {remote_path}...")
            self.provider.upload_file(str(local_path), remote_path)
            print("✅ Загружено")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False

    def create_folder(self, folder_name: str) -> bool:
        """
        Создать папку в облаке

        Args:
            folder_name: Имя новой папки

        Returns:
            True если успешно
        """
        if not self.provider:
            print("❌ Облако не подключено")
            return False

        remote_path = self.current_path.rstrip('/') + '/' + folder_name.lstrip('/')
        remote_path = remote_path.replace('//', '/')

        try:
            self.provider.create_folder(remote_path)
            print(f"✅ Папка '{folder_name}' создана")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания папки: {e}")
            return False

    def delete_file(self, filename: str) -> bool:
        """
        Удалить файл/папку в облаке

        Args:
            filename: Имя файла/папки в текущей облачной папке

        Returns:
            True если успешно
        """
        if not self.provider:
            print("❌ Облако не подключено")
            return False

        remote_path = self.current_path.rstrip('/') + '/' + filename.lstrip('/')
        remote_path = remote_path.replace('//', '/')

        # Удаляем локальный кэш если есть
        local_file = self.local_path / remote_path.lstrip('/')
        if local_file.exists():
            if local_file.is_dir():
                import shutil
                shutil.rmtree(local_file)
            else:
                local_file.unlink()

        try:
            self.provider.delete_file(remote_path)
            print(f"✅ '{filename}' удалён")
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления: {e}")
            return False
