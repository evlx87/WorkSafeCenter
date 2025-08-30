from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from employees.models import Employee


# Create your views here.
def overdue_trainings_report(request):
    overdue_date = timezone.now().date() + timedelta(days=30)
    employees = Employee.objects.filter(
        safetytraining__next_training_date__lte=overdue_date
    ).distinct()
    return render(request, 'reports/overdue_trainings.html', {'employees': employees})