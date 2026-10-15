"""
Production: debug off, strict hosts and CORS, secure cookies.

Every secret is required. If one is missing or still a placeholder, the app
refuses to start with a clear error instead of running with an insecure default.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *

PLACEHOLDER_VALUES = {"", "change-me"}


def require_env(name):
    """Return an environment variable, or stop startup if it's missing or a placeholder."""
    value = os.getenv(name, "").strip()
    if value in PLACEHOLDER_VALUES:
        raise ImproperlyConfigured(
            f"{name} must be set to a real value in production (see backend/.env.example)."
        )
    return value


def env_list(name):
    """A required, comma-separated environment variable as a list."""
    return [item.strip() for item in require_env(name).split(",") if item.strip()]


DEBUG = False

SECRET_KEY = require_env("SECRET_KEY")
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

DATABASES["default"]["PASSWORD"] = require_env("MYSQL_PASSWORD")

# Only the real frontend may call the API from a browser, e.g. https://stock.example.com
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")

# HTTPS: cookies are only sent over encrypted connections
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"

# HSTS makes browsers refuse plain HTTP for this domain. Start at 0 and raise it
# (e.g. to 31536000, one year) only once HTTPS is confirmed working: it can't be undone quickly.
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
