# config.py
from pathlib import Path

DEFAULT_START_PATH = Path.home()

COMMANDS = {
    # Локальные
    'ls': ['ls', 'list'],
    'cd': ['cd'],
    'pwd': ['pwd'],
    'openfile': ['openfile', 'open'],

    # Облачные
    'cloud_ls': ['cls', 'cloud_ls'],
    'cloud_cd': ['ccd', 'cloud_cd'],
    'cloud_pwd': ['cpwd', 'cloud_pwd'],
    'cloud_open': ['copen', 'cloud_open'],
    'cloud_download': ['get', 'download'],
    'token_setup': ['token_setup', 'tsetup'],
    'upload': ['upload', 'put', 'up'],  # ✅ ДОБАВИТЬ
    'downloads': ['downloads', 'dl', 'dls'],
    'clear_downloads': ['clear_dl', 'cdl', 'clean'],

    # Системные
    'help': ['help', 'h', '?'],
    'exit': ['exit', 'quit', 'q'],
}