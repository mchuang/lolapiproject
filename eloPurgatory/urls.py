from django.conf.urls import url

from . import views

app_name = 'eloPurgatory'
urlpatterns = [
    url(r'^(?P<region>[a-z]+)/(?P<summonerName>\w+)/(?P<queue>\w+)/$', views.basicCall, name='basicCall'),
    url(r'^home', views.home, name='home'),
    url(r'^search', views.handler, name='handler'),
]
