from django.contrib import admin
from django.contrib.admin import ModelAdmin

from .models import ImportExample


@admin.register(ImportExample)
class ImportExampleAdmin(ModelAdmin):
    list_display = ["name", "quantity", "weight", "price", "kind", "user"]
