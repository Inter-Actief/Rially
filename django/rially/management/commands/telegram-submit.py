import json
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from rially.models import Team, TeamTelegramSession, Submitted, Task, Location, Picture, LocationTask, TaskSolve, \
    LocationSolve, PictureSolve, LocationTaskSolve, PriorityQueueItem, QueueItem


from django.conf import settings

class Command(BaseCommand):
    ### DEBUGGEN!!!!!
    help = 'Submit a file.'

    def add_arguments(self, parser):
        parser.add_argument('--chatid', dest='chat_id', required=True, help='The chat ID of Telegram')
        parser.add_argument('--id', dest='id', required=True, help='The solve code the user entered')
        parser.add_argument('--filename', dest='filename', required=True, help='The file name of the asset')

    def handle(self, *args, **options):
        session = TeamTelegramSession.objects.filter(telegram_chat_id=options['chat_id'])
        if session.count() == 1:
            team = session.first().team
            t = options['id'].upper().split('-')
            type = None
            type2 = ''
            done = False
            if t[0] == 'T': # Task
                if len(t) == 2:
                    type = Task.objects.filter(id=int(t[1]))
                    type2 = ContentType.objects.get_for_model(Task)
                    if type.count() > 0 and TaskSolve.objects.filter(task=type.first(), team=team).count() > 0:
                        done = True
            elif t[0] == 'L':  # Location
                if len(t) == 2:
                    type = Location.objects.filter(id=int(t[1]))
                    type2 = ContentType.objects.get_for_model(Location)
                    if type.count() > 0 and LocationSolve.objects.filter(location=type.first(), team=team).count() > 0:
                        done = True
            elif t[0] == 'PL':  # Picture
                if len(t) == 3:
                    type = Picture.objects.filter(location__id=int(t[1]), id=int(t[2]))
                    type2 = ContentType.objects.get_for_model(Picture)
                    if type.count() > 0 and PictureSolve.objects.filter(picture=type.first(), team=team).count() > 0:
                        done = True
            elif t[0] == 'TL':  # Location task
                if len(t) == 3:
                    type = LocationTask.objects.filter(location__id=int(t[1]), id=int(t[2]))
                    type2 = ContentType.objects.get_for_model(LocationTask)
                    if type.count() > 0 and LocationTaskSolve.objects.filter(task=type.first(), team=team).count() > 0:
                        done = True

            if type is None or type.count() <= 0:
                return json.dumps({'result': False, 'reason': 'ID not correct.'})
            elif done:
                return json.dumps({'result': False, 'reason': 'Already solved.'})
            else:
                if Submitted.objects.filter(team=team, object_id=type.first().id, content_type=type2).count() > 0:
                    return json.dumps({'result': False, 'reason': 'Already in queue.'})
                else:
                    submit = Submitted(type=type.first(), file=options['filename'], team=team)
                    submit.save()

                    if type2 == ContentType.objects.get_for_model(Location):
                        queue = PriorityQueueItem(submitted=submit, time_sent=timezone.now() - timedelta(seconds=settings.RATE_EXPIRATION))
                        queue.save()
                    else:
                        queue = QueueItem(submitted=submit, time_sent=timezone.now() - timedelta(seconds=settings.RATE_EXPIRATION))
                        queue.save()
                    return json.dumps({'result': True})

        else:
            return json.dumps({'result': False, 'reason': 'No valid session found.'})
