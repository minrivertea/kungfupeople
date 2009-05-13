from django.conf.urls.defaults import *
from django.conf import settings
from django.http import HttpResponseRedirect
from djangopeople import views
from djangopeople.models import KungfuPerson
import os

def redirect(url):
    return lambda res: HttpResponseRedirect(url)

urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^login/$', views.login),
    (r'^logout/$', views.logout),
    (r'^about/$', views.about),
    (r'^recent/$', views.recent),
    (r'^recover/$', views.lost_password),
    (r'^recover/([a-z0-9]{3,})/([a-f0-9]+)/([a-f0-9]{32})/$',
        views.lost_password_recover),
    (r'^signup/$', views.signup),

    (r'^openid/$', 'django_openidconsumer.views.begin', {
        'sreg': 'email,nickname,fullname',
        'redirect_to': '/openid/complete/',    
    }),

    (r'^guess-club-name.json$', views.guess_club_name_json),
    (r'^guess-username.json$', views.guess_username_json),

    (r'^search/$', views.search),
    
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': os.path.join(settings.OUR_ROOT, 'static')
    }),
    (r'^admin/', include('django.contrib.admin.urls')),

    (r'^uk/$', redirect('/gb/')),
    (r'^([a-z]{2})/$', views.country),
    (r'^([a-z]{2})/sites/$', views.country_sites),
    (r'^([a-z]{2})/(\w+)/$', views.region),
    
    (r'^([a-z0-9]{3,})/$', views.profile),
    (r'^([a-z0-9]{3,})/bio/$', views.edit_bio),
    (r'^([a-z0-9]{3,})/password/$', views.edit_password),
    (r'^([a-z0-9]{3,})/account/$', views.edit_account),
    (r'^([a-z0-9]{3,})/location/$', views.edit_location),
    (r'^([a-z0-9]{3,})/finding/$', views.edit_finding),
    (r'^([a-z0-9]{3,})/upload/$', views.upload_profile_photo),
    (r'^([a-z0-9]{3,})/upload/done/$', views.upload_done),
)
