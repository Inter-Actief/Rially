import json

from django.core.management.base import BaseCommand

from rially.models import SiteState

from django.conf import settings

class Command(BaseCommand):
    help = 'Returns wether the submissions are open or not.'

    def handle(self, *args, **options):
        return json.dumps({"state": SiteState.objects.all().first().submission_open})
