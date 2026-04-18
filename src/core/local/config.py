from pathlib import Path

DEFAULT_START_PATH = Path.home()

COMMANDS = {
    # Локальные
    'ls': ['ls', 'list'],
    'cd': ['cd'],
    'pwd': ['pwd'],
    'openfile': ['openfile', 'open'],
    'touch': ['touch'],
    'mkdir': ['mkdir', 'md'],
    'rm': ['rm', 'del', 'delete'],

    # Облачные
    'upload': ['upload', 'put', 'up'],
    'get': ['get', 'download'],
    'token_setup': ['token_setup', 'tsetup'],
    'downloads': ['downloads', 'dl', 'dls'],
    'clear_downloads': ['clear_dl', 'cdl', 'clean'],

    # Системные
    'help': ['help', 'h', '?'],
    'exit': ['exit', 'quit', 'q'],
}