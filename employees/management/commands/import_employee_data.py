import openpyxl
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from employees.models import Employee
from organization.models import Department, Position, OrganizationSafetyInfo


class Command(BaseCommand):
    help = 'Импортирует данные об организации и сотрудниках из Excel файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к Excel файлу')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"Не удалось открыть файл: {e}"))
            return

        # --- 1. Импорт данных организации ---
        if "Организация" in wb.sheetnames:
            self.stdout.write("Обработка данных организации...")
            ws_org = wb["Организация"]
            # Данные начинаются со 2-й строки
            rows = list(ws_org.iter_rows(min_row=2, values_only=True))
            if rows and any(rows[0]):
                org_data = rows[0]

                # В вашей модели OrganizationSafetyInfo нет поля КПП,
                # поэтому берем: Название(0), ИНН(1), ОГРН(3), Адрес(4), Телефон(5)
                # [cite: 3530, 3582]
                org_info, created = OrganizationSafetyInfo.objects.update_or_create(
                    pk=1,  # Обычно в системе одна запись с настройками организации
                    defaults={
                        'name_full': str(org_data[0]) if org_data[0] else '',
                        'inn': str(org_data[1]) if org_data[1] else '',
                        'ogrn': str(org_data[3]) if org_data[3] else '',
                        'address_legal': str(org_data[4]) if org_data[4] else '',
                        'contact_phone': str(org_data[5]) if org_data[5] else '',
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Данные организации {
                            'созданы' if created else 'обновлены'}."))

        # --- 2. Импорт сотрудников ---
        if "Сотрудники" in wb.sheetnames:
            self.stdout.write("Импорт сотрудников...")
            ws_emp = wb["Сотрудники"]
            emp_count = 0

            # Начинаем со второй строки (пропускаем заголовки)
            for row in ws_emp.iter_rows(min_row=2, values_only=True):
                # Если ячейка с фамилией пустая — пропускаем строку
                if not row[0]:
                    continue

                last_name, first_name, middle_name, pos_name, dept_name, b_date, h_date = row[:7]

                # 1. Получаем или создаем Подразделение
                dept = None
                if dept_name:
                    dept, _ = Department.objects.get_or_create(name=dept_name.strip())

                # 2. Получаем или создаем Должность, ПРИВЯЗАННУЮ к подразделению
                pos = None
                if pos_name:
                    # Важно: добавляем department=dept в поиск и создание
                    pos, _ = Position.objects.get_or_create(
                        name=pos_name.strip(),
                        department=dept  # Теперь должность привяжется к отделу
                    )

                # Вспомогательная функция для дат
                def parse_date(d):
                    if isinstance(d, datetime):
                        return d.date()
                    if d:
                        try:
                            return datetime.strptime(
                                str(d).split()[0], '%Y-%m-%d').date()
                        except BaseException:
                            return None
                    return None

                # 3. Создание или обновление сотрудника
                # [cite: 3472]
                employee, created = Employee.objects.update_or_create(
                    last_name=str(last_name).strip(),
                    first_name=str(first_name).strip(),
                    middle_name=str(middle_name or '').strip(),
                    defaults={
                        'department': dept,
                        'position': pos,
                        'birth_date': parse_date(b_date),
                        'hire_date': parse_date(h_date),
                        'is_active': True
                    }
                )
                emp_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Успешно импортировано сотрудников: {emp_count}"))
        else:
            self.stderr.write(self.style.WARNING(
                "Лист 'Сотрудники' не найден в файле."))

        self.stdout.write(self.style.SUCCESS("Импорт полностью завершен!"))
