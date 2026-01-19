from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from employees.models import Employee
from incidents.models import Incident
from medical_checks.models import MedicalCheck
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from trainings.models import Training, TrainingProgram


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


def training_plan_report(request):
    """
    Представление для формирования списка направляемых на обучение.
    """
    programs = TrainingProgram.objects.all()
    selected_program_id = request.GET.get('program')
    employees_to_train = []
    selected_program = None

    if selected_program_id:
        selected_program = get_object_or_404(
            TrainingProgram, id=selected_program_id)
        today = timezone.now().date()
        six_months_later = today + relativedelta(months=6)

        # Критерий по должности/статусу (Педагоги, Руководители, Замы)
        target_group_query = Q(is_pedagogical=True) | \
            Q(is_executive=True) | \
            Q(position__name__icontains="заместитель")

        # Получаем всех активных сотрудников
        all_employees = Employee.objects.filter(is_active=True)

        for emp in all_employees:
            # Ищем последнее обучение сотрудника по выбранной программе
            last_training = Training.objects.filter(
                employee=emp,
                program=selected_program
            ).order_by('-training_date').first()

            if last_training:
                # 1. Если обучение было, проверяем когда оно истекает
                # Используем частоту из программы (в месяцах)
                expiry_date = last_training.training_date + \
                    relativedelta(months=selected_program.frequency_months)

                if expiry_date <= six_months_later:
                    emp.reason = f"Повторно (истекает {
                        expiry_date.strftime('%d.%m.%Y')})"
                    employees_to_train.append(emp)
            else:
                # 2. Если обучения не было, проверяем, подходит ли он по
                # должности
                is_target = Employee.objects.filter(
                    pk=emp.id).filter(target_group_query).exists()
                if is_target:
                    emp.reason = "Первичное (согласно должности)"
                    employees_to_train.append(emp)

    return render(request, 'reports/training_plan.html', {
        'programs': programs,
        'employees': employees_to_train,
        'selected_program': selected_program,
    })
