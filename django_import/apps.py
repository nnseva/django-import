from __future__ import unicode_literals

from django.apps import AppConfig


try:
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    from django.utils.translation import gettext_lazy as _


class Config(AppConfig):
    verbose_name = _('Django Import')
    name = 'django_import'
