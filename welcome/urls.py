from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r'^create-welcome-emails/$', views.create_welcome_emails, 
        name="create_welcome_emails"),

    url(r'^send-unsent-emails/$', views.send_unsent_emails,
        name="send_unsent_emails"),
                       
    url(r'^create-and-send-unsent-emails/$', 
        views.create_and_send_emails, name="create_and_send_emails"),
                       
)