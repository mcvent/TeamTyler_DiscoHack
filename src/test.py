import os
import sys
from api.manager import CloudManager
from api.providers.yadisk.provider import YandexDiskProvider


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def run_test():
    # --- КОНФИГУРАЦИЯ ---
    # Вставь сюда свой токен. .strip() уберет лишние пробелы и переносы
    TOKEN = "y0__xD67pCGCBjblgMg9offjhcw0rjt7wdIgBXBCnpIhqeelKCIfmh0ewDTHw".strip()

    manager = CloudManager()
    yandex = YandexDiskProvider(token=TOKEN)
    manager.register_provider("yandex", yandex)
    cloud = manager.get_provider("yandex")

    clear_screen()
    print("=" * 50)
    print("       DISCOHACK: CLOUD TEST TERMINAL")
    print("=" * 50)

    while True:
        print("\nВыберите действие:")
        print("1. Создать папку")
        print("2. Создать текстовый файл (любое расширение)")
        print("3. Показать список файлов в папке")
        print("4. Выход")

        choice = input("\nВаш выбор (1-4): ")

        try:
            if choice == "1":
                path = input("Введите путь и название папки (напр. /Disco): ").strip()
                if not path.startswith("/"): path = "/" + path

                print(f"--> Создаю папку: {path}...")
                cloud.create_folder(path)
                print("Успешно!")

            elif choice == "2":
                print("\nПодсказка: файл можно создать в корне (/) или в любой папке.")
                file_path = input(
                    "Введите полный путь с именем файла (напр. /Disco/notes.txt или /script.py): ").strip()
                if not file_path.startswith("/"): file_path = "/" + file_path

                content = input("Введите содержимое файла: ")

                print(f"--> Загружаю файл в {file_path}...")
                cloud.create_text_file(content, file_path)
                print("Файл успешно создан!")

            elif choice == "3":
                path = input("Какую папку просмотреть? (по умолчанию /): ").strip() or "/"
                if not path.startswith("/"): path = "/" + path

                print(f"\n--- Содержимое {path} ---")
                items = cloud.list_files(path)
                if not items:
                    print("Папка пуста.")
                else:
                    print(f"{'ТИП':<7} | {'ИМЯ':<25} | {'РАЗМЕР'}")
                    print("-" * 45)
                    for item in items:
                        itype = "[DIR]" if item.is_dir else "[FILE]"
                        print(f"{itype:<7} | {item.name:<25} | {item.size} байт")

            elif choice == "4":
                print("Завершение работы...")
                break

            else:
                print("Неверный ввод, попробуйте снова.")

        except Exception as e:
            print(f"\n[ОШИБКА]: {e}")
            print("Проверьте правильность пути и наличие родительских папок.")


if __name__ == "__main__":
    run_test()