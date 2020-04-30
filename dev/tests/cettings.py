from .settings import *  # noqa

import os
from .settings import BASE_DIR

DJANGO_IMPORT = {
    'storage': {
        'class': 'django.core.files.storage.FileSystemStorage',
        'settings': {
            'location': os.path.dirname(BASE_DIR),
        },
        'upload_to': 'uploads',
    },
    'models': [],
    'except': [
        'contenttypes.ContentType',
        'admin.LogEntry',
        'auth.Permission',
        'sessions.Session',
    ],
    'sync': False,
}
