from django.conf.urls.defaults import *
from stats import views

urlpatterns = patterns('',
    url(r'^/$', views.index, name="index"),
    url(r'^competitions/$', views.competitions, name="competitions"),
)