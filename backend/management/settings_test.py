"""Settings for the test suite: same as the app, minus the slow or noisy parts."""
from .settings import *  # noqa: F401,F403

# Fast, insecure hashing is fine for throwaway test users
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Keep test output readable: no per-request logging
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'management.middleware.RequestLoggingMiddleware']  # noqa: F405
LOGGING = {'version': 1, 'disable_existing_loggers': False}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
