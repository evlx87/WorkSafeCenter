from django.urls import path

from .views import reports_index, overdue_trainings_report, overdue_medical_checks_report, incident_statistics_report

app_name = 'reports'

urlpatterns = [
    path('', reports_index, name='reports_index'), # Главная страница отчетов
    path('overdue-trainings/', overdue_trainings_report, name='overdue_trainings_report'),
    path('overdue-medical-checks/', overdue_medical_checks_report, name='overdue_medical_checks_report'),
    path('incident-statistics/', incident_statistics_report, name='incident_statistics_report'),
]
