from django.conf.urls.defaults import *
from newsletter import views

urlpatterns = patterns('',
    url(r'^send_unsent/$', views.send_unsent, name="send_unsent"),
    url(r'^(?P<newsletter_id>\d+)/send/$', views.send_unsent, name="newsletter.send"),
)