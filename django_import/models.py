from django.db import models
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string
from django.contrib.contenttypes.models import ContentType
import re

from jsoneditor.fields.django_extensions_jsonfield import JSONField

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


def get_file_storage_class():
    """
    Function returning a class as a file storage class.
    """
    options = get_options()
    return import_string(options['storage']['class'])


class Storage(LazyObject):
    """
    Lazy storage instance class
    to setup additional parameters from settings
    """
    def _setup(self):
        options = get_options()
        options = options['storage']['settings']
        storage_class = get_file_storage_class()
        self._wrapped = storage_class(**options)


class ImportJob(models.Model):
    """
Every time the ImportJob instance is saved, the importing process
is called, synchronously, or asynchronously, depending on the
`async` value of the `DJANGO_IMPORT` variable in the settings
file.

The `options` attribute has the complex structure to setup
various custom import options.

- `format` is a format to be imported. It selects one of pandas module functions to be
    used for import. Available values can be got from the pandas documentation as a list of `read_*`
    functions, like `table`, `csv`, `fwf`, `excel`, `json`, or any other reading function returning
    a `DataFrame`, read [pandas documentation](https://pandas.pydata.org/docs/reference/io.html)

- `parameters` section determines parameters to be sent as additional
    parameters to the reading function. Check [pandas documentation](https://pandas.pydata.org/docs/reference/io.html)
    to see what additional parameters may or should be sent there

- the `mode` determines file open mode when the file is got from the storage;
    the only two, `rb` (read binary) and `rt` (read text) modes are supported;
    *note* that some custom storages don't support proper mode changing options

- the `headers` determines a list of headers which should be assigned to
    data columns. Existent heades if present, are replaced. Length of the
    `headers` list should be equal to number of data columns

+ `identity` is a list of field column names which are used to determine identity
    of the database instance. It is used by the system in the call to
    [`update_or_create()`](https://docs.djangoproject.com/en/2.2/ref/models/querysets/#update-or-create) method

+ `reflections` determines customization in translation data to
    field values.
    """

    model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='imports',
        verbose_name=_("Model"),
        help_text=_("Specify a model to be imported"),
    )
    options = JSONField(
        blank=True,
        default=dict,
        verbose_name=_('Options'),
        help_text=_('Detailed instructions for import if necessary'),
    )
    upload_file = models.FileField(
        upload_to=get_options()['storage']['upload_to'], storage=Storage(),
        verbose_name=_('Upload File'),
    )

    def __str__(self):
        return '%(upload_file)s->%(model)s' % {
            'upload_file': self.upload_file,
            'model': self.model
        }

    class Meta:
        verbose_name = _('Import Job')
        verbose_name_plural = _('Import Jobs')

    def save(self, *av, **kw):
        super(ImportJob, self).save(*av, **kw)
        log = ImportLog.objects.create(job=self)
        log.info(_('Starting import for: %s'), self.upload_file)
        sync = get_options().get('sync', True)
        if not sync:
            from .tasks import run_import
            run_import.delay(log.id)
        else:
            from .import_task import run_import
            run_import(log.id)


class ImportLog(models.Model):
    job = models.ForeignKey(
        ImportJob, on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('Job'),
        help_text=_('Job to which the log is related'),
    )
    imported_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Imported At'),
        help_text=_('Timestamp when the import happens'),
    )
    import_log = models.TextField(
        editable=False,
        default='',
        verbose_name=_('Import Log'),
        help_text=_("Detailed log of the importing process"),
    )
    is_finished = models.BooleanField(
        editable=False,
        default=False,
        verbose_name=_('Is Finished'),
    )

    def import_log_html(self):
        return mark_safe(re.sub("\n", "<br/>", self.import_log))
    import_log_html.allow_tags = True
    import_log_html.short_description = _("Detailed Import Log")

    class Meta:
        verbose_name = _('Import Log')
        verbose_name_plural = _('Import Logs')

    def __str__(self):
        return '%(imported_at)s: %(job)s' % {
            'imported_at': self.imported_at,
            'job': self.job
        }

    def message(self, level, chapter, format, *av, **kw):
        now = timezone.now()
        values = av if av else kw
        try:
            message = '%s: [%s(%s)] %s' % (now, chapter, level, (format % values))
        except Exception as ex:
            try:
                r = '%r' % values
            except Exception:
                r = '<something strange>'
            try:
                f = '%r' % format
            except Exception:
                f = '<something strange>'
            self.error('Error formatting %s using %s: %s', r, f, ex)
        self.import_log += '\n%s' % message
        self.save()

    def debug(self, format, *av, **kw):
        return self.message(5, 'DEBUG', format, *av, **kw)

    def info(self, format, *av, **kw):
        return self.message(4, 'INFO', format, *av, **kw)

    def warning(self, format, *av, **kw):
        return self.message(3, 'WARNING', format, *av, **kw)

    def error(self, format, *av, **kw):
        return self.message(2, 'ERROR', format, *av, **kw)

    def critical(self, format, *av, **kw):
        return self.message(1, 'CRITICAL', format, *av, **kw)

    def finish(self):
        self.is_finished = True
        self.info(_('Finished'))
