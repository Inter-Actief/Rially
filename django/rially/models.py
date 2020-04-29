from functools import partial

import os

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.crypto import get_random_string
from django.db.models import Sum
from django.db.models import CASCADE


def _update_filename(instance, filename, path):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(get_random_string(32), ext)
    return os.path.join(path, filename)


def upload_to(path):
    return partial(_update_filename, path=path)


class Team(models.Model):
    name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    telegram_token = models.CharField(max_length=50, default=None, null=True)

    def solved_tasks(self):
        return self.tasksolve_set.filter(team=self).values_list('task__id', flat=True).all()

    def processing_tasks(self):
        return self.submitted_set.filter(content_type=ContentType.objects.get(model='task')).values_list('object_id', flat=True).all()

    def solved_locationtasks(self):
        return self.locationtasksolve_set.filter(team=self).values_list('task__id', flat=True).all()

    def processing_locationtasks(self):
        return self.submitted_set.filter(content_type=ContentType.objects.get(model='locationtask')).values_list('object_id', flat=True).all()

    def points_tasks(self):
        res = self.solved_tasks().aggregate(Sum('points'))['points__sum']
        res2 = self.solved_locationtasks().aggregate(Sum('points'))['points__sum']
        if res is None:
            res = 0
        if res2 is None:
            res2 = 0
        return res + res2

    def solved_pictures(self):
        return self.picturesolve_set.filter(team=self).values_list('picture', flat=True).all()

    def processing_pictures(self):
        return self.submitted_set.filter(content_type=ContentType.objects.get(model='picture')).values_list('object_id', flat=True).all()

    def points_pictures(self):
        res = self.solved_pictures().aggregate(Sum('picture__points'))['picture__points__sum']
        if res is None:
            res = 0
        return res

    def solved_locations(self):
        return self.locationsolve_set.filter(team=self).values_list('location', flat=True).all()

    def processing_locations(self):
        return self.submitted_set.filter(content_type=ContentType.objects.get(model='location')).values_list('object_id', flat=True).all()

    def points_bonus(self):
        res = self.bonus_set.aggregate(Sum('points'))['points__sum']
        if res is None:
            res = 0
        return res

    def points_penalty(self):
        res = self.penalty_set.aggregate(Sum('points'))['points__sum']
        if res is None:
            res = 0
        else:
            res *= -1
        return res

    def points_total(self):
        return self.points_pictures() + self.points_tasks() + self.points_bonus() + self.points_penalty()

    def __str__(self):
        return 'Team: %s' % self.name


class TeamTelegramSession(models.Model):
    telegram_chat_id = models.CharField(max_length=64, primary_key=True)
    team = models.ForeignKey(Team, on_delete=CASCADE)


class Submitted(models.Model):
    object_id = models.PositiveIntegerField()
    type = GenericForeignKey('content_type', 'object_id')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    file = models.CharField(max_length=64)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    received = models.DateTimeField(auto_now_add=True)


class PriorityQueueItem(models.Model):
    submitted = models.ForeignKey(Submitted, on_delete=models.CASCADE)
    time_sent = models.DateTimeField()

    def __str__(self):
        return 'PrioQueue Item %s for %s' % (self.submitted.object_id, self.submitted.team)

class QueueItem(models.Model):
    submitted = models.ForeignKey(Submitted, on_delete=models.CASCADE)
    time_sent = models.DateTimeField()

    def __str__(self):
        return 'Queue Item %s for %s' % (self.submitted.object_id, self.submitted.team)


class Location(models.Model):
    name = models.TextField()
    description = models.TextField()
    id = models.IntegerField(unique=True, primary_key=True)
    ordering = ['id']

    def __str__(self):
        return 'Location %s: %s' % (self.id, self.name)


class Puzzle(models.Model):
    name = models.TextField()
    file = models.FileField(upload_to=upload_to(''), null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=CASCADE)

    def __str__(self):
        return 'Puzzle %s (%s): %s' % (self.id, self.location, self.name)


class LocationTask(models.Model):
    name = models.TextField()
    location = models.ForeignKey(Location, on_delete=CASCADE)

    def __str__(self):
        return 'LocationTask %s (%s): %s' % (self.id, self.location, self.name)


class Task(models.Model):
    name = models.TextField()

    def __str__(self):
        return 'Task %s: %s' % (self.id, self.name)


class Picture(models.Model):
    points = models.IntegerField()
    image = models.ImageField(upload_to=upload_to(''))
    location = models.ForeignKey(Location, on_delete=CASCADE)

    def __str__(self):
        return 'Picture (%s): %s' % (self.location, self.id)


class PictureSolve(models.Model):
    picture = models.ForeignKey(Picture, on_delete=CASCADE)
    team = models.ForeignKey(Team, on_delete=CASCADE)
    content = models.CharField(max_length=50)

    class Meta:
        unique_together = (("picture", "team"),)

    def __str__(self):
        return '%s solved %s' % (self.team, self.picture)


class LocationTaskSolve(models.Model):
    task = models.ForeignKey(LocationTask, on_delete=CASCADE)
    points = models.IntegerField()
    team = models.ForeignKey(Team, on_delete=CASCADE)
    content = models.CharField(max_length=50)

    class Meta:
        unique_together = (("task", "team"),)

    def __str__(self):
        return '%s solved %s' % (self.team, self.task)


class TaskSolve(models.Model):
    task = models.ForeignKey(Task, on_delete=CASCADE)
    points = models.IntegerField()
    team = models.ForeignKey(Team, on_delete=CASCADE)
    content = models.CharField(max_length=50)

    class Meta:
        unique_together = (("task", "team"),)

    def __str__(self):
        return '%s solved %s' % (self.team, self.task)


class LocationSolve(models.Model):
    location = models.ForeignKey(Location, on_delete=CASCADE)
    team = models.ForeignKey(Team, on_delete=CASCADE)
    content = models.CharField(max_length=50)

    class Meta:
        unique_together = (("location", "team"),)

    def __str__(self):
        return '%s unlocked %s' % (self.team, self.location)


class Aftermovie(models.Model):
    media = models.CharField(max_length=50)


class Bonus(models.Model):
    reason = models.TextField()
    points = models.IntegerField()
    team = models.ForeignKey(Team, on_delete=CASCADE)

    class Meta:
        verbose_name_plural = "Bonuses"

    def __str__(self):
        return '%s got a bonus of %s because %s' % (self.team, self.points, self.reason)


class Penalty(models.Model):
    reason = models.TextField()
    points = models.IntegerField()
    team = models.ForeignKey(Team, on_delete=CASCADE)

    class Meta:
        verbose_name_plural = "Penalties"

    def __str__(self):
        return '%s got a penalty of %s because %s' % (self.team, self.points, self.reason)

class SiteState(models.Model):
    submission_open = models.BooleanField()
    show_scoreboard = models.BooleanField()

    def save(self, *args, **kwargs):
        if self.id != None and SiteState.objects.all().count() > 1 or self.id == None and SiteState.objects.all().count() >= 1:
            raise ValueError("There can only be one SiteState entry.")
        else:
            super(SiteState, self).save(*args, **kwargs)

    def __str__(self):
        return  'Submissons are %s, ' % ("open" if self.submission_open else "closed") + \
                'Scores are %s.' % ("shown" if self.show_scoreboard else "hidden")
