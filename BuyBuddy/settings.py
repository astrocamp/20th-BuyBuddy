from pathlib import Path
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "13.215.172.147",
    "ec2-13-215-172-147.ap-southeast-1.compute.amazonaws.com",
    "buybuddy.site",
    "www.buybuddy.site",
    os.getenv("HOSTNAME"),
    "cce894edfc1c.ngrok-free.app"
]

CSRF_TRUSTED_ORIGINS = [
    "http://13.215.172.147/",
    "http://ec2-13-215-172-147.ap-southeast-1.compute.amazonaws.com/",
    "http://buybuddy.site/",
    "http://www.buybuddy.site/",
    f"http://{os.getenv('HOSTNAME')}",
]

# Application definition

INSTALLED_APPS = [
    "storages",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "pages",
    "users",
    "groups",
    "status",
    "notifications",
    "sales",
    "products",
    "anymail",
    "orders",
    "django_fsm",
    "tinymce",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    'widget_tweaks',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "BuyBuddy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "notifications.context_processors.navbar_notifications",
            ],
        },
    },
]

WSGI_APPLICATION = "BuyBuddy.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PG_DB_NAME"),
        "USER": os.environ.get("PG_USER"),
        "PASSWORD": os.environ.get("PG_PASSWORD"),
        "HOST": os.environ.get("PG_HOST", "localhost"),
        "PORT": os.environ.get("PG_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_USER_MODEL = "users.User"

# 開發階段先把密碼的各種驗證都關掉
# 開發階段僅保留最小長度驗證
if DEBUG:
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 8,
            },
        },
    ]
else:
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "zh-hant"

TIME_ZONE = "Asia/Taipei"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/assets/"
STATICFILES_DIRS = [
    BASE_DIR / "public",
    BASE_DIR / "src",
]
STATIC_ROOT = BASE_DIR / "staticfiles"  # 部署時用


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/users/sessions/new/"

SESSION_COOKIE_AGE = 60 * 60 * 24 * 3

HOSTNAME = os.getenv("HOSTNAME")

# 開發階段
if DEBUG:
    SITE_URL = "http://127.0.0.1:8000"
    SITE_NAME = "buybuddy (dev)"

    # Session  Cookie 設定
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"

# 正式環境階段
else:
    # TODO 正式上線要改網域
    SITE_URL = "http://buybuddy.site/"
    SITE_NAME = "buybuddy"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"


# 開發階段：在 terminal 顯示郵件內容
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# DEFAULT_FROM_EMAIL = 'noreply@yoursite.com'


# 真實發信
# Anymail 設定
ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.environ.get("MAILGUN_SENDER_DOMAIN"),
}
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

# AWS & S3 setting
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=604800",
}

MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_CHANNEL_SECRET_KEY = os.getenv("LINE_CHANNEL_SECRET_KEY")
LINE_SIGNATURE_REQUEST_URI = os.getenv("LINE_SIGNATURE_REQUEST_URI")
LINE_SANDBOX_URL = os.getenv("LINE_SANDBOX_URL")


# 富文本設定
TINYMCE_JS_URL = STATIC_URL + "tinymce/tinymce.min.js"
TINYMCE_DEFAULT_CONFIG = {
    "height": 300,
    "menubar": False,
    "plugins": "advlist,autolink,lists,link,image,charmap,preview,searchreplace,visualblocks,fullscreen,insertdatetime,media,table,code,help,wordcount",
    "toolbar": "undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | link image",
    "images_upload_url": "/groups/upload/",
    "csrf_cookie_name": "csrftoken",
    "csrf_token_header": "X-CSRFToken",
    "statusbar": False,
    "resize": False,
}
TINYMCE_LIMITED_CONFIG = {
    "height": 300,
    "menubar": False,
    "plugins": "advlist,autolink,lists,link,charmap,preview,searchreplace,visualblocks,fullscreen,insertdatetime,media,table,code,help,wordcount",
    "toolbar": "undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | link",
    "paste_data_images": False,
    "images_upload_url": "",
    "csrf_cookie_name": "csrftoken",
    "csrf_token_header": "X-CSRFToken",
    "statusbar": False,
    "resize": False,
}

# 第三方登入 - Django Allauth 設定
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

SOCIALACCOUNT_ADAPTER = "users.adapters.CustomSocialAccountAdapter"

# settings.py 末尾
SITE_ID = 1

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"

# settings.py
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

LINE_CHANNEL_ID = os.getenv("LINE_CHANNEL_ID")
LINE_CHANNEL_SECRET_KEY = os.getenv("LINE_CHANNEL_SECRET_KEY")
LINE_PRIVATE_KEY = os.getenv("LINE_PRIVATE_KEY")
LINE_KID = os.getenv("LINE_KID")
