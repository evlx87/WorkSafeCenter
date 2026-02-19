from django.core.management.base import BaseCommand
from trainings.models import TrainingCategory, TrainingProgram


class Command(BaseCommand):
    help = 'Заполняет базу данных категориями и стандартными программами обучения'

    def handle(self, *args, **kwargs):
        # 1. Создаем категории
        categories_data = [
            ('SAFETY', 'Охрана труда', 'Обучение по охране труда'),
            ('FIRE', 'Пожарная безопасность', 'Противопожарные инструктажи и обучение'),
            ('FIRST_AID', 'Первая помощь', 'Оказание первой помощи пострадавшим'),
            ('ELECTRICAL', 'Электробезопасность', 'Обучение по электробезопасности'),
            ('CIVIL_DEFENSE', 'Гражданская оборона', 'ГО и действия в ЧС'),
            ('ROAD_SAFETY', 'Безопасность дорожного движения', 'Обучение по БДД'),
            ('WORKING_HEIGHT', 'Работы на высоте', 'Обучение работам на высоте'),
            ('ANTITERROR', 'Антитеррористическая защищенность', 'Антитеррористическая безопасность'),
            ('ENVIRONMENTAL', 'Экологическая безопасность', 'Экологическая безопасность'),
            ('OTHER', 'Другое', 'Прочие виды обучения'),
        ]

        categories = {}
        for code, name, desc in categories_data:
            cat, created = TrainingCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc}
            )
            categories[code] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создана категория: {name}'))

        # 2. Создаем стандартные программы
        programs_data = [
            # Охрана труда
            ('Охрана труда для руководителей и специалистов', 'SAFETY', 40, 36, False),
            ('Охрана труда для рабочих профессий', 'SAFETY', 24, 24, False),

            # Пожарная безопасность
            ('Пожарная безопасность для руководителей', 'FIRE', 16, 60, False),
            ('Пожарная безопасность для рабочих', 'FIRE', 8, 12, True),

            # Первая помощь
            ('Оказание первой помощи пострадавшим', 'FIRST_AID', 8, 12, False),

            # Электробезопасность
            ('Электробезопасность - группа 1', 'ELECTRICAL', 16, 12, True),
            ('Электробезопасность - группа 2', 'ELECTRICAL', 72, 12, False),
            ('Электробезопасность - группа 3', 'ELECTRICAL', 144, 12, False),
            ('Электробезопасность - группа 4', 'ELECTRICAL', 144, 12, False),

            # Гражданская оборона
            ('Действия в чрезвычайных ситуациях', 'CIVIL_DEFENSE', 8, 24, False),
            ('Противодействие терроризму', 'CIVIL_DEFENSE', 8, 24, False),

            # БДД
            ('БДД для ответственных за БДД', 'ROAD_SAFETY', 40, 36, False),

            # Экологическая безопасность
            ('Экологическая безопасность', 'ENVIRONMENTAL', 16, 24, False),

            # Антитерроризм
            ('Антитеррористическая защищенность', 'ANTITERROR', 16, 24, False),
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
                self.stdout.write(self.style.SUCCESS(f'  Создана программа: {name}'))