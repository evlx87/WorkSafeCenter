# import openpyxl
# from django.core.management.base import BaseCommand
#
#
# class Command(BaseCommand):
#     help = 'Создает шаблон Excel (.xlsx) для последующего импорта данных о сотрудниках, отделах и должностях.'
#
#     def add_arguments(self, parser):
#         parser.add_argument(
#             'filename',
#             type=str,
#             nargs='?',
#             default='import_template.xlsx',
#             help='Имя файла для сохранения шаблона. По умолчанию "import_template.xlsx".'
#         )
#
#     def handle(self, *args, **kwargs):
#         filename = kwargs['filename']
#
#         # Создаем новую рабочую книгу Excel
#         wb = openpyxl.Workbook()
#
#         # Удаляем лист, созданный по умолчанию
#         if 'Sheet' in wb.sheetnames:
#             wb.remove(wb['Sheet'])
#
#         # --- Лист 1: Отделы ---
#         ws_deps = wb.create_sheet(title='Отделы')
#         ws_deps.append(['Название отдела', 'Описание'])
#         ws_deps.column_dimensions['A'].width = 40
#         ws_deps.column_dimensions['B'].width = 60
#
#         # --- Лист 2: Должности ---
#         ws_pos = wb.create_sheet(title='Должности')
#         ws_pos.append(['Название должности', 'Описание', 'Название отдела'])
#         ws_pos.column_dimensions['A'].width = 40
#         ws_pos.column_dimensions['B'].width = 60
#         ws_pos.column_dimensions['C'].width = 40
#
#         # --- Лист 3: Сотрудники ---
#         ws_emps = wb.create_sheet(title='Сотрудники')
#         ws_emps.append([
#             'Фамилия', 'Имя', 'Отчество', 'Email', 'Телефон',
#             'Дата рождения (ГГГГ-ММ-ДД)', 'Дата найма (ГГГГ-ММ-ДД)',
#             'Название должности', 'Название отдела'
#         ])
#         for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
#             ws_emps.column_dimensions[col].width = 25
#
#         # Сохраняем файл
#         try:
#             wb.save(filename)
#             self.stdout.write(
#                 self.style.SUCCESS(
#                     f'Шаблон успешно создан и сохранен в файл "{filename}"'))
#         except Exception as e:
#             self.stderr.write(
#                 self.style.ERROR(
#                     f'Произошла ошибка при сохранении файла: {e}'))
import openpyxl
from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Генерирует Excel шаблон для импорта данных организации и сотрудников'

    def handle(self, *args, **options):
        wb = openpyxl.Workbook()

        # --- Лист 1: Организация ---
        ws_org = wb.active
        ws_org.title = "Организация"

        # Заголовки на основе вашей модели OrganizationSafetyInfo и переменных
        # из .env
        org_headers = [
            'Полное наименование',
            'ИНН',
            'КПП',
            'ОГРН',
            'Юридический адрес',
            'Контактный телефон'
        ]
        ws_org.append(org_headers)

        # Попробуем предзаполнить данными из текущих переменных окружения (если
        # они есть)
        ws_org.append([
            os.getenv('ORG_NAME_FULL', ''),
            os.getenv('ORG_INN', ''),
            os.getenv('ORG_KPP', ''),
            os.getenv('ORG_OGRN', ''),
            os.getenv('ORG_ADDRESS_LEGAL', ''),
            os.getenv('ORG_CONTACT_PHONE', '')
        ])

        # --- Лист 2: Сотрудники ---
        ws_emp = wb.create_sheet(title="Сотрудники")

        # Заголовки на основе вашей модели Employee (исключая "Пол")
        emp_headers = [
            'Фамилия',
            'Имя',
            'Отчество',
            'Должность',
            'Подразделение',
            'Дата рождения (ГГГГ-ММ-ДД)',
            'Дата приема (ГГГГ-ММ-ДД)'
        ]
        ws_emp.append(emp_headers)

        # Пример данных
        ws_emp.append(['Иванов', 'Иван', 'Иванович', 'Директор',
                      'Администрация', '1980-01-01', '2023-01-10'])

        filename = 'import_template.xlsx'
        try:
            wb.save(filename)
            self.stdout.write(self.style.SUCCESS(
                f'Шаблон успешно создан и сохранен в файл "{filename}".\n'
                f'Теперь вы можете заполнить его и использовать для импорта.'
            ))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f'Ошибка при сохранении файла: {e}'))
