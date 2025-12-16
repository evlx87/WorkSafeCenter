from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from incidents.models import Incident
from medical_checks.models import MedicalCheck
from trainings.models import Instruction


def index(request):
    today = timezone.now().date()
    # Дата через 30 дней для поиска приближающихся событий
    in_30_days = today + timedelta(days=30)

    # 1. Просроченные медосмотры (дата следующего осмотра уже прошла)
    overdue_checks_count = MedicalCheck.objects.filter(
        next_check_date__lt=today, employee__is_active=True
    ).values('employee').distinct().count()

    # 2. Просроченные инструктажи (аналогично)
    overdue_trainings_count = Instruction.objects.filter(
        next_training_date__lt=today, employee__is_active=True
    ).values('employee').distinct().count()

    # 3. Приближающиеся события (в ближайшие 30 дней)
    upcoming_events = list(
        MedicalCheck.objects.filter(
            next_check_date__gte=today,
            next_check_date__lte=in_30_days,
            employee__is_active=True))
    upcoming_events += list(
        Instruction.objects.filter(
            next_training_date__gte=today,
            next_training_date__lte=in_30_days,
            employee__is_active=True))

    # 4. Инциденты за последние 30 дней
    last_30_days = today - timedelta(days=30)
    recent_incidents_count = Incident.objects.filter(
        incident_date__gte=last_30_days).count()

    context = {
        'overdue_checks_count': overdue_checks_count,
        'overdue_trainings_count': overdue_trainings_count,
        'upcoming_events_count': len(upcoming_events),
        'recent_incidents_count': recent_incidents_count,
    }

    return render(request, 'index.html', context)
