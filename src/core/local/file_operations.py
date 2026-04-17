# file_operations.py
import subprocess
from pathlib import Path


class FileOperations:
    @staticmethod
    def open_file(file_path):
        """Открыть файл программой по умолчанию"""
        if not file_path.exists():
            raise Exception(f"Файл '{file_path.name}' не существует")

        if file_path.is_dir():
            raise Exception(f"'{file_path.name}' является папкой, а не файлом")

        try:
            subprocess.run(['xdg-open', str(file_path)], check=True)
        except FileNotFoundError:
            raise Exception("xdg-open не найден. Установите: sudo apt install xdg-utils")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка при открытии файла: {e}")