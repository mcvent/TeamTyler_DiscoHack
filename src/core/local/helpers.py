# helpers.py
from datetime import datetime
import os

def format_size(size):
    """Форматирование размера файла"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def get_file_info(item):
    """Получение информации о файле/директории"""
    try:
        stat_info = item.stat()
        return {
            'is_dir': item.is_dir(),
            'size': stat_info.st_size,
            'modified': datetime.fromtimestamp(stat_info.st_mtime),
            'permission_error': False
        }
    except PermissionError:
        return {
            'is_dir': False,
            'size': 0,
            'modified': None,
            'permission_error': True
        }

def clear_screen():
    """Очистка экрана"""
    os.system('clear' if os.name == 'posix' else 'cls')