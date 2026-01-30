import openpyxl
from django.core.management.base import BaseCommand
from openpyxl.styles import Font, PatternFill


class Command(BaseCommand):
    help = 'Создает максимально полный Excel-шаблон для заполнения всей БД'

    def handle(self, *args, **options):
        wb = openpyxl.Workbook()

        # 0. Реквизиты организации (OrganizationSafetyInfo)
        ws0 = wb.active
        ws0.title = "0. Организация"
        ws0.append([
            'Полное название', 'Сокращенное название', 'ИНН', 'КПП', 'ОГРН',
            'Юр. адрес', 'ФИО Директора', 'ФИО ответственного за ОТ'
        ])

        # 1. Площадки (Site)
        ws1 = wb.create_sheet("1. Площадки")
        ws1.append(
            ['Название площадки', 'Адрес площадки', 'Ответственный (ФИО)'])

        # 2. Подразделения (Department)
        ws2 = wb.create_sheet("2. Подразделения")
        ws2.append(['Название отдела', 'Описание',
                   'Вышестоящий отдел (Название)'])

        # 3. Должности (Position)
        ws3 = wb.create_sheet("3. Должности")
        ws3.append(['Название должности', 'Отдел', 'Описание'])

        # 4. Программы обучения (TrainingProgram)
        ws4 = wb.create_sheet("4. Программы")
        ws4.append(['Название программы', 'Тип (SAFETY/FIRE/etc)',
                    'Часы', 'Периодичность (мес)', 'Обязательна (Да/Нет)'])

        # 5. Сотрудники (Employee)
        ws5 = wb.create_sheet("5. Сотрудники")
        ws5.append(['Фамилия',
                    'Имя',
                    'Отчество',
                    'Должность',
                    'Отдел',
                    'Дата рождения (ГГГГ-ММ-ДД)',
                    'Дата приема',
                    'Телефон',
                    'Email',
                    'Руководитель (Да/Нет)',
                    'Спец. по ОТ (Да/Нет)',
                    'Член комиссии (Да/Нет)',
                    'Председатель комиссии (Да/Нет)',
                    'Освобожден от инструктажей (Да/Нет)'])

        # 6. Пройденное обучение (Training)
        ws6 = wb.create_sheet("6. Обучение")
        ws6.append(['ФИО Сотрудника (Полностью)',
                    'Название программы',
                    'Дата обучения',
                    'Номер протокола',
                    'Номер удостоверения',
                    'Имя файла скана (ivanov_doc.pdf)'])

        # Стилизация
        header_fill = PatternFill(start_color="D9EAD3", fill_type="solid")
        header_font = Font(bold=True)
        for sheet in wb.worksheets:
            for cell in sheet[1]:
                cell.fill = header_fill
                cell.font = header_font
            for col in sheet.columns:
                sheet.column_dimensions[col[0].column_letter].width = 25

        filename = 'full_system_template.xlsx'
        wb.save(filename)
        self.stdout.write(
            self.style.SUCCESS(
                f'Создан полный шаблон: {filename}'))
