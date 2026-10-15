"""Settings for the test suite: the shared settings, minus the slow or noisy parts."""

from .base import *

# At least 32 characters: JWTs are signed with this key
SECRET_KEY = "test-only-insecure-key-for-signing-jwts-in-tests"
ALLOWED_HOSTS = ["testserver", "localhost"]
CORS_ALLOW_ALL_ORIGINS = True

# Fast, insecure hashing is fine for throwaway test users
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Keep test output readable: no per-request logging
MIDDLEWARE = [m for m in MIDDLEWARE if m != "management.middleware.RequestLoggingMiddleware"]
LOGGING = {"version": 1, "disable_existing_loggers": False}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
