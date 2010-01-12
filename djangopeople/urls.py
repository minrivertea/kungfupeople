# python
import os

# django
from django.conf.urls.defaults import *
from django.conf import settings
from djangopeople.models import KungfuPerson
from djangopeople.feeds import LatestAll, LatestPeople

# app
from djangopeople import views

feeds = {
    'people': LatestPeople,
    'all': LatestAll,
}

urlpatterns = patterns('',
    (r'^$', views.index),
    url(r'^club/([A-Za-z0-9-:]{3,})/$', views.club, name="club.view"),
    url(r'^clubs/$', views.clubs_all, name="clubs_all"),
    url(r'^style/([A-Za-z0-9-:]{3,})/$', views.style, name="style.view"),
                       
    url(r'^all/(clubs|styles|people|photos)/$', views.all_something, 
        name="all_something"),
    url(r'^all/(clubs|styles|people|photos)/by-date/$', views.all_something,
        {'sort_by':'date'}, name="all_something_by_date"),
                       
    (r'^login/$', views.login),
    (r'^logout/$', views.logout),
    (r'^recent/$', views.recent),
    (r'^recover/$', views.lost_password),
    (r'^recover/([a-z0-9]{3,})/([a-f0-9]+)/([a-f0-9]{32})/$',
        views.lost_password_recover),
    url(r'^signup/$', views.signup, name="signup"),
    url(r'^wall/$', views.wall, name="wall"),
    url(r'^zoom/$', views.zoom, name="zoom"),
    url(r'^zoom-content/$', views.zoom_content, name="zoom_content"),
    url(r'^zoom-content.json$', views.zoom_content_json, name="zoom_content_json"),
                       
    url(r'^swf_upload_test/$', views.swf_upload_test),

    (r'^guess-club-name.json$', views.guess_club_name_json),
    (r'^guess-username.json$', views.guess_username_json),
    url(r'^find-clubs-by-location.json$', views.find_clubs_by_location_json),

    url(r'^_nav.html$', views.nav_html, name="nav_html"),
    url(r'^search/$', views.search, name="search"),
    url(r'^tinymcefilebrowser/$', views.tinymce_filebrowser,
       name="tinymce.filebrowser"),
    url(r'^runway/$', views.runway, name="runway"),
    url(r'^runway/data.js$', views.runway_data_js, name="runway_data_js"),
    url(r'^crossdomain.xml$', views.crossdomain_xml, name="crossdomain_xml"),
                       
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}),
                       
    url(r'^([a-z]{2})/$', views.country, name="country"),
    (r'^([a-z]{2})/sites/$', views.country_sites),
    (r'^([a-z]{2})/(\w+)/$', views.region),
    
    url(r'^([a-z0-9]{3,})/$', views.profile, name="person.view"),
    url(r'^([a-z0-9]{3,})/crop-profile-photo/$', views.crop_profile_photo,
        name="crop_profile_photo"),
    url(r'^([a-z0-9]{3,})/_user-info.html$', views.user_info_html,
        name="user_info_html"), # used by runway

    url(r'^([a-z0-9]{3,})/_user-info-map.html$', views.user_info_html,
        {'include_photo':True},
        name="user_info_html"), # used by worldmap
    url(r'^([a-z0-9]{3,})/password/$', views.edit_password, name="edit_password"),
    url(r'^all-videos/$', views.videos_all, name="videos_all"),
    url(r'^([a-z0-9]{3,})/videos/add/$', views.add_video, name="add_video"),
    url(r'^([a-z0-9]{3,})/video/(\d+)/$', views.video, name="video.view"),
    url('^get_youtube_video_by_id.json$', views.get_youtube_video_by_id_json),
    (r'^([a-z0-9]{3,})/club/delete/([a-z0-9-:]{3,})/$', views.delete_club_membership),
    url(r'^([a-z0-9]{3,})/style/delete/([a-z0-9-:]{3,})/$', views.delete_style, 
       name="delete_style"),
    url(r'^([a-z0-9]{3,})/videos/delete/(\d+)/$', views.delete_video, name="delete_video"),

    url(r'^([a-z0-9]{3,})/diary/add/$', views.diary_entry_add, name="add_diary_entry"),
    (r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/delete/$', views.diary_entry_delete),
    (r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/edit/$', views.diary_entry_edit),
    url(r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/location.json$', views.diary_entry_location_json),
    url(r'^([a-z0-9]{3,})/diary/([a-z0-9-]{3,})/$', views.diary_entry, name="diaryentry.view"),
    url(r'^([a-z0-9]{3,})/club/$', views.edit_club, name="edit_club"),    
    url(r'^([a-z0-9]{3,})/style/$', views.edit_style, name="edit_style"),
    url(r'^([a-z0-9]{3,})/photo/(\d+)/delete/$', views.photo_delete, name="photo.delete"),
    url(r'^([a-z0-9]{3,})/photo/(\d+)/edit/$', views.photo_edit, name="photo.edit"),
    url(r'^([a-z0-9]{3,})/photo/(\d+)/$', views.photo, name="photo.view"),
    url(r'^([a-z0-9]{3,})/viewallphotos/$', views.viewallphotos),
    url(r'^([a-z0-9]{3,})/photo/upload/$', views.photo_upload, 
        {'prefer':'multiple'}, name="upload_photo"),
    url(r'^([a-z0-9]{3,})/photo/upload/single/$', views.photo_upload, 
        {'prefer':'single'}),
    #url(r'^([a-z0-9]{3,})/photo/upload/multiple/$', views.photo_upload),
    url(r'^([a-z0-9]{3,})/photo/upload/pre/$', views.photo_upload_multiple_pre),

    url(r'^([a-z0-9]{3,})/profile/$', views.edit_profile, name="edit_profile"),
    (r'^([a-z0-9]{3,})/location/$', views.edit_location),
    url(r'^([a-z0-9]{3,})/profileupload/$', views.upload_profile_photo,
        name="upload_profile_photo"),
    url(r'^([a-z0-9]{3,})/profileupload/webcam/$', views.webcam_profile_photo,
        name="webcam_profile_photo"),
    #(r'^([a-z0-9]{3,})/upload/done/$', views.upload_done),
    (r'^([a-z0-9]{3,})/whatnext/$', views.whatnext),
    url(r'^([a-z0-9]{3,})/newsletter/options/$', views.newsletter_options, 
       name="newsletter.options"),
)
