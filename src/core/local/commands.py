# commands.py
from .config import COMMANDS
from pathlib import Path


class CommandHandler:
    def __init__(self, navigator, file_ops, cloud_bridge=None):
        self.navigator = navigator
        self.file_ops = file_ops
        self.running = True
        self.cloud_bridge = cloud_bridge

    def execute(self, command, args):
        cmd = command.lower()

        if cmd in COMMANDS['ls']:
            return self._list()
        elif cmd in COMMANDS['cd']:
            return self._cd(args)
        elif cmd in COMMANDS['pwd']:
            return self._pwd()
        elif cmd in COMMANDS['openfile']:
            return self._open_file(args)
        elif cmd in COMMANDS['cloud_ls']:
            return self._cloud_ls(args)
        elif cmd in COMMANDS['cloud_cd']:
            return self._cloud_cd(args)
        elif cmd in COMMANDS['cloud_pwd']:
            return self._cloud_pwd()
        elif cmd in COMMANDS['cloud_open']:
            return self._cloud_open(args)
        elif cmd in COMMANDS['cloud_download']:
            return self._cloud_download(args)
        elif cmd in COMMANDS['token_setup']:
            return self._token_setup()
        elif cmd in COMMANDS['upload']:
            return self._upload_file(args)
        elif cmd in COMMANDS['help']:
            return self._help()
        elif cmd in COMMANDS['exit']:
            return self._exit()
        else:
            return f"Неизвестная команда: {command}"

    # ============ ЛОКАЛЬНЫЕ КОМАНДЫ ============

    def _list(self):
        try:
            items = self.navigator.list_directory()
            result = f"\nСодержимое: {self.navigator.get_current_path()}\n"
            result += "-" * 60 + "\n"
            result += f"{'ТИП':<8} {'ИМЯ':<30} {'РАЗМЕР':<12}\n"
            result += "-" * 60 + "\n"
            for item in items:
                name = item['name'][:28] if len(item['name']) > 28 else item['name']
                result += f"{item['type']:<8} {name:<30} {item['size']:<12}\n"
            result += "-" * 60 + f"\nВсего: {len(items)}"
            return result
        except Exception as e:
            return f"Ошибка: {e}"

    def _cd(self, path):
        try:
            self.navigator.change_directory(path)
            return f"Перешли в: {self.navigator.get_current_path()}"
        except Exception as e:
            return f"Ошибка: {e}"

    def _pwd(self):
        return f"Текущая директория: {self.navigator.get_current_path()}"

    def _open_file(self, filename):
        if not filename:
            return "Ошибка: Укажите имя файла"
        try:
            file_path = self.navigator.get_current_path() / filename.strip()
            self.file_ops.open_file(file_path)
            return f"Файл '{filename}' открыт"
        except Exception as e:
            return f"Ошибка: {e}"

    # ============ ОБЛАЧНЫЕ КОМАНДЫ ============

    def _cloud_ls(self, args: str) -> str:
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "❌ Облако не подключено. Выполните: token_setup"
        items = self.cloud_bridge.list_directory()
        if not items:
            return "Папка пуста"
        result = f"\n☁️ ОБЛАЧНАЯ ПАПКА: {self.cloud_bridge.get_current_path()}\n"
        result += "-" * 60 + "\n"
        for item in items:
            icon = "📁" if item['is_dir'] else "📄"
            cloud_icon = "☁️ " if not item.get('downloaded', False) else "✓ "
            result += f"{icon} {cloud_icon}{item['name']:<30} {item['size']}\n"
        result += "-" * 60
        return result

    def _cloud_cd(self, path: str) -> str:
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "❌ Облако не подключено. Выполните: token_setup"
        if not path:
            return "Укажите путь"
        if self.cloud_bridge.change_directory(path):
            return f"Перешли в: {self.cloud_bridge.get_current_path()}"
        return f"❌ Папка '{path}' не найдена"

    def _cloud_pwd(self) -> str:
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "❌ Облако не подключено"
        return f"☁️ {self.cloud_bridge.get_current_path()}"

    def _cloud_open(self, filename: str) -> str:
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "❌ Облако не подключено"
        if not filename:
            return "Укажите имя файла"
        if self.cloud_bridge.open_file(filename):
            return f"✅ Файл '{filename}' открыт"
        return f"❌ Не удалось открыть '{filename}'"

    def _cloud_download(self, filename: str) -> str:
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "❌ Облако не подключено"
        if not filename:
            return "Укажите имя файла"
        remote_path = self.cloud_bridge.get_current_path().rstrip('/') + '/' + filename
        if self.cloud_bridge.download_file(remote_path):
            return f"✅ Файл '{filename}' скачан"
        return f"❌ Не удалось скачать '{filename}'"

    def _token_setup(self) -> str:
        if not self.cloud_bridge:
            return "❌ Ошибка: облачный мост не инициализирован"
        print("\n🔐 НАСТРОЙКА ТОКЕНА YANDEX DISK")
        print("=" * 50)
        print("Введите токен Яндекс Диска:")
        print("=" * 50)
        import getpass
        token = getpass.getpass("Токен: ")
        if token:
            self.cloud_bridge.save_token(token)
            return "✅ Токен сохранен! Теперь можно использовать облачные команды"
        return "❌ Токен не введен"

    # ✅ ИСПРАВЛЕННЫЙ МЕТОД UPLOAD
    def _upload_file(self, args: str) -> str:
        """Загрузить файл в облако"""
        if not self.cloud_bridge or not self.cloud_bridge.has_token():
            return "❌ Облако не подключено"

        if not args:
            return "Использование: upload <локальный_файл> [облачный_путь]"

        parts = args.split(maxsplit=1)
        local_path_str = parts[0]

        # ✅ ПРОВЕРЯЕМ ПУТЬ ОТНОСИТЕЛЬНО ТЕКУЩЕЙ ЛОКАЛЬНОЙ ДИРЕКТОРИИ
        local_path = Path(local_path_str)
        if not local_path.is_absolute():
            current_local = self.navigator.get_current_path()
            local_path = current_local / local_path_str

        # ✅ НОРМАЛИЗУЕМ ПУТЬ
        local_path = local_path.resolve()

        if not local_path.exists():
            return f"❌ Файл '{local_path_str}' не существует\nПроверьте: ls | grep {local_path_str}"

        if local_path.is_dir():
            return f"❌ '{local_path.name}' является папкой"

        remote_path = parts[1] if len(parts) > 1 else None

        if self.cloud_bridge.upload_file(local_path, remote_path):
            return f"✅ Файл '{local_path.name}' загружен в облако"
        return f"❌ Ошибка загрузки"

    # ============ СИСТЕМНЫЕ КОМАНДЫ ============

    def _help(self):
        return """
============================================================
ДОСТУПНЫЕ КОМАНДЫ:
============================================================
ЛОКАЛЬНЫЕ:
  ls, list    - показать содержимое
  cd <путь>   - перейти в папку
  pwd         - показать текущий путь
  openfile    - открыть файл

ОБЛАЧНЫЕ:
  cls         - показать облачную папку
  ccd <путь>  - перейти в облачную папку
  cpwd        - показать облачный путь
  copen       - открыть файл из облака
  get         - скачать файл из облака
  upload      - загрузить файл в облако
  token_setup - настроить токен

СИСТЕМНЫЕ:
  help        - справка
  exit, q     - выход
============================================================
"""

    def _exit(self):
        self.running = False
        return "До свидания!"