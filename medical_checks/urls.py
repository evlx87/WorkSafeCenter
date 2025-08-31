from django.urls import path
from .views import medical_check_list

app_name = 'medical_checks'

urlpatterns = [
    path('', medical_check_list, name='medical_check_list'),
]