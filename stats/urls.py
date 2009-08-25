from django.conf.urls.defaults import *
from stats import views

urlpatterns = patterns('',
    url(r'^$', views.index, name="stats_index"),
    url(r'^competitions/$', views.competitions, name="competitions"),
    url(r'^new-people/$', views.new_people, name="new_people"),
    url(r'^_list-new-people.html$', views.list_new_people_html, 
        name="list_new_people_html"),
)