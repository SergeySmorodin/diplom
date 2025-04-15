from dotenv import load_dotenv
import os
from django.core.exceptions import ImproperlyConfigured


load_dotenv()

def get_env_variable(var_name):
    try:
        return os.getenv(var_name)
    except KeyError:
        error_msg = f"Установите переменную окружения {var_name}"
        raise ImproperlyConfigured(error_msg)

# Настройки подключения к базе данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_variable('DB_NAME'),
        'USER': get_env_variable('DB_USER'),
        'PASSWORD': get_env_variable('DB_PASSWORD'),
        'HOST': get_env_variable('DB_HOST'),
        'PORT': get_env_variable('DB_PORT'),
    }
}

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

