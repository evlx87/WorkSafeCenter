import os
from dotenv import load_dotenv
load_dotenv()

environment = os.getenv('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
else:
    from .development import *