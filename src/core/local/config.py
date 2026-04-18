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


    # 'cloud_ls': ['cls', 'cloud_ls'],
    # 'cloud_cd': ['ccd', 'cloud_cd'],
    # 'cloud_pwd': ['cpwd', 'cloud_pwd'],
    # 'cloud_open': ['copen', 'cloud_open'],
    # 'cloud_mkdir': ['cmkdir', 'cmd'],
    # 'cloud_touch': ['ctouch', 'ct'],
    # 'cloud_rm': ['crm', 'crm'],

    # Системные
    'help': ['help', 'h', '?'],
    'exit': ['exit', 'quit', 'q'],
}