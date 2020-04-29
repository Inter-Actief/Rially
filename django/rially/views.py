import zipfile
import string
import random
import csv
import pytz
from datetime import datetime, timedelta
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.db import transaction, DatabaseError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils import timezone

from .models import *
from .settings import *

from django.contrib.auth import views as auth_views


class LocationView(generic.DetailView):
    template_name = 'location.html'
    model = Location

    def get_context_data(self, **kwargs):
        context = super(LocationView, self).get_context_data(**kwargs)
        context['locations'] = Location.objects.all()
        context['nextlocation'] = Location.objects.filter(id=(context.get('location').id + 1)).first()
        context['team'] = AuthUser.get_team(self.request)
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_team(request):
            return super(LocationView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class HomeView(generic.TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['locations'] = Location.objects.all()
        context['team'] = AuthUser.get_team(self.request)
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_team(request):
            return super(HomeView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class TasksView(generic.TemplateView):
    template_name = 'tasks.html'

    def get_context_data(self, **kwargs):
        context = super(TasksView, self).get_context_data(**kwargs)
        context['locations'] = Location.objects.all()
        context['tasks'] = Task.objects.all()
        context['team'] = AuthUser.get_team(self.request)
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_team(request):
            return super(TasksView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class BonusView(generic.TemplateView):
    template_name = 'bonus.html'

    def get_context_data(self, **kwargs):
        context = super(BonusView, self).get_context_data(**kwargs)
        context['locations'] = Location.objects.all()
        context['team'] = AuthUser.get_team(self.request)
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_team(request):
            return super(BonusView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class ScoreView(generic.TemplateView):
    template_name = 'score_error.html'

    def get_context_data(self, **kwargs):
        context = super(ScoreView, self).get_context_data(**kwargs)
        context['locations'] = Location.objects.all()
        context['teams'] = sorted(Team.objects.all(), key= lambda t: -t.points_total())
        context['team'] = AuthUser.get_team(self.request)
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_team(request):
            state = SiteState.objects.all().first()
            if state.show_scoreboard:
                self.template_name = 'score.html'
            return super(ScoreView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')

class HelpView(generic.TemplateView):
    template_name = 'help.html'

    def get(self, request, *args, **kwargs):
        return super(HelpView, self).get(request, *args, **kwargs)

class AdminPanelView(generic.TemplateView):
    template_name = 'adminpanel.html'

    def get_context_data(self, **kwargs):
        context = super(AdminPanelView, self).get_context_data(**kwargs)
        context['submissionstate'] = SiteState.objects.all().first().submission_open
        context['teams'] = Team.objects.all()
        context['showscorestate'] = SiteState.objects.all().first().show_scoreboard
        return context

    def post(self, request, *args, **kwargs):
        if 'setsubmissions' in request.POST:
            if request.POST['setsubmissions'] == 'open':
                state = SiteState.objects.all().first()
                state.submission_open = True
                state.save()
            elif request.POST['setsubmissions'] == 'close':
                state = SiteState.objects.all().first()
                state.submission_open = False
                state.save()
        if 'setshowscore' in request.POST:
            if request.POST['setshowscore'] == 'hide':
                state = SiteState.objects.all().first()
                state.show_scoreboard = False
                state.save()
            elif request.POST['setshowscore'] == 'show':
                state = SiteState.objects.all().first()
                state.show_scoreboard = True
                state.save()
        if 'addteams' in request.POST:
            teamnames = request.POST['teams'].replace('\r', '').split('\n')

            # teamcsv = open("teams.csv", "a")
            with open(os.path.join(settings.PROJECT_BASE_DIR, 'teams.csv'), 'w') as team_csv:
                writer = csv.writer(team_csv)

                for teamname in teamnames:
                    username_alloweds = string.ascii_lowercase + string.digits
                    first_words = teamname.split(" ")[:3]
                    joined = ''.join(first_words)
                    username = ''
                    for letter in joined:
                        if letter.lower() in username_alloweds:
                            username += letter.lower()
                    username = username[:12]
                    token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))
                    password = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))

                    if username == '' or User.objects.filter(username=username).count() > 0:
                        continue

                    user = User.objects.create_user(username=username, password=password)
                    user.save()

                    team = Team(name=teamname, user=user, telegram_token=token)
                    team.save()

                    writer.writerow([teamname, username, password, token])


        return super(AdminPanelView, self).get(request, *args, **kwargs)


    def get(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            return super(AdminPanelView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class AdminDownloadView(generic.TemplateView):
    template_name = 'admindownload.html'

    def get_context_data(self, **kwargs):
        context = super(AdminDownloadView, self).get_context_data(**kwargs)
        context['downloads'] = Aftermovie.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            if request.GET.get('download') == 'zip':
                filenames = ["{}/{}".format(settings.MEDIA_ROOT, v) for v in Aftermovie.objects.values_list('media', flat=True)]
                zip_subdir = "aftermovie_material"
                zip_filename = "%s.zip" % zip_subdir

                s = BytesIO()

                zf = zipfile.ZipFile(s, "w")

                for fpath in filenames:
                    fdir, fname = os.path.split(fpath)
                    zip_path = os.path.join(zip_subdir, fname)
                    zf.write(fpath, zip_path)
                zf.close()

                resp = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
                resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

                return resp
            else:
                return super(AdminDownloadView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class AdminScoreView(generic.TemplateView):
    template_name = 'adminscore.html'

    def get_context_data(self, **kwargs):
        context = super(AdminScoreView, self).get_context_data(**kwargs)
        context['locations'] = Location.objects.all()
        context['teams'] = sorted(Team.objects.all(), key= lambda t: -t.points_total())
        context['team'] = Team.objects.first()
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            return super(AdminScoreView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class AdminDistributedRateView(generic.TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'adminrate.html'

    def get_context_data(self, **kwargs):
        context = super(AdminDistributedRateView, self).get_context_data(**kwargs)

        context['queue_length'] = QueueItem.objects.count() + PriorityQueueItem.objects.count()
        context['queue_important'] = PriorityQueueItem.objects.count()
        context['queue_longest'] = Submitted.objects.order_by('received').first().received if context['queue_length'] > 0 else None
        # item = (Submitted.objects.filter(content_type=ContentType.objects.get(model='task')) | \
        #         Submitted.objects.filter(content_type=ContentType.objects.get(model='locationtask'))).order_by('received')

        queue = 'priority'
        item = PriorityQueueItem.objects.filter(time_sent__lte=timezone.now() - timedelta(seconds=settings.RATE_EXPIRATION))
        if item.count() <= 0:
            queue = 'normal'
            item = QueueItem.objects.filter(time_sent__lte=timezone.now() - timedelta(seconds=settings.RATE_EXPIRATION))
            if item.count() <= 0:
                return context

        item = item.first()

        print(item, item.time_sent)
        context['type'] = item.submitted.content_type.model
        context['subject'] = item.submitted.type
        context['team'] = item.submitted.team
        context['file'] = '/media/{}'.format(item.submitted.file)
        context['id'] = item.id
        context['queue'] = queue

        if item.submitted.content_type.model != 'location':
            context['subject_name'] = '/media/{}'.format(item.submitted.type.image)


        # We sent the submitted to someone, so we should change the sent time
        item.time_sent = timezone.now()
        item.save()
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            return super(AdminDistributedRateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')

    def post(self, request, *args, **kwargs):
        print(request.POST)
        if AuthUser.is_admin(request):
            aftermovie = 'aftermovie' in request.POST and request.POST['aftermovie'] == 'on'

            try:
                item = None
                if request.POST['queue'] == 'normal':
                    item = QueueItem.objects.get(id=int(request.POST['id']))
                elif request.POST['queue'] == 'priority':
                    item = PriorityQueueItem.objects.get(id=int(request.POST['id']))
                s = item.submitted
            except ObjectDoesNotExist:
                return super(AdminDistributedRateView, self).get(request, *args, **kwargs)
            if item.submitted.content_type == ContentType.objects.get(model='task'):
                points = abs(int(request.POST['points']))
                try:
                    with transaction.atomic():
                        ts = TaskSolve(task=s.type, points=points, team=s.team, content=s.file)
                        ts.save()
                        item.submitted.delete()
                        item.delete()
                        if aftermovie:
                            am = Aftermovie(media=s.file)
                            am.save()
                    messages.add_message(request, messages.SUCCESS,
                                         'Succesfully awarded team {} with {} points!'.format(s.team, points))
                except DatabaseError:
                    messages.add_message(request, messages.ERROR,
                                         'Oops! Something went wrong.')
            elif item.submitted.content_type == ContentType.objects.get(model='locationtask'):
                points = abs(int(request.POST['points']))
                try:
                    with transaction.atomic():
                        lts = LocationTaskSolve(task=s.type, points=points, team=s.team, content=s.file)
                        lts.save()
                        item.submitted.delete()
                        item.delete()
                        if aftermovie:
                            am = Aftermovie(media=s.file)
                            am.save()
                    messages.add_message(request, messages.SUCCESS,
                                         'Succesfully awarded team {} with {} points!'.format(s.team, points))
                except DatabaseError:
                    messages.add_message(request, messages.ERROR,
                                         'Oops! Something went wrong.')
            elif item.submitted.content_type == ContentType.objects.get(model='picture'):
                if request.POST['extra'] == 'yes':
                    try:
                        with transaction.atomic():
                            p = PictureSolve(picture=s.type, team=s.team, content=s.file)
                            p.save()
                            item.submitted.delete()
                            item.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()
                        messages.add_message(request, messages.SUCCESS,
                                             'Succesfully awarded team {} with {} points!'.format(s.team, s.type.points))
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
                else:
                    try:
                        with transaction.atomic():
                            item.submitted.delete()
                            item.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()
                        messages.add_message(request, messages.SUCCESS,
                                             'You succesfully declined the picture.')
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
            elif item.submitted.content_type == ContentType.objects.get(model='location'):
                if request.POST['extra'] == 'yes':
                    try:
                        with transaction.atomic():
                            l = LocationSolve(location=s.type, team=s.team, content=s.file)
                            l.save()
                            item.submitted.delete()
                            item.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()

                        msg = ''
                        if hasattr(s.type, 'points'):
                            msg = 'Succesfully awarded team {} with {} points!'.format(s.team, s.type.points)
                        else:
                            msg = 'Succesfully approved submission of team {}!'.format(s.team)

                        messages.add_message(request, messages.SUCCESS, msg)
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
                else:
                    try:
                        with transaction.atomic():
                            item.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()
                        messages.add_message(request, messages.SUCCESS,
                                             'You succesfully declined the location.')
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
            else:
                messages.add_message(request, messages.ERROR, 'Oops, something went wrong.')
            return super(AdminDistributedRateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')



class AdminTaskRateView(generic.TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'adminrate.html'

    def get_context_data(self, **kwargs):
        context = super(AdminTaskRateView, self).get_context_data(**kwargs)
        context['page_type'] = 'task'
        context['queue_length'] = Submitted.objects.count()
        context['queue_important'] = Submitted.objects.filter(content_type=ContentType.objects.get(model='location')).count()
        context['queue_longest'] = Submitted.objects.order_by('received').first().received if context['queue_length'] > 0 else None
        item = (Submitted.objects.filter(content_type=ContentType.objects.get(model='task')) | \
                Submitted.objects.filter(content_type=ContentType.objects.get(model='locationtask'))).order_by('received')
        if item.count() <= 0:
            context['type'] = None
            return context
        item = item.first()
        context['type'] = item.content_type.model
        context['subject'] = item.type
        context['team'] = item.team.name
        context['file'] = '/media/{}'.format(item.file)
        context['id'] = item.id
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            return super(AdminTaskRateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')

    def post(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            aftermovie = 'aftermovie' in request.POST and request.POST['aftermovie'] == 'on'
            try:
                s = Submitted.objects.get(id=int(request.POST['id']))
            except ObjectDoesNotExist:
                return super(AdminTaskRateView, self).get(request, *args, **kwargs)
            if s.content_type == ContentType.objects.get(model='task'):
                points = abs(int(request.POST['points']))
                try:
                    with transaction.atomic():
                        ts = TaskSolve(task=s.type, points=points, team=s.team, content=s.file)
                        ts.save()
                        s.delete()
                        if aftermovie:
                            am = Aftermovie(media=s.file)
                            am.save()
                    messages.add_message(request, messages.SUCCESS,
                                         'Succesfully awarded team {} with {} points!'.format(s.team, points))
                except DatabaseError:
                    messages.add_message(request, messages.ERROR,
                                         'Oops! Something went wrong.')
            elif s.content_type == ContentType.objects.get(model='locationtask'):
                points = abs(int(request.POST['points']))
                try:
                    with transaction.atomic():
                        lts = LocationTaskSolve(task=s.type, points=points, team=s.team, content=s.file)
                        lts.save()
                        s.delete()
                        if aftermovie:
                            am = Aftermovie(media=s.file)
                            am.save()
                    messages.add_message(request, messages.SUCCESS,
                                         'Succesfully awarded team {} with {} points!'.format(s.team, points))
                except DatabaseError:
                    messages.add_message(request, messages.ERROR,
                                         'Oops! Something went wrong.')
            else:
                messages.add_message(request, messages.ERROR, 'Oops, something went wrong.')
            return super(AdminTaskRateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')

class AdminRateView(generic.TemplateView):
    http_method_names = ['get', 'post']
    template_name = 'adminrate.html'

    def get_context_data(self, **kwargs):
        context = super(AdminRateView, self).get_context_data(**kwargs)
        context['page_type'] = 'location'
        context['queue_length'] = Submitted.objects.count()
        context['queue_important'] = Submitted.objects.filter(content_type=ContentType.objects.get(model='location')).count()
        context['queue_longest'] = Submitted.objects.order_by('received').first().received if context['queue_length'] > 0 else None
        item = Submitted.objects.filter(content_type=ContentType.objects.get(model='location')).order_by('received')
        if item.count() <= 0:
            item = Submitted.objects.filter(content_type=ContentType.objects.get(model='picture')).order_by('received')
            if item.count() <= 0:
                context['type'] = None
                return context
        item = item.first()
        context['type'] = item.content_type.model
        context['subject'] = item.type
        if item.content_type.model != 'location':
            context['subject_name'] = '/media/{}'.format(item.type.image)
        context['team'] = item.team.name
        context['file'] = '/media/{}'.format(item.file)
        context['id'] = item.id
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            return super(AdminRateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')

    def post(self, request, *args, **kwargs):
        if AuthUser.is_admin(request):
            aftermovie = 'aftermovie' in request.POST and request.POST['aftermovie'] == 'on'
            try:
                s = Submitted.objects.get(id=int(request.POST['id']))
            except ObjectDoesNotExist:
                return super(AdminRateView, self).get(request, *args, **kwargs)
            if s.content_type == ContentType.objects.get(model='task'):
                points = abs(int(request.POST['points']))
                try:
                    with transaction.atomic():
                        ts = TaskSolve(task=s.type, points=points, team=s.team, content=s.file)
                        ts.save()
                        s.delete()
                        if aftermovie:
                            am = Aftermovie(media=s.file)
                            am.save()
                    messages.add_message(request, messages.SUCCESS,
                                         'Succesfully awarded team {} with {} points!'.format(s.team, points))
                except DatabaseError:
                    messages.add_message(request, messages.ERROR,
                                         'Oops! Something went wrong.')
            elif s.content_type == ContentType.objects.get(model='locationtask'):
                points = abs(int(request.POST['points']))
                try:
                    with transaction.atomic():
                        lts = LocationTaskSolve(task=s.type, points=points, team=s.team, content=s.file)
                        lts.save()
                        s.delete()
                        if aftermovie:
                            am = Aftermovie(media=s.file)
                            am.save()
                    messages.add_message(request, messages.SUCCESS,
                                         'Succesfully awarded team {} with {} points!'.format(s.team, points))
                except DatabaseError:
                    messages.add_message(request, messages.ERROR,
                                         'Oops! Something went wrong.')
            elif s.content_type == ContentType.objects.get(model='picture'):
                if request.POST['extra'] == 'yes':
                    try:
                        with transaction.atomic():
                            p = PictureSolve(picture=s.type, team=s.team, content=s.file)
                            p.save()
                            s.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()
                        messages.add_message(request, messages.SUCCESS,
                                             'Succesfully awarded team {} with {} points!'.format(s.team, s.type.points))
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
                else:
                    try:
                        with transaction.atomic():
                            s.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()
                        messages.add_message(request, messages.SUCCESS,
                                             'You succesfully declined the picture.')
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
            elif s.content_type == ContentType.objects.get(model='location'):
                if request.POST['extra'] == 'yes':
                    try:
                        with transaction.atomic():
                            l = LocationSolve(location=s.type, team=s.team, content=s.file)
                            l.save()
                            s.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()

                        msg = ''
                        if hasattr(s.type, 'points'):
                            msg = 'Succesfully awarded team {} with {} points!'.format(s.team, s.type.points)
                        else:
                            msg = 'Succesfully approved submission of team {}!'.format(s.team)

                        messages.add_message(request, messages.SUCCESS, msg)
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
                else:
                    try:
                        with transaction.atomic():
                            s.delete()
                            if aftermovie:
                                am = Aftermovie(media=s.file)
                                am.save()
                        messages.add_message(request, messages.SUCCESS,
                                             'You succesfully declined the location.')
                    except DatabaseError:
                        messages.add_message(request, messages.ERROR,
                                             'Oops! Something went wrong.')
            else:
                messages.add_message(request, messages.ERROR, 'Oops, something went wrong.')
            return super(AdminRateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/login')


class LoginView(generic.FormView):
    template_name = 'login.html'

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        if AuthUser.is_team(request):
            return redirect('/home')
        return auth_views.login(request, template_name='login.html')

    def post(self, request, *args, **kwargs):
        if AuthUser.is_team(request):
            return redirect('/home')
        return auth_views.login(request, template_name='login.html')


class LogoutView(generic.FormView):

    def get(self, request, *args, **kwargs):
        return auth_views.logout(request, '/')


class AuthUser:
    @staticmethod
    def is_team(request):
        if request.user is not None and not request.user.is_anonymous:
            for team in Team.objects.all():
                if team.user.id is request.user.id:
                    return True
        return False

    @staticmethod
    def is_admin(request):
        if request.user is not None and not request.user.is_anonymous:
            if request.user.is_superuser:
                return True
        return False

    @staticmethod
    def get_team(request):
        if request.user is not None and not request.user.is_anonymous:
            for team in Team.objects.all():
                if team.user.id is request.user.id:
                    return team
        return None
