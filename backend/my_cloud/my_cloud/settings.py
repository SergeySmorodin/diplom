import os
from pathlib import Path
from config.general_config import DATABASES, SECRET_KEY, DEBUG, ALLOWED_HOSTS
from config.my_cloud_config import BASE_DIR, MEDIA_URL, MEDIA_ROOT
from config.logging_config import LOGGING


AUTH_USER_MODEL = 'users.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'mptt',

    'cloud_app.apps.CloudAppConfig',
    'users.apps.UsersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_cloud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'my_cloud.wsgi.application'

CORS_ALLOW_CREDENTIALS = False
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

#STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Куда собирать файлы при `collectstatic`

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'my_cloud.utils.custom_exception_handler',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}


SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Хранение сессий в БД
SESSION_COOKIE_HTTPONLY = True  # Защита от XSS (JavaScript не может прочитать куки)
SESSION_COOKIE_SECURE = False  # Только HTTPS (включить в production!)
SESSION_COOKIE_SAMESITE = 'Lax'  # Защита от CSRF (можно 'Strict' для большей безопасности)
SESSION_COOKIE_NAME = 'fs_sessionid'  # Уникальное имя куки
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Сессия сохраняется после закрытия браузера
SESSION_COOKIE_AGE = 1209600  # Время жизни сессии (2 недели, в секундах)

CSRF_USE_SESSIONS = False  # Хранить CSRF-токен в cookie (лучше для React)
CSRF_COOKIE_HTTPONLY = False  # React должен читать CSRF-токен
CSRF_COOKIE_SECURE = False  # Только HTTPS (в production)
CSRF_COOKIE_SAMESITE = 'Lax'  # Защита от CSRF
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'  # React будет отправлять токен в заголовке