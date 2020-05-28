from django.conf import settings


DJANGO_IMPORT = {
    'storage': {
        'class': 'django.core.files.storage.FileSystemStorage',
        'settings': {
            'location': '',
        },
        'upload_to': 'uploads',
    },
    'models': [],
    'except': [
        'contenttypes.ContentType',
        'admin.LogEntry',
        'auth.Permission',
        'sessions.Session',
        'django_import.ImportJob',
        'django_import.ImportLog',
    ],
    'sync': True,
    'rows_report': 1000,
}


def get_options():
    """
    Returns options from the settings.DJANGO_IMPORT,
    or default values
    """
    options = {}
    options.update(DJANGO_IMPORT)
    options.update(getattr(settings, 'DJANGO_IMPORT', {}))
    return options
