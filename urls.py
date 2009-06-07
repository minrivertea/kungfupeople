import os

from django.conf.urls.defaults import *
from django.conf import settings
from django.http import HttpResponseRedirect
import django.views.static
from django.contrib import admin
admin.autodiscover()

from djangopeople import views
from djangopeople.models import KungfuPerson



def redirect(url):
    return lambda res: HttpResponseRedirect(url)

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
                      
    (r'', include('djangopeople.urls')),
    
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': os.path.join(settings.OUR_ROOT, 'static')
    }),
                       
    # CSS, Javascript and IMages
    (r'^img/(?P<path>.*)$', django.views.static.serve,
     {'document_root': settings.MEDIA_ROOT + '/img',
       'show_indexes': False}),                       
    (r'^css/(?P<path>.*)$', django.views.static.serve,
      {'document_root': settings.MEDIA_ROOT + '/css',
       'show_indexes': False}),
    (r'^js/(?P<path>.*)$', django.views.static.serve,
      {'document_root': settings.MEDIA_ROOT + '/js',
       'show_indexes': False}),
                       
 
)
