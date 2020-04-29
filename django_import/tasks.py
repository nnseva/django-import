from celery import shared_task
from .import_task import run_import

run_import = shared_task(run_import, track_started=True)
