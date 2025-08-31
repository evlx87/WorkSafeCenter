from django.urls import path
from .views import safety_trainings_list

app_name = 'safety_trainings'

urlpatterns = [
    path('', safety_trainings_list, name='safety_trainings_list'),
]