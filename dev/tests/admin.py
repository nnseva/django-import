from datetime import datetime
from django import forms
from django.db import models
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.contenttypes.models import ContentType
from django.forms import ChoiceField

from .models import ImportExample


@admin.register(ImportExample)
class ImportExampleAdmin(ModelAdmin):
    list_display = ["name", "quantity", "weight", "price", "kind", "user"]
