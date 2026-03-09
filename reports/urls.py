from django.urls import path

from .views import reports_index, overdue_trainings_report, overdue_medical_checks_report, incident_statistics_report, \
    training_plan_report, sout_report, documents_report, risks_report, ComplianceDashboardView, ComplianceReportView

app_name = 'reports'

urlpatterns = [
    path('', reports_index, name='reports_index'), # Главная страница отчетов
    path('overdue-trainings/', overdue_trainings_report, name='overdue_trainings_report'),
    path('overdue-medical-checks/', overdue_medical_checks_report, name='overdue_medical_checks_report'),
    path('incident-statistics/', incident_statistics_report, name='incident_statistics_report'),
    path('training-plan/', training_plan_report, name='training_plan_report'),
    path('sout/', sout_report, name='sout_report'),  # Новый
    path('documents/', documents_report, name='documents_report'),  # Новый
    path('risks/', risks_report, name='risks_report'),  # Новый
    path('compliance/', ComplianceDashboardView.as_view(), name='compliance_dashboard'),
    path('compliance/employee/<int:employee_pk>/', ComplianceReportView.as_view(), name='compliance_report'),
]
