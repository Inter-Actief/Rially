import json

from django.core.management.base import BaseCommand

from rially.models import Team, TeamTelegramSession


class Command(BaseCommand):
    help = 'Checks if a user is registered and in which team.'

    def add_arguments(self, parser):
        parser.add_argument('--chatid', dest='chat_id', required=True, help='The chat ID of Telegram',)

    def handle(self, *args, **options):
        session = TeamTelegramSession.objects.filter(telegram_chat_id=options['chat_id'])
        if session.count() == 1:
            return json.dumps({'in_team': True, 'team': session.first().team.name})
        else:
            return json.dumps({'in_team': False})
