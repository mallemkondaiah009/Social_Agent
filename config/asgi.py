import os
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

load_dotenv()

# 1. Set the settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. Initialize the ASGI application
django_application = get_asgi_application()

# 3. Import the handler ONLY after get_asgi_application() has run
# This ensures Django's apps (including staticfiles) are loaded
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

# 4. Wrap it
application = ASGIStaticFilesHandler(django_application)