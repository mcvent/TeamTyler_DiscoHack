from .config import COMMANDS
from pathlib import Path


class CommandHandler:
    def __init__(self, navigator, file_ops, cloud_bridge=None):
        self.navigator = navigator
        self.file_ops = file_ops
        self.running = True
        self.cloud_bridge = cloud_bridge
        self.cloud_mode = False

    def execute(self, command, args):
        cmd = command.lower()
        if cmd in COMMANDS['ls']:
            return self._ls(args)
        elif cmd in COMMANDS['cd']:
            return self._cd(args)
        elif cmd in COMMANDS['pwd']:
            return self._pwd()
        elif cmd in COMMANDS['openfile']:
            return self._open_file(args)
        elif cmd in COMMANDS['mkdir']:
            return self._mkdir(args)
        elif cmd in COMMANDS['touch']:
            return self._touch(args)
        elif cmd in COMMANDS['rm']:
            return self._rm(args)
        elif cmd in COMMANDS['upload']:
            return self._upload_file(args)
        elif cmd in COMMANDS['get']:
            return self._cloud_download(args)
        elif cmd in COMMANDS['token_setup']:
            return self._token_setup()
        elif cmd in COMMANDS['downloads']:
            return self._show_downloads()
        elif cmd in COMMANDS['clear_downloads']:
            return self._clear_downloads(args)
        elif cmd in COMMANDS['help']:
            return self._help()
        elif cmd in COMMANDS['exit']:
            return self._exit()
        else:
            return f"Unknown command: {command}"



    def _cloud_download(self, filename: str) -> str:
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "Облако не подключено"
        if not filename:
            return "Укажите имя файла"
        remote_path = self.cloud_bridge.get_current_path().rstrip('/') + '/' + filename
        if self.cloud_bridge.download_file(remote_path):
            return f"Файл '{filename}' скачан"
        return f"Не удалось скачать '{filename}'"

    def _token_setup(self) -> str:
        if not self.cloud_bridge:
            return "Ошибка: облачный мост не инициализирован"
        print("\nНАСТРОЙКА ТОКЕНА YANDEX DISK")
        print("=" * 50)
        print("Введите токен Яндекс Диска:")
        print("=" * 50)
        import getpass
        token = getpass.getpass("Токен: ")
        if token:
            self.cloud_bridge.save_token(token)
            self.cloud_mode = True
            return "Токен сохранен! Облачный режим включен"
        return "Токен не введен"

    def _upload_file(self, args: str) -> str:
        """Загрузить файл в облако"""
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "Облако не подключено"

        if not args:
            return "Использование: upload <локальный_файл> [облачный_путь]"

        parts = args.split(maxsplit=1)
        local_path_str = parts[0]

        local_path = Path(local_path_str)
        if not local_path.is_absolute():
            current_local = self.navigator.get_current_path()
            local_path = current_local / local_path_str

        local_path = local_path.resolve()

        if not local_path.exists():
            return f"Файл '{local_path_str}' не существует\nПроверьте: ls | grep {local_path_str}"

        if local_path.is_dir():
            return f"'{local_path.name}' является папкой"

        remote_path = parts[1] if len(parts) > 1 else None

        if self.cloud_bridge.upload_file(local_path, remote_path):
            return f"Файл '{local_path.name}' загружен в облако"
        return f"Ошибка загрузки"

    def _show_downloads(self) -> str:
        """Показать скачанные файлы"""
        if not self.cloud_bridge:
            return "Облако не подключено"
        return self.cloud_bridge.show_downloads()

    def _clear_downloads(self, args: str) -> str:
        """Очистить папку Downloads"""
        if not self.cloud_bridge:
            return "Облако не подключено"

        days = None
        if args and args.strip().isdigit():
            days = int(args.strip())

        return self.cloud_bridge.clear_downloads(days)

    def _cd(self, path: str) -> str:
        """Перейти в папку (локально или в облаке)"""
        if not path:
            return "Usage: cd <path>"

        if self.cloud_mode and self.cloud_bridge and self.cloud_bridge.has_token():
            # Облачный режим
            if path == '..' or path == '/':
                if self.cloud_bridge.change_directory(path):
                    return f"Changed to: {self.cloud_bridge.get_current_path()}"
            else:
                if self.cloud_bridge.change_directory(path):
                    return f"Changed to: {self.cloud_bridge.get_current_path()}"
            return f"Folder '{path}' not found in cloud"
        else:
            # Локальный режим
            try:
                self.navigator.change_directory(path)
                return f"Changed to: {self.navigator.get_current_path()}"
            except Exception as e:
                return f"Error: {e}"

    def _pwd(self) -> str:
        """Показать текущий путь (локальный или облачный)"""
        if self.cloud_mode and self.cloud_bridge and self.cloud_bridge.has_token():
            return f" Cloud: {self.cloud_bridge.get_current_path()}"
        else:
            return f" Local: {self.navigator.get_current_path()}"

    def _ls(self, args: str = "") -> str:
        """Показать содержимое (локально или в облаке)"""
        if self.cloud_mode and self.cloud_bridge and self.cloud_bridge.has_token():
            # Облачный режим
            items = self.cloud_bridge.list_directory()
            if not items or (len(items) == 1 and 'Токен не настроен' in items[0]['name']):
                return "Cloud folder is empty or not connected"

            result = f"\nCLOUD: {self.cloud_bridge.get_current_path()}\n"
            result += "-" * 60 + "\n"
            for item in items:
                icon = "📁" if item['is_dir'] else "📄"
                cloud_icon = "☁️" if not item.get('downloaded', False) else "✓"
                result += f"{icon} {cloud_icon}{item['name']:<30} {item['size']}\n"
            result += "-" * 60
            return result
        else:
            # Локальный режим
            try:
                items = self.navigator.list_directory()
                result = f"\n LOCAL: {self.navigator.get_current_path()}\n"
                result += "-" * 60 + "\n"
                result += f"{'TYPE':<8} {'NAME':<30} {'SIZE':<12}\n"
                result += "-" * 60 + "\n"
                for item in items:
                    name = item['name'][:28] if len(item['name']) > 28 else item['name']
                    result += f"{item['type']:<8} {name:<30} {item['size']:<12}\n"
                result += "-" * 60 + f"\nTotal: {len(items)}"
                return result
            except Exception as e:
                return f"Error: {e}"

    def _open_file(self, filename: str) -> str:
        """Открыть файл (локально или из облака)"""
        if not filename:
            return "Usage: openfile <filename>"

        if self.cloud_mode and self.cloud_bridge and self.cloud_bridge.has_token():
            # Облачный режим
            if self.cloud_bridge.open_file(filename):
                return f"File '{filename}' opened from cloud"
            return f"Failed to open '{filename}' from cloud"
        else:
            # Локальный режим
            try:
                file_path = self.navigator.get_current_path() / filename.strip()
                self.file_ops.open_file(file_path)
                return f"File '{filename}' opened locally"
            except Exception as e:
                return f"Error: {e}"

    def _mkdir(self, args: str) -> str:
        """Создать папку (локально + в облаке если подключено)"""
        if not args:
            return "Usage: mkdir <folder_name>"

        folder_name = args.strip()
        current_path = self.navigator.get_current_path()
        new_path = current_path / folder_name

        # 1. Создаём локально
        try:
            new_path.mkdir()
            result = f"Folder '{folder_name}' created locally"
        except FileExistsError:
            return f"Folder '{folder_name}' already exists"
        except Exception as e:
            return f"Error creating folder locally: {e}"

        # 2. Если облако подключено - создаём и там
        if self.cloud_bridge and self.cloud_bridge.has_token():
            if self.cloud_bridge.create_folder(folder_name):
                result += " + in cloud"
            else:
                result += " (cloud sync failed)"

        return result

    def _touch(self, args: str) -> str:
        """Создать файл (локально + в облаке если подключено)"""
        if not args:
            return "Usage: touch <filename>"

        filename = args.strip()
        current_path = self.navigator.get_current_path()
        new_path = current_path / filename

        # 1. Создаём локально
        try:
            new_path.touch()
            result = f"File '{filename}' created locally"
        except Exception as e:
            return f"Error creating file locally: {e}"

        # 2. Если облако подключено - создаём и там
        if self.cloud_bridge and self.cloud_bridge.has_token():
            remote_path = self.cloud_bridge.get_current_path().rstrip('/') + '/' + filename
            if self.cloud_bridge.upload_file(new_path, remote_path):
                result += " + in cloud"
            else:
                result += " (cloud sync failed)"

        return result

    def _rm(self, args: str) -> str:
        """Удалить файл/папку (локально + из облака если подключено)"""
        if not args:
            return "Usage: rm <name>"

        name = args.strip()
        current_path = self.navigator.get_current_path()
        target_path = current_path / name

        if not target_path.exists():
            return f"'{name}' does not exist"

        print(f"Are you sure you want to delete '{name}'? (y/N)")
        confirm = input().lower()
        if confirm != 'y':
            return "Deletion cancelled"

        result = []

        # 1. Удаляем локально
        try:
            if target_path.is_dir():
                import shutil
                shutil.rmtree(target_path)
                result.append(f"Folder '{name}' deleted locally")
            else:
                target_path.unlink()
                result.append(f"File '{name}' deleted locally")
        except Exception as e:
            return f"Error deleting locally: {e}"

        # 2. Если облако подключено - удаляем и там
        if self.cloud_bridge and self.cloud_bridge.has_token():
            if self.cloud_bridge.delete_file(name):
                result.append("deleted from cloud")
            else:
                result.append("cloud delete failed")

        return " + ".join(result)

    # ============ СИСТЕМНЫЕ КОМАНДЫ ============

    def _help(self):
        return

    def _exit(self):
        self.running = False
        return
