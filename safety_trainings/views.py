from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from django.utils import timezone

from trainings.models import Training, TrainingProgram
from .models import SafetyTraining


# Create your views here.
def safety_trainings_list(request):
    programs = TrainingProgram.objects.all()
    summary_data = []
    today = timezone.now().date()
    four_months_later = today + relativedelta(months=4)

    for program in programs:
        trainings_for_program = Training.objects.filter(program=program)
        total_count = trainings_for_program.count()
        approaching_count = 0

        if program.frequency_months > 0:
            for training in trainings_for_program:
                expiration_date = training.training_date + \
                    relativedelta(months=program.frequency_months)
                if today < expiration_date <= four_months_later:
                    approaching_count += 1

        if total_count > 0:  # Показываем в сводке только те программы, по которым есть обучение
            summary_data.append({
                'name': program.name,
                'hours': program.hours,
                'total_count': total_count,
                'approaching_count': approaching_count,
            })

    # код для получения списка инструктажей
    trainings = SafetyTraining.objects.all()

    # Добавляем новые данные в контекст
    context = {
        'trainings': trainings,
        'summary_data': summary_data,
    }

    return render(
        request, 'safety_trainings/safety_trainings_list.html', context)
