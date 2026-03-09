from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from employees.models import Employee
from incidents.models import Incident
from medical_checks.models import MedicalCheck
from trainings.models import Training, TrainingProgram, TrainingCategory
from trainings.services import check_employee_compliance


# Create your views here.
def overdue_trainings_report(request):
    overdue_date = timezone.now().date() + timedelta(days=30)
    employees = Employee.objects.filter(
        instructions__next_training_date__lte=overdue_date,
        is_active=True
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
    Улучшенное представление для формирования списка направляемых на обучение
    с фильтрацией по категории обучения
    """
    programs = TrainingProgram.objects.all().select_related('category')
    categories = TrainingCategory.objects.filter(is_active=True)

    selected_program_id = request.GET.get('program')
    selected_category = request.GET.get('category')
    planning_horizon_months = int(request.GET.get('horizon', 6))

    employees_to_train = []
    selected_program = None
    today = timezone.now().date()
    horizon_date = today + relativedelta(months=planning_horizon_months)

    # Фильтрация программ
    if selected_program_id:
        selected_program = get_object_or_404(
            TrainingProgram, id=selected_program_id)
        programs = programs.filter(id=selected_program_id)
    elif selected_category:
        programs = programs.filter(category__code=selected_category)

    # Получаем всех активных сотрудников
    all_employees = Employee.objects.filter(
        is_active=True,
        termination_date__isnull=True
    ).select_related('position', 'department')

    for emp in all_employees:
        for program in programs:
            # Проверяем, нужна ли эта программа сотруднику
            if not _is_program_required_for_employee(emp, program):
                continue

            # Ищем последнее обучение по этой программе
            last_training = Training.objects.filter(
                employee=emp,
                program=program
            ).order_by('-training_date').first()

            needs_training = False
            reason = ""
            expiry_date = None

            if last_training:
                # Обучение было - проверяем срок действия
                if program.frequency_months > 0:
                    expiry_date = last_training.training_date + relativedelta(
                        months=program.frequency_months
                    )
                    if expiry_date <= horizon_date:
                        needs_training = True
                        if expiry_date < today:
                            reason = f"Просрочено (истекло {
                                expiry_date.strftime('%d.%m.%Y')})"
                        else:
                            reason = f"Истекает {
                                expiry_date.strftime('%d.%m.%Y')}"
            else:
                # Обучение не было - нужно первичное
                needs_training = True
                reason = "Первичное обучение (не пройдено)"

            if needs_training:
                # Проверяем, нет ли уже записи для этого сотрудника и программы
                already_in_list = any(
                    e['employee'].id == emp.id and e['program'].id == program.id
                    for e in employees_to_train
                )
                if not already_in_list:
                    employees_to_train.append({
                        'employee': emp,
                        'program': program,
                        'reason': reason,
                        'expiry_date': expiry_date,
                        'last_training_date': last_training.training_date if last_training else None,
                        'priority': _calculate_priority(emp, program, expiry_date, today)
                    })

    # Сортировка по приоритету
    employees_to_train.sort(
        key=lambda x: (
            x['priority'],
            x['expiry_date'] or today))

    return render(request, 'reports/training_plan.html', {
        'programs': programs,
        'categories': categories,
        'employees': employees_to_train,
        'selected_program': selected_program,
        'selected_category': selected_category,
        'planning_horizon_months': planning_horizon_months,
    })


def _is_program_required_for_employee(employee, program):
    """
    Определяет, требуется ли сотруднику данная программа обучения
    """
    category_code = program.category.code if program.category else None

    # 1. Если программа обязательна для всех
    if program.is_mandatory:
        return True

    # 2. Проверка по целевым должностям
    if program.target_positions.exists():
        if employee.position and program.target_positions.filter(
                id=employee.position.id
        ).exists():
            return True

    # 3. Проверка по категории и статусу сотрудника
    if category_code == 'SAFETY':  # Охрана труда
        # Нужна руководителям, членам комиссии, специалистам по ОТ
        if (employee.is_executive or
                employee.is_safety_committee_member or
                employee.is_safety_specialist):
            return True
        # Также нужна всем рабочим (если не освобождены)
        if not employee.exempt_from_safety_instruction:
            return True

    elif category_code == 'FIRE':  # Пожарная безопасность
        # Нужна руководителям и всем сотрудникам
        if employee.is_executive or not employee.exempt_from_safety_instruction:
            return True

    elif category_code == 'FIRST_AID':  # Первая помощь
        # Нужна руководителям, педагогам, членам комиссии
        if (employee.is_executive or
                employee.is_pedagogical or
                employee.is_safety_committee_member):
            return True

    elif category_code == 'ELECTRICAL':  # Электробезопасность
        # Нужна всем (минимум 1 группа)
        return True

    elif category_code == 'WORKING_HEIGHT':  # Работы на высоте
        # Только если должность требует
        if employee.position and any(
                keyword in employee.position.name.lower()
                for keyword in ['монтажник', 'высот', 'кровель', 'строитель']
        ):
            return True

    return False


def _calculate_priority(employee, program, expiry_date, today):
    """
    Рассчитывает приоритет обучения (1 - highest, 5 - lowest)
    """
    if not expiry_date:
        return 2  # Первичное обучение - высокий приоритет

    days_until_expiry = (expiry_date - today).days

    if days_until_expiry < 0:
        return 1  # Просрочено - критический приоритет
    elif days_until_expiry <= 30:
        return 2  # Истекает в течение месяца
    elif days_until_expiry <= 60:
        return 3  # Истекает в течение 2 месяцев
    elif days_until_expiry <= 90:
        return 4  # Истекает в течение 3 месяцев
    else:
        return 5  # Плановое


def sout_report(request):
    """Отчет по специальной оценке условий труда"""
    from assessments.models import Workplace
    from django.utils import timezone

    today = timezone.now().date()
    workplaces = Workplace.objects.select_related(
        'sout', 'position', 'site').all()

    stats = {
        'total': workplaces.count(),
        'not_conducted': 0,
        'expired': 0,
        'warning': 0,
        'valid': 0,
    }

    for wp in workplaces:
        status = wp.sout_status
        if status in stats:
            stats[status] += 1

    return render(request, 'reports/sout_report.html', {
        'workplaces': workplaces,
        'stats': stats,
        'today': today,
    })


def documents_report(request):
    """Отчет по документам"""
    from documents.models import Document
    from django.utils import timezone

    today = timezone.now().date()
    documents = Document.objects.all().select_related('employee', 'category')

    stats = {
        'total': documents.count(),
        'overdue': documents.filter(end_date__lt=today).count(),
        'expiring_soon': documents.filter(
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30)
        ).count(),
    }

    return render(request, 'reports/documents_report.html', {
        'documents': documents,
        'stats': stats,
    })


def risks_report(request):
    """Отчет по профессиональным рискам"""
    from assessments.models import RiskAssessment, Workplace

    workplaces = Workplace.objects.prefetch_related('risks').all()

    stats = {
        'total_workplaces': workplaces.count(),
        'with_risks': workplaces.filter(
            risks__isnull=False).distinct().count(),
        'high_risks': RiskAssessment.objects.filter(
            risk_level__in=[
                'high',
                'critical']).count(),
    }

    return render(request, 'reports/risks_report.html', {
        'workplaces': workplaces,
        'stats': stats,
    })


class ComplianceDashboardView(TemplateView):
    """Панель соответствия требованиям по обучению"""
    template_name = 'reports/compliance_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        all_employees = Employee.objects.filter(
            is_active=True,
            termination_date__isnull=True
        )

        violations_count = 0
        warnings_count = 0
        compliant_count = 0

        for emp in all_employees:
            status = check_employee_compliance(emp)
            has_violations = (
                status['expired_programs'] or
                status['expired_instructions']
            )
            has_warnings = (
                status['missing_programs'] or
                status['missing_instructions']
            )

            if has_violations:
                violations_count += 1
            elif has_warnings:
                warnings_count += 1
            else:
                compliant_count += 1

        context.update({
            'total_employees': all_employees.count(),
            'compliant_count': compliant_count,
            'violations_count': violations_count,
            'warnings_count': warnings_count,
            'compliance_rate': round(
                compliant_count / all_employees.count() * 100, 1
            ) if all_employees.count() > 0 else 0,
            'today': today,
        })

        return context


class ComplianceReportView(TemplateView):
    """Отчёт по соответствию конкретного сотрудника"""
    template_name = 'reports/compliance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = get_object_or_404(Employee, pk=kwargs['employee_pk'])
        compliance_status = check_employee_compliance(employee)

        context.update({
            'employee': employee,
            'compliance': compliance_status,
            'today': timezone.now().date(),
        })

        return context
