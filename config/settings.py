"""
Settings router - определяет какой конфиг использовать
"""
import os

from dotenv import load_dotenv

load_dotenv()

environment = os.getenv('DJANGO_ENV')

if environment == 'production':
    from .settings.production import *
elif environment == 'development':
    from .settings.development import *
else:
    from .settings.development import *
