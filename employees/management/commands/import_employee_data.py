import os

import openpyxl
from django.core.files import File
from django.core.management.base import BaseCommand

from employees.models import Employee
from organization.models import OrganizationSafetyInfo, Site, Department, Position
from trainings.models import TrainingProgram, Training


class Command(BaseCommand):
    help = 'Полный импорт структуры организации, сотрудников и обучения со сканами'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)
        parser.add_argument(
            '--scans-dir',
            type=str,
            help='Папка с PDF-файлами удостоверений')

    def handle(self, *args, **options):
        path = options['file_path']
        scans_dir = options.get('scans-dir')
        wb = openpyxl.load_workbook(path)

        # 0. Организация (Обновляем синглтон)
        ws_org = wb["0. Организация"]
        for row in ws_org.iter_rows(min_row=2, values_only=True):
            if row[0]:
                OrganizationSafetyInfo.objects.update_or_create(
                    pk=1,
                    defaults={
                        'name_full': row[0],
                        'name_short': row[1],
                        'inn': row[2],
                        'kpp': row[3],
                        'ogrn': row[4],
                        'address_legal': row[5],
                        'director_fio': row[6],
                        'ot_responsible_fio': row[7]})

        # 1. Площадки
        ws_sites = wb["1. Площадки"]
        org = OrganizationSafetyInfo.load_organization()
        for row in ws_sites.iter_rows(min_row=2, values_only=True):
            if row[0]:
                Site.objects.get_or_create(
                    name=row[0], organization=org,
                    defaults={'address': row[1], 'ot_responsible_name': row[2]}
                )

        # 2. Подразделения (с учетом иерархии)
        ws_deps = wb["2. Подразделения"]
        for row in ws_deps.iter_rows(min_row=2, values_only=True):
            if row[0]:
                parent = Department.objects.filter(
                    name=row[2]).first() if row[2] else None
                Department.objects.get_or_create(
                    name=row[0],
                    defaults={'description': row[1] or '', 'parent': parent}
                )

        # 3. Должности
        ws_pos = wb["3. Должности"]
        for row in ws_pos.iter_rows(min_row=2, values_only=True):
            if row[0]:
                dept = Department.objects.filter(name=row[1]).first()
                Position.objects.get_or_create(
                    name=row[0], department=dept,
                    defaults={'description': row[2] or ''}
                )

        # 4. Программы обучения
        ws_prog = wb["4. Программы"]
        for row in ws_prog.iter_rows(min_row=2, values_only=True):
            if row[0]:
                TrainingProgram.objects.get_or_create(
                    name=row[0],
                    defaults={
                        'training_type': row[1],
                        'hours': row[2] or 0,
                        'frequency_months': row[3] or 12,
                        'is_mandatory': str(
                            row[4]).lower() == 'да'})

        # 5. Сотрудники
        ws_emp = wb["5. Сотрудники"]
        for row in ws_emp.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            pos = Position.objects.filter(name=row[3]).first()
            dept = Department.objects.filter(name=row[4]).first()
            Employee.objects.update_or_create(
                last_name=row[0],
                first_name=row[1],
                middle_name=row[2],
                defaults={
                    'position': pos,
                    'department': dept,
                    'birth_date': row[5],
                    'hire_date': row[6],
                    'phone': row[7],
                    'email': row[8],
                    'is_executive': str(
                        row[9]).lower() == 'да',
                    'is_safety_specialist': str(
                        row[10]).lower() == 'да',
                    'is_safety_committee_member': str(
                        row[11]).lower() == 'да',
                    'is_safety_committee_chair': str(
                        row[12]).lower() == 'да',
                    'exempt_from_safety_instruction': str(
                            row[13]).lower() == 'да'})

        # 6. Обучение и Сканы
        ws_train = wb["6. Обучение"]
        for row in ws_train.iter_rows(min_row=2, values_only=True):
            fio, prog_name, t_date, prot, cert, scan_file = row
            if not fio:
                continue

            names = fio.split()
            emp = Employee.objects.filter(
                last_name=names[0], first_name=names[1]).first()
            prog = TrainingProgram.objects.filter(name=prog_name).first()

            if emp and prog:
                training, _ = Training.objects.get_or_create(
                    employee=emp, program=prog, training_date=t_date, defaults={
                        'protocol_number': prot, 'certificate_number': cert})

                # Загрузка файла из папки
                if scan_file and scans_dir:
                    file_path = os.path.join(scans_dir, scan_file)
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            # В вашей модели Training поле называется file
                            training.document_scan.save(scan_file, File(f), save=True)
                        self.stdout.write(
                            f"Файл {scan_file} загружен для {fio}")

        self.stdout.write(self.style.SUCCESS(
            'Импорт всей структуры базы данных успешно завершен!'))
