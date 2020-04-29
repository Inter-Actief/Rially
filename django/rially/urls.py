"""rially URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView

from rially import settings
from rially.views import LocationView, LoginView, HomeView, LogoutView, \
    ScoreView, AdminScoreView, BonusView, TasksView, AdminRateView, \
    AdminDownloadView, AdminTaskRateView, HelpView, AdminPanelView, \
    AdminDistributedRateView

urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^admin/', admin.site.urls),
    url(r'^home/$', HomeView.as_view()),
    url(r'^tasks/$', TasksView.as_view()),
    url(r'^bonus/$', BonusView.as_view()),
    url(r'^score/$', ScoreView.as_view()),
    url(r'^adminpanel/$', AdminPanelView.as_view()),
    url(r'^adminscore/$', AdminScoreView.as_view()),
    url(r'^adminrate/$', AdminRateView.as_view()),
    url(r'^admintaskrate/$', AdminTaskRateView.as_view()),
    url(r'^adminratedist$', AdminDistributedRateView.as_view()),
    url(r'^admindownload/$', AdminDownloadView.as_view()),
    url(r'^location/(?P<pk>\d+)/', LocationView.as_view()),
    url(r'^help/$', HelpView.as_view()),
    url(r'^$', RedirectView.as_view(url='/home')),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
