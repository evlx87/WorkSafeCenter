from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from django.utils import timezone

from trainings.models import Training
from .models import SafetyTraining


# Create your views here.
def safety_trainings_list(request):
    # 1. Получаем уникальные программы обучения (по названию и часам)
    unique_programs = Training.objects.values(
        'program_name', 'hours').distinct()

    summary_data = []
    today = timezone.now().date()
    four_months_later = today + relativedelta(months=4)

    for program in unique_programs:
        # 2. Для каждой программы получаем все связанные записи об обучении
        trainings_for_program = Training.objects.filter(
            program_name=program['program_name'],
            hours=program['hours']
        )

        total_count = trainings_for_program.count()
        approaching_count = 0

        # 3. Проверяем каждую запись на приближение срока повторного обучения
        for training in trainings_for_program:
            if training.frequency_months > 0:
                expiration_date = training.training_date + \
                    relativedelta(months=training.frequency_months)
                # Считаем тех, у кого срок истекает в ближайшие 4 месяца, но
                # еще не прошел
                if today < expiration_date <= four_months_later:
                    approaching_count += 1

        summary_data.append({
            'name': program['program_name'],
            'hours': program['hours'],
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
