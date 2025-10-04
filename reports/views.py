from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from employees.models import Employee
from incidents.models import Incident
from medical_checks.models import MedicalCheck


# Create your views here.
def overdue_trainings_report(request):
    overdue_date = timezone.now().date() + timedelta(days=30)
    employees = Employee.objects.filter(
        safetytraining__next_training_date__lte=overdue_date
    ).distinct()
    return render(request,
                  'reports/overdue_trainings.html',
                  {'employees': employees})


def reports_index(request):
    """Отображает главную страницу со ссылками на все отчеты."""
    return render(request, 'reports/reports_index.html')


def overdue_medical_checks_report(request):
    """Отчет по сотрудникам с приближающимся сроком медосмотра."""
    overdue_date = timezone.now().date() + timedelta(days=30)

    # Находим ID сотрудников, у которых есть предстоящий медосмотр
    employee_ids = MedicalCheck.objects.filter(
        next_check_date__lte=overdue_date,
        employee__is_active=True
    ).values_list('employee_id', flat=True)

    employees = Employee.objects.filter(
        id__in=set(employee_ids)).order_by('last_name')

    return render(request,
                  'reports/overdue_medical_checks.html',
                  {'employees': employees})


def incident_statistics_report(request):
    """Отчет со статистикой по типам инцидентов."""
    stats = Incident.objects.values('incident_type').annotate(
        count=Count('id')).order_by('incident_type')

    # Для отображения полных названий в шаблоне
    incident_type_map = dict(Incident.INCIDENT_TYPES)

    incident_stats = [
        {
            'type_name': incident_type_map.get(item['incident_type']),
            'count': item['count']
        }
        for item in stats
    ]

    return render(request, 'reports/incident_statistics.html',
                  {'incident_stats': incident_stats})
