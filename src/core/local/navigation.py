# navigation.py
import os
from pathlib import Path
from core.local.helpers import get_file_info, format_size


class Navigator:
    def __init__(self, start_path):
        self.current_path = start_path

    def get_current_path(self):
        return self.current_path

    def list_directory(self):
        """Показать содержимое текущей папки"""
        try:
            items = []
            for item in self.current_path.iterdir():
                info = get_file_info(item)

                if info['permission_error']:
                    items.append({
                        'type': '[???]',
                        'name': item.name,
                        'size': ' (нет доступа)',
                        'modified': '????????',
                        'is_dir': False
                    })
                else:
                    item_type = "[DIR]" if info['is_dir'] else "[FILE]"
                    size = "" if info['is_dir'] else f" {format_size(info['size'])}"
                    modified = info['modified'].strftime("%Y-%m-%d %H:%M:%S") if info['modified'] else "????????"

                    items.append({
                        'type': item_type,
                        'name': item.name,
                        'size': size,
                        'modified': modified,
                        'is_dir': info['is_dir']
                    })

            # Сортировка: папки первые
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return items

        except PermissionError:
            raise Exception("Нет доступа к директории")

    def change_directory(self, path):
        """Переход в другую папку"""
        if not path or path.strip() == "":
            raise Exception("Укажите путь для перехода")

        target_path = Path(path.strip())
        if not target_path.is_absolute():
            target_path = self.current_path / target_path

        target_path = target_path.resolve()

        if not target_path.exists():
            raise Exception(f"Путь '{target_path}' не существует")

        if not target_path.is_dir():
            raise Exception(f"'{target_path}' не является директорией")

        if not os.access(target_path, os.R_OK):
            raise Exception(f"Нет доступа к директории '{target_path}'")

        self.current_path = target_path