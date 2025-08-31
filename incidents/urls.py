from django.urls import path
from .views import incident_list

app_name = 'incidents'

urlpatterns = [
    path('', incident_list, name='incident_list'),
]