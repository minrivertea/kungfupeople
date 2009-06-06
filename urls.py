import os

from django.conf.urls.defaults import *
from django.conf import settings
from django.http import HttpResponseRedirect
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
 
)
