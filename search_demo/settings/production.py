"""
settings/production.py
───────────────────────
Production settings for Railway.
All secrets come from Railway environment variables — nothing hardcoded.
"""
from .base import *
import os

SECRET_KEY = os.environ['SECRET_KEY']

DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Railway injects DATABASE_URL automatically when you add a Postgres plugin
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        env='DATABASE_URL',
        conn_max_age=600,
        ssl_require=True,
    )
}

# Trust Railway's proxy so HTTPS is detected correctly
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT      = True
SESSION_COOKIE_SECURE    = True
CSRF_COOKIE_SECURE       = True