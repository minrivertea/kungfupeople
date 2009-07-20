import os
from django.conf.urls.defaults import *
from django.conf import settings
from djangopeople import views
from djangopeople.models import KungfuPerson
from djangopeople.feeds import LatestAll, LatestPeople

feeds = {
    'people': LatestPeople,
    'all': LatestAll,
}

urlpatterns = patterns('',
    (r'^$', views.index),
    url(r'^club/([A-Za-z0-9-:]{3,})/$', views.club, name="club.view"),
    url(r'^style/([A-Za-z0-9-:]{3,})/$', views.style, name="style.view"),
    (r'^login/$', views.login),
    (r'^logout/$', views.logout),
    (r'^recent/$', views.recent),
    (r'^recover/$', views.lost_password),
    (r'^recover/([a-z0-9]{3,})/([a-f0-9]+)/([a-f0-9]{32})/$',
        views.lost_password_recover),
    (r'^signup/$', views.signup),
                       
    url(r'^swf_upload_test/$', views.swf_upload_test),

    (r'^guess-club-name.json$', views.guess_club_name_json),
    (r'^guess-username.json$', views.guess_username_json),

    (r'^search/$', views.search),
                       
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}),
                       
    (r'^([a-z]{2})/$', views.country),
    (r'^([a-z]{2})/sites/$', views.country_sites),
    (r'^([a-z]{2})/(\w+)/$', views.region),
    
    url(r'^([a-z0-9]{3,})/$', views.profile, name="person.view"),
    (r'^([a-z0-9]{3,})/password/$', views.edit_password),
    (r'^([a-z0-9]{3,})/videos/add/$', views.add_video),
    (r'^([a-z0-9]{3,})/videos/$', views.videos),
    (r'^([a-z0-9]{3,})/club/delete/([a-z0-9-:]{3,})/$', views.delete_club_membership),
    (r'^([a-z0-9]{3,})/style/delete/([a-z0-9-:]{3,})/$', views.delete_style),
    (r'^([a-z0-9]{3,})/videos/delete/(\d+)/$', views.delete_video),
    (r'^([a-z0-9]{3,})/diary/add/$', views.diary_entry_add),
    (r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/delete/$', views.diary_entry_delete),
    (r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/edit/$', views.diary_entry_edit),
    url(r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/location.json$', views.diary_entry_location_json),
    url(r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/$', views.diary_entry, name="diaryentry.view"),
    (r'^([a-z0-9]{3,})/club/$', views.edit_club),     # is this used?
    (r'^([a-z0-9]{3,})/style/$', views.edit_style),   # is this used?
    url(r'^([a-z0-9]{3,})/photo/(\d+)/delete/$', views.photo_delete, name="photo.delete"),
    url(r'^([a-z0-9]{3,})/photo/(\d+)/edit/$', views.photo_edit, name="photo.edit"),
    url(r'^([a-z0-9]{3,})/photo/(\d+)/$', views.photo, name="photo.view"),
    url(r'^([a-z0-9]{3,})/viewallphotos/$', views.viewallphotos),
    url(r'^([a-z0-9]{3,})/photo/upload/$', views.photo_upload, 
        {'prefer':'multiple'}),
    url(r'^([a-z0-9]{3,})/photo/upload/single/$', views.photo_upload, 
        {'prefer':'single'}),
    #url(r'^([a-z0-9]{3,})/photo/upload/multiple/$', views.photo_upload),
    url(r'^([a-z0-9]{3,})/photo/upload/pre/$', views.photo_upload_multiple_pre),

    (r'^([a-z0-9]{3,})/profile/$', views.edit_profile),
    (r'^([a-z0-9]{3,})/location/$', views.edit_location),
    url(r'^([a-z0-9]{3,})/profileupload/$', views.upload_profile_photo, name="upload_profile_photo"),
    (r'^([a-z0-9]{3,})/upload/done/$', views.upload_done),
    (r'^([a-z0-9]{3,})/whatnext/$', views.whatnext),
    url(r'^([a-z0-9]{3,})/newsletter/options/$', views.newsletter_options, 
       name="newsletter.options"),
)
