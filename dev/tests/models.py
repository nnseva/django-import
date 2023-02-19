from django.conf import settings
from django.db import models


try:
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    from django.utils.translation import gettext_lazy as _


class ImportExample(models.Model):
    """ Import Example """

    name = models.CharField(
        max_length=128,
        verbose_name=_('Name'),
    )
    quantity = models.IntegerField(
        null=True, blank=True,
        verbose_name=_('Quantity'),
    )
    weight = models.FloatField(
        null=True, blank=True,
        verbose_name=_('Weight'),
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Price'),
    )
    kind = models.CharField(
        max_length=32,
        choices=[
            ('wood', _('Wood')),
            ('steel', _('Steel')),
            ('oil', _('Oil')),
        ],
        verbose_name=_('Kind'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='examples',
        null=True, blank=True,
        verbose_name=_('User'),
        help_text=_('User who regards to this example'),
    )

    def _set_user_name(self, value):
        self.user = self._meta.get_field('user').related_model.objects.filter(username=value).first()

    user_name = property(
        lambda self: self.user.username if self.user else None,
        _set_user_name
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Import Example')
        verbose_name_plural = _('Import Examples')
