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

from sitemaps import FlatPageSitemap, sitemap, CustomSitemap

sitemaps = {
    'flatpages': FlatPageSitemap,
    'otherpages': CustomSitemap,
}


urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
                      
    (r'', include('djangopeople.urls')),
    (r'^newsletters/', include('newsletter.urls')),
                       
    (r'^sitemap.xml$', sitemap,
     {'sitemaps': sitemaps}),
                       
)

if settings.DEBUG:
    
    # When not in debug mode (i.e. development mode)
    # nothing django.views.static.serve should not be used at all.
    # If it is used it means that nginx config isn't good enough.
    
    urlpatterns += patterns('', 
                            
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
                            