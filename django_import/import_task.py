import tablib

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
    try:
        log.info(_('Starting import %s'), job.upload_file)
        format_parameters = job.options.get('parameters', {})
        format = format_parameters.get('format', None)
        read_headers = format_parameters.get('headers', True)
        mode = job.options.get('mode', 'rb')
        headers = job.options.get('headers', None)
        reflections = job.options.get('reflections', {})
        identity = job.options.get('identity', [])
        # TODO: file encoding? data encoding? leave as-is a while ...
        if not mode in ['rb', 'rt']:
            log.warning(_('Mode should be either rb (read binary), or rt (read text), got %s, ignored'), mode)
            mode = 'rb'

        if not format:
            log.info(_('Format is not set, autodetecting: %s'), job.upload_file)
            with job.upload_file.open(mode) as f:
                format = tablib.detect_format(f)
            if not format:
                log.info(_('Format is not autodetected, trying in another mode: %s'), job.upload_file)
                job = type(job).objects.get(id=job.id)
                mode = {'rb':'rt', 'rt':'rb'}[mode]
                with job.upload_file.open(mode) as f:
                    format = tablib.detect_format(f)
            if not format:
                log.info(_('Format is not autodetected, trying as is: %s'), job.upload_file)
            else:
                log.info(_('Format is autodetected: %s'), format)
        with job.upload_file.open(mode) as f:
            params = {}
            if format:
                params['format'] = format
            params.update(**format_parameters)
            dataset = tablib.import_set(f, **format_parameters)
        log.info(
            _('Import file has been recognized, %s columns, %s rows: %s'),
            dataset.width, dataset.height, job.upload_file
        )
        if dataset.headers:
            log.info(_('Headers found: %s'), ', '.join(dataset.headers))
        if headers:
            dataset.headers = headers
        if not dataset.headers:
            dataset.headers = ['%04d' % (i+1) for i in range(dataset.width)]
            log.info(_('Headers not found, replacing by sequential numbers: %s'), ', '.join(dataset.headers))
        model = job.model.model_class()
        convertors = {}
        reflector = Reflector()
        for f in model._meta.get_fields():
            reflection = reflections.get(f.name, 'direct')
            if isinstance(reflection, str):
                reflection = {
                    'function': reflection
                }
            reflection_function = getattr(reflect, 'reflection_%' % reflection['function'], None)
            if not reflection_function:
                log.warning(_('Reflection function %s has not been registered, ignored'), reflection['function'])
                continue
            convertors[f.name] = {
                'function': reflection_function,
                'parameters': reflection.get('parameters', {})
            }
        cnt = 0
        skipped = 0
        for ind, data in enumerate(dataset.dict):
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
                        instance, created = model.objects.update_or_create(**ident, defaults=create)
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
    except tablib.InvalidDatasetType as ex:
        log.error(_("You’re trying to add something that doesn’t quite look right: %s"), ex)
    except tablib.InvalidDimensions as ex:
        log.error(_("You’re trying to add something that doesn’t quite fit right: %s"), ex)
    except tablib.UnsupportedFormat as ex:
        log.error(_("You’re trying to add something that doesn’t quite taste right: %s"), ex)
    except Exception as ex:
        log.error(_("You’re trying to add something that doesn’t work right: %s"), ex)
    except Exception as ex:
        log.error(_('Unexpected error: %s'), ex)
    log.finish()
