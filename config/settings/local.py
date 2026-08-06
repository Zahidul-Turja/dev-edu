import os
import environ
from pathlib import Path
from datetime import timedelta

env = environ.Env(DEBUG=(bool, False))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env.read_env(os.path.join(BASE_DIR, ".env"))

ENVIRONMENT = env.get_value("ENVIRONMENT", cast=str, default="development")

SECRET_KEY = env.get_value(var="SECRET_KEY", cast=str)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.get_value(var="DEBUG", cast=bool)

ALLOWED_HOSTS = env.get_value("ALLOWED_HOSTS").split(",")

# CORS and CSRF
CORS_ALLOWED_ORIGINS = env.get_value("CORS_ALLOWED_ORIGINS").split(",")
CSRF_TRUSTED_ORIGINS = env.get_value("CSRF_TRUSTED_ORIGINS").split(",")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_celery_beat",
    "user_management",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.get_value("DB_NAME", cast=str),
        "USER": env.get_value("DB_USER", cast=str),
        "PASSWORD": env.get_value("DB_PASSWORD", cast=str),
        "HOST": env.get_value("DB_HOST", cast=str, default="db"),
        "PORT": env.get_value("DB_PORT", cast=str, default="5432"),
        "OPTIONS": {
            "sslmode": "prefer",
        },
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", env.get_value("REDIS_PORT", cast=str, default="6379"))],
        },
    },
}


AUTH_USER_MODEL = "user_management.User"

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    # TODO: password proper check
    # {
    #     "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    # },
    # {
    #     "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    # },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # "rest_framework.permissions.AllowAny",
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "otp_request": "5/hour",
        "otp_verify": "10/hour",
        "login": "20/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 16,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_CHARSET": "utf-8",
    "UNICODE_JSON": True,
    # "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        days=env.get_value("ACCESS_LIFE_TIME_DAYS", cast=int, default=7)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.get_value("REFRESH_LIFE_TIME_DAYS", cast=int, default=10)
    ),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_ACCESS_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "BLACKLIST_AFTER_ROTATION": True,
}


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Dhaka"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static/"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "static_root")


MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

OTP_EXPIRY_SECONDS = env.get_value("OTP_EXPIRY_SECONDS", cast=int, default=120)
OTP_MAX_ATTEMPTS = env.get_value("OTP_MAX_ATTEMPTS", cast=int, default=5)
OTP_RESEND_COOLDOWN_SECONDS = env.get_value(
    "OTP_RESEND_COOLDOWN_SECONDS", cast=int, default=180
)


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.get_value("EMAIL_HOST", cast=str, default="smtp.gmail.com")
EMAIL_PORT = env.get_value("EMAIL_PORT", cast=str, default=587)
EMAIL_USE_TLS = env.get_value("EMAIL_USE_TLS", cast=str).lower() == "true"
EMAIL_HOST_USER = env.get_value("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env.get_value("EMAIL_HOST_PASSWORD")


REDIS_URL = env.get_value("REDIS_URL", cast=str, default="redis://redis:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
