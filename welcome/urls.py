from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r'^create-welcome-emails/$', views.create_welcome_emails, 
        name="create_welcome_emails"),

)