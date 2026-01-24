import openpyxl
from django.core.management.base import BaseCommand

from employees.models import Employee
from trainings.models import TrainingProgram, Training


class Command(BaseCommand):
    help = 'Импортирует данные из расширенного Excel шаблона'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к файлу Excel')

    def handle(self, *args, **options):
        path = options['file_path']
        try:
            wb = openpyxl.load_workbook(path)
        except Exception as e:
            self.stderr.write(f"Ошибка открытия файла: {e}")
            return

        if "Программы обучения" in wb.sheetnames:
            self.stdout.write("Импорт программ обучения...")
            ws = wb["Программы обучения"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[0]:
                    continue

                TrainingProgram.objects.get_or_create(
                    name=row[0], defaults={
                        'training_type': row[1] if row[1] else 'OTHER', 'hours': int(
                            row[2]) if row[2] else 0, 'frequency_months': int(
                            row[3]) if row[3] else 0, 'is_mandatory': True if str(
                            row[4]).lower() in [
                            'да', 'yes', '1'] else False})

        if "Обучение сотрудников" in wb.sheetnames:
            self.stdout.write("Импорт записей об обучении...")
            ws = wb["Обучение сотрудников"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                fio, prog_name, t_date, prot_num, cert_num = row
                if not fio or not prog_name:
                    continue

                parts = str(fio).split()
                emp = Employee.objects.filter(
                    last_name=parts[0],
                    first_name=parts[1] if len(parts) > 1 else ""
                ).first()

                prog = TrainingProgram.objects.filter(name=prog_name).first()

                if emp and prog:
                    Training.objects.get_or_create(
                        employee=emp,
                        program=prog,
                        training_date=t_date,
                        defaults={
                            'protocol_number': str(prot_num) if prot_num else '',
                            'certificate_number': str(cert_num) if cert_num else ''})
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Не найден сотрудник или программа для: {fio} / {prog_name}"))

        self.stdout.write(self.style.SUCCESS("Импорт успешно завершен!"))
