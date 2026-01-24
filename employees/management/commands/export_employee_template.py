import openpyxl
from django.core.management.base import BaseCommand
from openpyxl.styles import Font, PatternFill


class Command(BaseCommand):
    help = 'Генерирует расширенный Excel шаблон для импорта данных'

    def handle(self, *args, **options):
        wb = openpyxl.Workbook()

        # --- Лист 1: Организация ---
        ws_org = wb.active
        ws_org.title = "Организация"
        ws_org.append(['Полное наименование', 'ИНН', 'КПП',
                      'ОГРН', 'Юридический адрес', 'Контактный телефон'])

        # --- Лист 2: Сотрудники ---
        ws_emps = wb.create_sheet(title='Сотрудники')
        ws_emps.append([
            'Фамилия', 'Имя', 'Отчество', 'Должность', 'Подразделение',
            'Дата рождения (ГГГГ-ММ-ДД)', 'Дата найма', 'Email', 'Телефон'
        ])

        # --- Лист 3: Программы обучения ---
        ws_progs = wb.create_sheet(title='Программы обучения')
        # Поля на основе модели TrainingProgram
        ws_progs.append([
            'Название программы', 'Тип (SAFETY/FIRE/ELECTRICAL/FIRST_AID)',
            'Часов', 'Периодичность (мес)', 'Обязательно (Да/Нет)'
        ])

        # --- Лист 4: Пройденное обучение ---
        ws_trainings = wb.create_sheet(title='Обучение сотрудников')
        # Поля на основе модели Training [cite: 2324, 2342]
        ws_trainings.append([
            'ФИО Сотрудника (Фамилия Имя Отчество)', 'Название программы',
            'Дата обучения (ГГГГ-ММ-ДД)', 'Номер протокола', 'Номер удостоверения'
        ])

        # Стилизация заголовков для всех листов
        header_fill = PatternFill(start_color="D3D3D3", fill_type="solid")
        header_font = Font(bold=True)
        for sheet in wb.sheetnames:
            for cell in wb[sheet][1]:
                cell.fill = header_fill
                cell.font = header_font
            # Авто-ширина колонок (примерная)
            for col in wb[sheet].columns:
                wb[sheet].column_dimensions[col[0].column_letter].width = 20

        filename = 'export_employee_template.xlsx'
        wb.save(filename)
        self.stdout.write(
            self.style.SUCCESS(
                f'Шаблон успешно создан: {filename}'))
