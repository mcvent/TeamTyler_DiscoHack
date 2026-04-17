# main.py
import sys
from local.explorer import ConsoleExplorer

def main():
    """Точка входа в программу"""
    try:
        explorer = ConsoleExplorer()
        explorer.run()
    except Exception as e:
        print(f"Критическая ошибка при запуске: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())