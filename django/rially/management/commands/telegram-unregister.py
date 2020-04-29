import json

from django.core.management.base import BaseCommand

from rially.models import Team, TeamTelegramSession


class Command(BaseCommand):
    help = 'Removes registration of chatid if it exists.'

    def add_arguments(self, parser):
        parser.add_argument('--chatid', dest='chat_id', required=True, help='The chat ID of Telegram')

    def handle(self, *args, **options):
        session = TeamTelegramSession.objects.filter(telegram_chat_id=options['chat_id'])
        if session is not None and session.count() > 0:
            session.delete()
            return json.dumps({'result': True})
        else:
            return json.dumps({'result': False, 'reason': 'Chat ID is not known yet'})
