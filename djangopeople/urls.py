import os
from django.conf.urls.defaults import *
from django.conf import settings


from djangopeople import views
from djangopeople.models import KungfuPerson


urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^login/$', views.login),
    (r'^logout/$', views.logout),
    (r'^recent/$', views.recent),
    (r'^recover/$', views.lost_password),
    (r'^recover/([a-z0-9]{3,})/([a-f0-9]+)/([a-f0-9]{32})/$',
        views.lost_password_recover),
    (r'^signup/$', views.signup),

    (r'^guess-club-name.json$', views.guess_club_name_json),
    (r'^guess-username.json$', views.guess_username_json),

    (r'^search/$', views.search),
                       
    (r'^([a-z]{2})/$', views.country),
    (r'^([a-z]{2})/sites/$', views.country_sites),
    (r'^([a-z]{2})/(\w+)/$', views.region),
    
    (r'^([a-z0-9]{3,})/$', views.profile),
    (r'^([a-z0-9]{3,})/password/$', views.edit_password),
    (r'^([a-z0-9]{3,})/videos/add/$', views.add_video),
    (r'^([a-z0-9]{3,})/videos/$', views.videos),
    (r'^([a-z0-9]{3,})/videos/delete/(\d+)/$', views.delete_video),
    (r'^([a-z0-9]{3,})/profile/$', views.edit_profile),
    (r'^([a-z0-9]{3,})/location/$', views.edit_location),
    (r'^([a-z0-9]{3,})/upload/$', views.upload_profile_photo),
    (r'^([a-z0-9]{3,})/upload/done/$', views.upload_done),
)
