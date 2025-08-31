from django.urls import path
from .views import overdue_trainings_report

app_name = 'reports'

urlpatterns = [
    path('overdue-trainings/', overdue_trainings_report, name='overdue_trainings_report'),
]