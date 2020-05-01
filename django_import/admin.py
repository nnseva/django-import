from django.apps import apps
from django.utils.safestring import mark_safe
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.contrib import admin
from django.contrib.admin import ModelAdmin, StackedInline
from django.contrib.contenttypes.models import ContentType

import markdown

from .models import ImportJob, ImportLog, get_options


class ImportLogInline(StackedInline):
    readonly_fields = [
        'imported_at',
        'is_finished',
        'import_log_html',
    ]
    model = ImportLog
    extra = 0

    def has_add_permission(request, *av, **kw):
        return False


@admin.register(ImportJob)
class ImportJobAdmin(ModelAdmin):
    fields = [
        "model",
        "options",
        "upload_file",
        "extra_help"
    ]
    readonly_fields = [
        "extra_help"
    ]
    list_display = ["id", "model", "upload_file"]

    inlines = [
        ImportLogInline
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'model':
            queryset = ContentType.objects.all().annotate(full_name=Concat(F('app_label'), Value('.'), F('model')))
            options = get_options()
            if not options.get('models', []):
                models = ['%s.%s' % (m._meta.app_label, m._meta.model_name) for m in apps.get_models()]
                queryset = queryset.filter(
                    full_name__in=models
                ).exclude(
                    full_name__in=[x.lower() for x in options.get('except', [])]
                )
            else:
                queryset = queryset.filter(full_name__in=[m.lower() for m in options.get('models', [])])
            kwargs['queryset'] = queryset.order_by('model')
        return super(ImportJobAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def extra_help(self, *av, **kw):
        try:
            from . import reflections
            help = '# Options\n%s\n# Reflections\n%s\n# Actual reflections list\n' % (ImportJob.__doc__, reflections.__doc__)
            for r in reflections.__dict__:
                func = getattr(reflections, r, None)
                if func and callable(func) and func.__name__.startswith('reflection_'):
                    help += '\n### %s\n%s' % (func.__name__.split('_', 1)[1], func.__doc__)
            help = markdown.markdown(help, extensions=['extra', 'smarty', 'sane_lists', 'attr_list'], output='html5')
            help = help.replace('<ul>', '<ul style="margin-left:20px;">').replace('<li>', '<li style="list-style-type: square;">')
        except Exception as ex:
            help = str(ex)
        return mark_safe(help)
