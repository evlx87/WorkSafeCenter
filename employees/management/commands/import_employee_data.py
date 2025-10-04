import openpyxl
from django.core.management.base import BaseCommand
from django.db import transaction

from employees.models import Employee
from organization.models import Department, Position


class Command(BaseCommand):
    help = 'Импортирует данные о сотрудниках, отделах и должностях из файла Excel (.xlsx).'

    def add_arguments(self, parser):
        parser.add_argument(
            'filename',
            type=str,
            help='Путь к файлу Excel для импорта.')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        filename = kwargs['filename']

        try:
            wb = openpyxl.load_workbook(filename)
        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(
                    f'Файл "{filename}" не найден.'))
            return

        # --- 1. Импорт Отделов ---
        self.stdout.write('Импорт отделов...')
        ws_deps = wb['Отделы']
        for row_idx, row in enumerate(ws_deps.iter_rows(
                min_row=2, values_only=True), start=2):
            name, description = row
            if not name:
                continue
            dept, created = Department.objects.update_or_create(
                name=name.strip(),
                defaults={
                    'description': description.strip() if description else ''}
            )
            if created:
                self.stdout.write(f'  - Создан отдел: {dept.name}')
        self.stdout.write(self.style.SUCCESS('Импорт отделов завершен.'))

        # --- 2. Импорт Должностей ---
        self.stdout.write('\nИмпорт должностей...')
        ws_pos = wb['Должности']
        for row_idx, row in enumerate(ws_pos.iter_rows(
                min_row=2, values_only=True), start=2):
            name, description, dept_name = row
            if not name:
                continue
            try:
                department = Department.objects.get(name=dept_name.strip())
                pos, created = Position.objects.update_or_create(
                    name=name.strip(),
                    defaults={
                        'description': description.strip() if description else '',
                        'department': department
                    }
                )
                if created:
                    self.stdout.write(f'  - Создана должность: {pos.name}')
            except Department.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f'Ошибка в листе "Должности" (строка {row_idx}): отдел "{dept_name}" не найден. Пропустили.'))
                continue
        self.stdout.write(self.style.SUCCESS('Импорт должностей завершен.'))

        # --- 3. Импорт Сотрудников ---
        self.stdout.write('\nИмпорт сотрудников...')
        ws_emps = wb['Сотрудники']
        for row_idx, row in enumerate(ws_emps.iter_rows(
                min_row=2, values_only=True), start=2):
            last_name, first_name, middle_name, email, phone, birth_date, hire_date, pos_name, dept_name = row
            if not email and not (last_name and first_name):
                continue

            try:
                position = Position.objects.get(name=pos_name.strip())
                department = Department.objects.get(name=dept_name.strip())

                defaults = {
                    'first_name': first_name.strip(),
                    'last_name': last_name.strip(),
                    'middle_name': middle_name.strip() if middle_name else '',
                    'phone': phone if phone else '',
                    'birth_date': birth_date,
                    'hire_date': hire_date,
                    'position': position,
                    'department': department,
                    'is_active': True
                }

                # Используем email как уникальный идентификатор
                emp, created = Employee.objects.update_or_create(
                    email=email.strip() if email else None,
                    defaults=defaults
                )

                if created:
                    self.stdout.write(f'  - Создан сотрудник: {emp}')

            except Position.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f'Ошибка в листе "Сотрудники" (строка {row_idx}): должность "{pos_name}" не найдена. Пропустили.'))
            except Department.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f'Ошибка в листе "Сотрудники" (строка {row_idx}): отдел "{dept_name}" не найден. Пропустили.'))
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f'Неизвестная ошибка в листе "Сотрудники" (строка {row_idx}): {e}. Пропустили.'))

        self.stdout.write(self.style.SUCCESS('Импорт сотрудников завершен.'))
        self.stdout.write(self.style.SUCCESS(
            '\nВсе операции успешно выполнены!'))
