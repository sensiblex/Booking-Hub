from .settings import *  # noqa: F403


SECRET_KEY = SECRET_KEY or 'test-secret-key'  # noqa: F405
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/bookinghub-test.sqlite3',
    }
}

MEDIA_ROOT = '/tmp/bookinghub-test-media'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
