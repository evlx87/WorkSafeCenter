"""
Development settings
"""
from .base import *

DEBUG = True

# Разрешаем доступ к статике в режиме разработки
if DEBUG:
    import mimetypes
    mimetypes.add_type("application/javascript", ".js", True)

# Дополнительные настройки для разработки
INTERNAL_IPS = [
    '127.0.0.1',
]
