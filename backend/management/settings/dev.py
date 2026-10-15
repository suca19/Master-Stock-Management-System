"""Local development: debug on, permissive CORS, emails printed to the console."""

from .base import *

DEBUG = True

# A fallback is fine here: this key never protects real data
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-only-key-never-use-this-in-production")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# The React dev build runs on another port, so allow any origin locally
CORS_ALLOW_ALL_ORIGINS = True

# Print emails in the backend logs instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
