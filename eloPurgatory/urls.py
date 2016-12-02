from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'(?P<region>[a-z]+)/(?P<summonerName>\w+)/', views.basicCall),
]
