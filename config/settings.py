import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables desde el archivo .env en local
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-zn*-cdk3_ydbkxfx!=if*io7&=utwnh#lxj0bngskd^4c=@tu9'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

# Application definition
INSTALLED_APPS = [
    "unfold",  # Panel moderno para el administrador
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",  # Conexión S3 con Supabase Storage
    "catalogo",  # Tu app del catálogo
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Archivos estáticos en producción
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database (PostgreSQL en Supabase vía DATABASE_URL, con fallback local)
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (Supabase Storage S3 si están las llaves en .env, o carpeta local)
SUPABASE_S3_ACCESS_KEY_ID = os.environ.get('SUPABASE_S3_ACCESS_KEY_ID')
SUPABASE_S3_SECRET_ACCESS_KEY = os.environ.get('SUPABASE_S3_SECRET_ACCESS_KEY')

if SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": SUPABASE_S3_ACCESS_KEY_ID,
                "secret_key": SUPABASE_S3_SECRET_ACCESS_KEY,
                "bucket_name": "dsclub-media",
                "endpoint_url": os.environ.get(
                    "SUPABASE_S3_ENDPOINT_URL",
                    "https://mpyifntswkwowpxppiam.storage.supabase.co/storage/v1/s3",
                ),
                "region_name": "us-west-2",
                "addressing_style": "path",
                "default_acl": None,
                "querystring_auth": False,
                "custom_domain": "mpyifntswkwowpxppiam.supabase.co/storage/v1/object/public/dsclub-media",
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = "https://mpyifntswkwowpxppiam.supabase.co/storage/v1/object/public/dsclub-media/"
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Personalización del panel administrativo (Django Unfold)
UNFOLD = {
    "SITE_TITLE": "DSCLUB Admin",
    "SITE_HEADER": "DSCLUB | Gestión de Stock",
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'