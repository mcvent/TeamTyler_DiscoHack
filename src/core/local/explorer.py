# local/explorer.py
from .navigation import Navigator
from .file_operations import FileOperations
from .commands import CommandHandler
from .helpers import clear_screen
from .config import DEFAULT_START_PATH
from .cloud_bridge import CloudBridge
from pathlib import Path


class ConsoleExplorer:
    def __init__(self):
        self.navigator = Navigator(DEFAULT_START_PATH)
        self.file_ops = FileOperations()

        # ✅ СНАЧАЛА создаём cloud_bridge
        cloud_path = Path.home() / 'YandexDisk'
        cloud_path.mkdir(parents=True, exist_ok=True)
        self.cloud_bridge = CloudBridge(cloud_path)

        # ✅ ПОТОМ передаём его в CommandHandler
        self.command_handler = CommandHandler(self.navigator, self.file_ops, self.cloud_bridge)

    def run(self):
        """Основной цикл программы"""
        clear_screen()
        print("=" * 60)
        print("КОНСОЛЬНЫЙ ПРОВОДНИК ДЛЯ UBUNTU")
        print("=" * 60)
        print(self.command_handler._help())

        while self.command_handler.running:
            try:
                print(f"\nТекущая директория: {self.navigator.get_current_path()}")
                user_input = input("> ").strip()

                if not user_input:
                    continue

                parts = user_input.split(maxsplit=1)
                command = parts[0]
                args = parts[1] if len(parts) > 1 else ""

                result = self.command_handler.execute(command, args)
                if result:
                    print(result)

            except KeyboardInterrupt:
                print("\n\nПрограмма прервана пользователем")
                break
            except Exception as e:
                print(f"Непредвиденная ошибка: {e}")