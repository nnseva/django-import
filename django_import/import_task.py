import pandas

from six import string_types
from functools import partial

from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db import DatabaseError

from . import reflections as reflect
from .reflector import Reflector


def run_import(import_log_id=None):
    """
    Evaluates importing process just after the ImportJob instance has been saved.

    It may be evaluated synchronously in the context of the WEB Application,
    or asynchronously in the context of the Celery Worker,
    depending on `async` option of the `DJANGO_IMPORT` variable in the settings file.
    """
    from django_import.models import ImportLog

    log = ImportLog.objects.filter(id=import_log_id).last()
    if not log:
        return

    job = log.job
    log.info(_('Trying to import %s'), job.upload_file)

    try:
        try_import(log)
    except Exception as ex:
        log.error(_('Unexpected error: %s'), ex)
    log.finish()


def try_import(log):
    job = log.job
    format_parameters = job.options.get('parameters', {})
    format = job.options.get('format', 'csv')
    mode = job.options.get('mode', 'rb')
    headers = job.options.get('headers', None)
    reflections = job.options.get('reflections', {})
    identity = job.options.get('identity', [])
    # TODO: file encoding? data encoding? leave as-is a while ...
    if mode not in ['rb', 'rt']:
        log.warning(_('Mode should be either rb (read binary), or rt (read text), got %s, ignored'), mode)
        mode = 'rb'

    read_function = getattr(pandas, 'read_%s' % format, None)
    if not read_function:
        log.warning(_('Read function not found, finished: read_%s'), format)

    params = {}
    params.update(**format_parameters)

    job.upload_file.open(mode)
    try:
        dataset = read_function(job.upload_file, **format_parameters)
    except Exception:
        job.upload_file.close()
        raise
    job.upload_file.close()
    log.info(
        _('Import file has been recognized, %s columns, %s rows: %s'),
        len(dataset.columns), len(dataset.index), job.upload_file
    )
    if headers:
        dataset = dataset.rename(columns=dict(zip([a for a in dataset.columns], headers)))
    if isinstance(dataset.columns, pandas.core.indexes.numeric.Int64Index):
        dataset = dataset.rename(columns=dict(zip([a for a in dataset.columns], ['%04d' % (a + 1) for a in dataset.columns])))
        log.info(_('Headers not found, replacing by sequential numbers: %s'), ', '.join(dataset.columns))
    model = job.model.model_class()
    convertors = {}
    reflector = Reflector()
    for f in model._meta.get_fields():
        reflection = reflections.get(f.name, 'direct')
        if isinstance(reflection, string_types):
            reflection = {
                'function': reflection
            }
        if not isinstance(reflection, dict):
            log.warning(_("The reflection is not formatted properly: %s"), reflection)
            continue
        reflection_function = getattr(reflect, 'reflection_%s' % reflection['function'], None)
        if not reflection_function:
            log.warning(_('Reflection function %s has not been registered, ignored'), reflection['function'])
            continue
        convertors[f.name] = {
            'function': reflection_function,
            'parameters': reflection.get('parameters', {})
        }
    cnt = 0
    skipped = 0
    for ind, data in [(row[0], dict(zip(dataset.columns, row[1]))) for row in dataset.iterrows()]:
        create, update = {}, {}
        try:
            for field_name in convertors:
                f = partial(convertors[field_name]['function'], **convertors[field_name]['parameters'])
                c, u = f(reflector, model, field_name, data, log)
                create.update(c)
                update.update(u)
        except Exception as ex:
            log.warning(_("Error while importing data: %s"), ex)
            continue
        if not create and not update:
            if not cnt and skipped >= 2:
                log.warning(_("%s rows at the top have no reflected data, import interrupted"), skipped + 1)
                break
            else:
                log.warning(_("No any reflected data found, row skipped: %s"), ', '.join(['%s:%r' % (k, v) for k, v in data.items()]))
                skipped += 1
                continue
        try:
            with transaction.atomic():
                ident = dict([(k, v) for k, v in create.items() if k in identity])
                if ident:
                    instance, created = model.objects.update_or_create(defaults=create, **ident)
                else:
                    instance = model.objects.create(**create)
                if update:
                    for k in update:
                        setattr(instance, k, update[k])
                    instance.save()
        except DatabaseError as ex:
            log.error(_("Database error while importing data: create %r, update %r, %s"), create, update, ex)
            continue
        cnt += 1
    log.info(_('Import has been processed, %s rows successfully imported'), cnt)
