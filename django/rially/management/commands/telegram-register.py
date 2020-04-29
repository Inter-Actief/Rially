import json

from django.core.management.base import BaseCommand

from rially.models import Team, TeamTelegramSession


class Command(BaseCommand):
    help = 'Checks an entered telegram token and adds it to a team when correct.'

    def add_arguments(self, parser):
        parser.add_argument('--chatid', dest='chat_id', required=True, help='The chat ID of Telegram',)
        parser.add_argument('--token', dest='token', required=True, help='The token/password the user entered')

    def handle(self, *args, **options):
        has_token = Team.objects.filter(telegram_token=options['token'])
        if has_token.count() == 1:
            session = TeamTelegramSession.objects.filter()
            p, created = TeamTelegramSession.objects.get_or_create(telegram_chat_id=options['chat_id'], team=has_token.first())
            if p is not None:
                return json.dumps({'result': True, 'team': p.team.name})
            else:
                return json.dumps({'result': False})
        else:
            return json.dumps({'result': False})
