"""
settings/local.py
──────────────────
Local development settings.
This file is in .gitignore — never committed.
Copy .env.example to .env and fill in your values.
"""
from .base import *
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-only')

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME',     'fts_demo'),
        'USER':     os.environ.get('DB_USER',     'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST':     os.environ.get('DB_HOST',     'localhost'),
        'PORT':     os.environ.get('DB_PORT',     '5432'),
    }
}