from django.conf.urls.defaults import *
from stats import views

urlpatterns = patterns('',
    url(r'^competitions/$', views.competitions, name="competitions"),
)