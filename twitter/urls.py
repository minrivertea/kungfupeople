from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
        url(r'^auth/$', views.auth, name='auth'),
        url(r'^return/$', views.return_, name='return'),
        url(r'^unauth/$', views.unauth, name='unauth'),

        url(r'^signup/$', views.twitter_signup, name='twitter_signup'),
        url(r'^reset/$', views.reset_session, name='twitter_reset'),

)