from django.core.management.base import BaseCommand

from trainings.models import TrainingProgram, InstructionType


class Command(BaseCommand):
    help = 'Заполняет базу данных начальными программами обучения и типами инструктажей согласно требованиям.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начинаем настройку справочников обучения...')

        # ==========================================
        # 1. Программы обучения (Курсы / ДПО)
        # ==========================================

        # Список программ на основе вашего ТЗ
        programs_data = [
            {
                'name': 'Охрана труда для руководителей и специалистов',
                'training_type': 'SAFETY',
                'hours': 40,
                'frequency_months': 36,  # 1 раз в 3 года
                # False, т.к. назначаем только руководителям и комиссии (через
                # services.py)
                'is_mandatory': False,
                'defaults': {}
            },
            {
                'name': 'Электробезопасность (для всего персонала)',
                'training_type': 'OTHER',  # Используем OTHER или добавьте ELECTRICAL в choices модели
                'hours': 16,  # Стандартное кол-во часов, можно менять
                'frequency_months': 12,  # Каждый год
                'is_mandatory': True,  # True, так как обучают "весь персонал"
                'defaults': {}
            },
            {
                'name': 'Оказание первой помощи пострадавшим',
                'training_type': 'FIRST_AID',
                'hours': 8,
                'frequency_months': 12,  # Каждый год
                'is_mandatory': False,  # False, т.к. только руков., замы и педагоги
                'defaults': {}
            },
            {
                'name': 'Пожарная безопасность (для руководителей)',
                'training_type': 'FIRE',
                'hours': 16,
                'frequency_months': 60,  # 1 раз в 5 лет
                'is_mandatory': False,  # False, т.к. только руководители и замы
                'defaults': {}
            }
        ]

        for prog in programs_data:
            obj, created = TrainingProgram.objects.get_or_create(
                name=prog['name'],
                defaults={
                    'training_type': prog['training_type'],
                    'hours': prog['hours'],
                    'frequency_months': prog['frequency_months'],
                    'is_mandatory': prog['is_mandatory']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создана программа: {
                            obj.name}'))
            else:
                self.stdout.write(f'Программа уже существует: {obj.name}')

        # ==========================================
        # 2. Типы инструктажей
        # ==========================================

        instructions_data = [
            # --- Охрана труда ---
            {
                'name': 'Вводный инструктаж по охране труда',
                'category': 'SAFETY',
                'type_name': 'Вводный',
                'frequency_months': 0,  # Разовый
            },
            {
                'name': 'Первичный инструктаж по охране труда на рабочем месте',
                'category': 'SAFETY',
                'type_name': 'Первичный',
                # Обычно проводится один раз при приеме (или переводе)
                'frequency_months': 0,
            },
            {
                'name': 'Повторный инструктаж по охране труда',
                'category': 'SAFETY',
                'type_name': 'Повторный',
                'frequency_months': 6,  # Стандартно раз в 6 месяцев
            },

            # --- Пожарная безопасность ---
            {
                'name': 'Вводный инструктаж по пожарной безопасности',
                'category': 'FIRE',
                'type_name': 'Вводный',
                'frequency_months': 0,
            },
            {
                'name': 'Повторный инструктаж по пожарной безопасности',
                'category': 'FIRE',
                'type_name': 'Повторный',
                # Стандартно раз в 6 месяцев (или 12 для некоторых категорий)
                'frequency_months': 6,
            },

            # --- Электробезопасность (Инструктаж для неэлектротехнического персонала - 1 группа) ---
            {
                'name': 'Инструктаж по электробезопасности (1 группа)',
                'category': 'ELECTRICAL',
                'type_name': 'Ежегодный',
                'frequency_months': 12,
            },
        ]

        for instr in instructions_data:
            # Используем update_or_create, чтобы обновить параметры, если
            # запись уже есть
            obj, created = InstructionType.objects.get_or_create(
                category=instr['category'],
                type_name=instr['type_name'],
                defaults={
                    'name': instr['name'],
                    'frequency_months': instr['frequency_months']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создан тип инструктажа: {
                            obj.name}'))
            else:
                self.stdout.write(
                    f'Тип инструктажа уже существует: {
                        obj.name}')

        self.stdout.write(self.style.SUCCESS(
            '\nНастройка данных завершена успешно!'))
