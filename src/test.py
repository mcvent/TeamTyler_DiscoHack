# test.py
import sys
import os
from loguru import logger

# Добавляем путь, чтобы импорты 'api...' работали
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.manager import CloudManager
from api.providers.yadisk.provider import YandexDiskProvider


def check_everything():
    # --- ВСТАВЬ СВОЙ ТОКЕН ТУТ ---
    TOKEN = "y0__xD67pCGCBjblgMg9offjhcw0rjt7wdIgBXBCnpIhqeelKCIfmh0ewDTHw"
    # -----------------------------

    manager = CloudManager()
    yandex = YandexDiskProvider(token=TOKEN)

    try:
        # Используем В ТОЧНОСТИ те имена, что в файле manager.py выше
        manager.register_provider("yandex", yandex)
        logger.info("Провайдер зарегистрирован")

        cloud = manager.get_provider("yandex")
        logger.info("Пытаемся получить список файлов...")

        files = cloud.list_files("/")

        logger.success(f"Успех! Найдено объектов: {len(files)}")
        for f in files:
            pref = "[DIR]" if f.is_dir else "[FILE]"
            print(f"{pref} {f.name}")

    except Exception as e:
        logger.error(f"Ошибка: {e}")


if __name__ == "__main__":
    check_everything()