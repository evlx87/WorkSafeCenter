from django.core.management.base import BaseCommand

from trainings.models import TrainingCategory, TrainingProgram


class Command(BaseCommand):
    help = 'Заполняет базу данных категориями и стандартными программами обучения'

    def handle(self, *args, **kwargs):
        # 1. Создаем ТОЛЬКО необходимые категории
        categories_data = [
            ('SAFETY',
             'Охрана труда',
             'Обучение по охране труда (Постановление № 2464)'),
            ('FIRE',
             'Пожарная безопасность',
             'Противопожарные инструктажи и обучение (69-ФЗ, 123-ФЗ)'),
            ('FIRST_AID',
             'Первая помощь',
             'Оказание первой помощи (273-ФЗ, Постановление № 2464)'),
            ('ELECTRICAL',
             'Электробезопасность',
             'Обучение по электробезопасности (Приказ № 811)'),
        ]

        categories = {}
        for code, name, desc in categories_data:
            cat, created = TrainingCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            categories[code] = cat
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создана категория: {name}'))

        # 2. Создаем стандартные программы ТОЛЬКО для необходимых категорий
        programs_data = [
            # Охрана труда (Постановление № 2464 - 3 года)
            ('Охрана труда для руководителей и специалистов', 'SAFETY', 40, 36, False),
            ('Охрана труда для рабочих профессий', 'SAFETY', 24, 24, False),

            # Пожарная безопасность (законы о ПБ)
            ('Пожарная безопасность для руководителей', 'FIRE', 16, 60, False),
            ('Пожарная безопасность для рабочих', 'FIRE', 8, 12, True),

            # Первая помощь (273-ФЗ для педагогов - 1 год, № 2464 для
            # руководителей - 1 год)
            ('Оказание первой помощи пострадавшим', 'FIRST_AID', 8, 12, False),

            # Электробезопасность (Приказ № 811 - ежегодно)
            ('Электробезопасность - группа 1', 'ELECTRICAL', 16, 12, True),
            ('Электробезопасность - группа 2', 'ELECTRICAL', 72, 12, False),
            ('Электробезопасность - группа 3', 'ELECTRICAL', 144, 12, False),
            ('Электробезопасность - группа 4', 'ELECTRICAL', 144, 12, False),
            ('Электробезопасность - группа 5', 'ELECTRICAL', 144, 12, False),
        ]

        for name, cat_code, hours, freq, mandatory in programs_data:
            prog, created = TrainingProgram.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[cat_code],
                    'hours': hours,
                    'frequency_months': freq,
                    'is_mandatory': mandatory
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Создана программа: {name}'))

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Настройка данных обучения завершена!'))
