import os

import openpyxl
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.dateparse import parse_date

from employees.models import Employee
from organization.models import OrganizationSafetyInfo, Site, Department, Position
from trainings.models import TrainingProgram, Training, Instruction, InstructionType, ProgramNameMapping, \
    TrainingCategory


class Command(BaseCommand):
    help = 'Импорт данных организации и сотрудников из Excel файла (корректная структура)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к Excel файлу')
        parser.add_argument(
            '--scans-dir',
            type=str,
            help='Папка с PDF-файлами удостоверений и сканов'
        )

    def _parse_date(self, value):
        """Безопасный парсинг даты из разных форматов"""
        if not value:
            return None
        try:
            if isinstance(value, str):
                return parse_date(value)
            return value.date() if hasattr(value, 'date') else value
        except BaseException:
            return None

    def handle(self, *args, **options):
        path = options['file_path']
        scans_dir = options.get('scans-dir')

        if not os.path.exists(path):
            raise CommandError(f'Файл не найден: {path}')

        try:
            wb = openpyxl.load_workbook(path)
        except Exception as e:
            raise CommandError(f'Ошибка открытия Excel файла: {e}')

        # ==========================================
        # 0. Организация (ТОЛЬКО существующие поля модели)
        # ==========================================
        try:
            ws_org = wb["0. Организация"]
            for row in ws_org.iter_rows(min_row=2, values_only=True):
                if row[0]:  # Полное название
                    # Читаем ТОЛЬКО существующие поля модели
                    defaults = {
                        'name_full': str(row[0]).strip() if row[0] else '',
                        'inn': str(row[1]).strip() if len(row) > 1 and row[1] else '',
                        'kpp': str(row[2]).strip() if len(row) > 2 and row[2] else '',
                        'ogrn': str(row[3]).strip() if len(row) > 3 and row[3] else '',
                        'address_legal': str(row[4]).strip() if len(row) > 4 and row[4] else '',
                        'contact_phone': str(row[5]).strip()[:20] if len(row) > 5 and row[5] else '',
                        # Обрезаем до 20 символов
                    }

                    # Используем метод синглтона
                    org = OrganizationSafetyInfo.load_organization()
                    for key, value in defaults.items():
                        setattr(org, key, value)
                    org.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Организация: {
                                row[0]}'))
                    break
        except KeyError:
            self.stdout.write(self.style.WARNING(
                '⚠️ Лист "0. Организация" не найден — пропускаем'))

        # ==========================================
        # 1. Площадки
        # ==========================================
        org = OrganizationSafetyInfo.load_organization()
        sites_created = 0
        try:
            ws_sites = wb["1. Площадки"]
            for row in ws_sites.iter_rows(min_row=2, values_only=True):
                if row[0] and org:
                    Site.objects.get_or_create(
                        name=str(
                            row[0]).strip(), organization=org, defaults={
                            'address': str(
                                row[1]).strip() if len(row) > 1 and row[1] else '', 'ot_responsible_name': str(
                                row[2]).strip() if len(row) > 2 and row[2] else ''})
                    sites_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Площадки: {sites_created} шт.'))
        except KeyError:
            self.stdout.write(self.style.WARNING(
                '⚠️ Лист "1. Площадки" не найден — пропускаем'))

        # ==========================================
        # 2. Подразделения
        # ==========================================
        deps_created = 0
        try:
            ws_deps = wb["2. Подразделения"]
            for row in ws_deps.iter_rows(min_row=2, values_only=True):
                if row[0]:
                    parent = None
                    if len(row) > 2 and row[2]:
                        parent = Department.objects.filter(
                            name=str(row[2]).strip()).first()

                    dept, created = Department.objects.get_or_create(
                        name=str(row[0]).strip(),
                        defaults={
                            'description': str(row[1]).strip() if len(row) > 1 and row[1] else '',
                            'parent': parent
                        }
                    )
                    if created:
                        deps_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Подразделения: {deps_created} шт.'))
        except KeyError:
            self.stdout.write(self.style.WARNING(
                '⚠️ Лист "2. Подразделения" не найден — пропускаем'))

        # ==========================================
        # 3. Должности
        # ==========================================
        pos_created = 0
        try:
            ws_pos = wb["3. Должности"]
            for row in ws_pos.iter_rows(min_row=2, values_only=True):
                if row[0]:
                    dept = None
                    if len(row) > 1 and row[1]:
                        dept = Department.objects.filter(
                            name=str(row[1]).strip()).first()

                    pos, created = Position.objects.get_or_create(
                        name=str(
                            row[0]).strip(), defaults={
                            'department': dept, 'description': str(
                                row[2]).strip() if len(row) > 2 and row[2] else ''})
                    if created:
                        pos_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Должности: {pos_created} шт.'))
        except KeyError:
            self.stdout.write(self.style.WARNING(
                '⚠️ Лист "3. Должности" не найден — пропускаем'))

        # ==========================================
        # 4. Сотрудники
        # ==========================================
        emp_created = 0
        emp_updated = 0
        employees_by_fio = {}  # Для последующей привязки инструктажей и обучения

        try:
            ws_emp = wb["4. Сотрудники"]
            for row in ws_emp.iter_rows(min_row=2, values_only=True):
                if not row[0] or not row[2]:
                    continue

                # Парсинг дат
                birth_date = self._parse_date(
                    row[6]) if len(row) > 6 else None
                hire_date = self._parse_date(
                    row[7]) if len(row) > 7 else None
                termination_date = self._parse_date(
                    row[18]) if len(row) > 18 else None

                # Поиск должности и отдела
                position = None
                if len(row) > 4 and row[4]:
                    position = Position.objects.filter(
                        name=str(row[4]).strip()).first()

                department = None
                if len(row) > 5 and row[5]:
                    department = Department.objects.filter(
                        name=str(row[5]).strip()).first()

                # Создание/обновление сотрудника
                emp, created = Employee.objects.update_or_create(
                    last_name=str(row[0]).strip(),
                    first_name=str(row[2]).strip(),
                    defaults={
                        'middle_name': str(row[3]).strip() if len(row) > 3 and row[3] else '',
                        'previous_last_name': str(row[1]).strip() if len(row) > 1 and row[1] else '',
                        'position': position,
                        'department': department,
                        'birth_date': birth_date,
                        'hire_date': hire_date,
                        'phone': str(row[8]).strip() if len(row) > 8 and row[8] else '',
                        'email': str(row[9]).strip() if len(row) > 9 and row[9] else '',
                        'is_executive': str(row[10]).strip().lower() == 'да' if len(row) > 10 and row[10] else False,
                        'is_pedagogical': str(row[11]).strip().lower() == 'да' if len(row) > 11 and row[11] else False,
                        'is_safety_specialist': str(row[12]).strip().lower() == 'да' if len(row) > 12 and row[12] else False,
                        'is_safety_committee_member': str(row[13]).strip().lower() == 'да' if len(row) > 13 and row[
                            13] else False,
                        'is_safety_committee_chair': str(row[14]).strip().lower() == 'да' if len(row) > 14 and row[
                            14] else False,
                        'is_acting_director': str(row[15]).strip().lower() == 'да' if len(row) > 15 and row[
                            15] else False,
                        'exempt_from_safety_instruction': str(row[16]).strip().lower() == 'да' if len(row) > 16 and row[
                            16] else False,
                        'on_parental_leave': str(row[17]).strip().lower() == 'да' if len(row) > 17 and row[
                            17] else False,
                        'termination_date': termination_date,
                        'termination_order_number': str(row[19]).strip() if len(row) > 19 and row[19] else '',
                        'is_active': termination_date is None,
                    }
                )

                # Сохраняем для последующей привязки по ФИО
                fio_key = f"{
                    emp.last_name} {
                    emp.first_name} {
                    emp.middle_name}".strip()
                employees_by_fio[fio_key] = emp

                if created:
                    emp_created += 1
                else:
                    emp_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Сотрудники: {emp_created} новых, {emp_updated} обновлено'))
        except KeyError:
            raise CommandError(
                '❌ Критическая ошибка: Лист "4. Сотрудники" не найден!')
        # ==========================================
        # 5. Программы обучения
        # ==========================================
        prog_created = 0
        try:
            ws_prog = wb["5. Программы"]
            for row in ws_prog.iter_rows(min_row=2, values_only=True):
                if not row[0]:
                    continue

                # 1. Получаем код из Excel (например, 'SAFETY', 'FIRE')
                raw_category = str(row[1]).strip() if row[1] else 'OTHER'

                # Словарик для человеческих названий (если категории еще нет в базе)
                category_names = {
                    'SAFETY': 'Охрана труда',
                    'FIRE': 'Пожарная безопасность',
                    'FIRST_AID': 'Первая помощь',
                    'ELECTRICAL': 'Электробезопасность',
                    'ANTITERROR': 'Антитеррористическая защищенность',
                    'OTHER': 'Прочее'
                }

                # 2. Находим или создаем категорию, указывая ОБЯЗАТЕЛЬНО field 'code'
                # В вашей модели поле называется 'code' (судя по ошибке trainings_trainingcategory_code_key)
                category_obj, _ = TrainingCategory.objects.get_or_create(
                    code=raw_category,
                    defaults={'name': category_names.get(raw_category, raw_category)}
                )

                # 3. Создаем программу
                prog, created = TrainingProgram.objects.get_or_create(
                    name=str(row[0]).strip(),
                    defaults={
                        'category': category_obj,
                        'hours': int(row[2]) if len(row) > 2 and row[2] else 8,
                        'frequency_months': int(row[3]) if len(row) > 3 and row[3] else 12,
                        'is_mandatory': str(row[4]).strip().lower() == 'да' if len(row) > 4 and row[4] else False
                    }
                )
                if created:
                    prog_created += 1
            self.stdout.write(self.style.SUCCESS(f'✅ Программы обучения: {prog_created} шт.'))
        except KeyError:
            self.stdout.write(self.style.WARNING('⚠️ Лист "5. Программы" не найден'))

        # ==========================================
        # 6. Автоматическое назначение директора и спец. по ОТ
        # ==========================================
        if org:
            # Директор: ищем сотрудника с должностью "Директор" или флагом И.о.
            # директора
            director = None

            # 1. Сначала ищем сотрудника с точным названием должности
            # "Директор"
            director_position = Position.objects.filter(
                name__iexact='Директор'
            ).first()

            if director_position:
                director = Employee.objects.filter(
                    is_active=True,
                    position=director_position
                ).order_by('hire_date').first()

            # 2. Если не найден, ищем сотрудника с флагом "И.о. директора"
            if not director:
                director = Employee.objects.filter(
                    is_active=True,
                    is_acting_director=True
                ).order_by('hire_date').first()

            if director:
                org.director = director
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Назначен директор: {director.last_name} {director.first_name} '
                    f'({director.position.name if director.position else "И.о. директора"})'
                ))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️ Директор не найден. Проверьте, что в списке сотрудников есть '
                        'сотрудник с должностью "Директор" или флагом "И.о. директора"'))

            # Специалист по ОТ: первый активный сотрудник со статусом спец. по
            # ОТ
            specialist = Employee.objects.filter(
                is_active=True,
                is_safety_specialist=True
            ).first()

            if specialist:
                org.safety_specialist = specialist
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Назначен спец. по ОТ: {
                            specialist.last_name} {
                            specialist.first_name}'))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️ Специалист по ОТ не найден. Проверьте, что в списке сотрудников '
                        'есть сотрудник с флагом "Специалист по ОТ"'))

            org.save()

        # ==========================================
        # 7. Обучение
        # ==========================================
        train_created = 0
        try:
            ws_train = wb["6. Обучение"]
            for row in ws_train.iter_rows(min_row=2, values_only=True):
                if not row[0] or not row[3]:  # Требуется ФИО и Название программы
                    continue

                # Поиск сотрудника ПО ФИО с учетом предыдущей фамилии
                fio_parts = str(row[0]).strip().split()
                if len(fio_parts) < 2:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️ Некорректный формат ФИО: "{row[0]}"'))
                    continue

                ln = fio_parts[0].strip()  # Фамилия
                fn = fio_parts[1].strip()  # Имя
                mn = fio_parts[2].strip() if len(
                    fio_parts) > 2 else ''  # Отчество

                # ПОИСК ПО ТЕКУЩЕЙ ИЛИ ПРЕДЫДУЩЕЙ ФАМИЛИИ
                emp = Employee.objects.filter(
                    Q(last_name__iexact=ln) | Q(previous_last_name__iexact=ln),
                    first_name__iexact=fn,
                    middle_name__iexact=mn
                ).first()

                if not emp:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️ Сотрудник "{
                                row[0]}" не найден'))
                    continue

                # --- 7.2. Получаем данные из строки Excel ---
                category_raw = str(
                    row[1]).strip().lower() if row[1] else 'другое'
                doc_type_raw = str(row[2]).strip().lower() if row[2] else ''
                program_name_in_doc = str(
                    row[3]).strip()  # ТО, ЧТО НАПИСАНО В БУМАГЕ
                train_date = self._parse_date(row[4])
                doc_number = str(row[5]).strip() if len(
                    row) > 5 and row[5] else ''

                if not train_date:
                    continue

                # --- 7.3. Маппинг (Связываем "кривое" название с "правильной" группой) ---

                # Маппинг категорий
                category_map = {
                    'от': 'SAFETY', 'охрана труда': 'SAFETY',
                    'пб': 'FIRE', 'пожарная безопасность': 'FIRE',
                    'эб': 'ELECTRICAL', 'электробезопасность': 'ELECTRICAL',
                    'первая помощь': 'FIRST_AID',
                    'антитерроризм': 'ANTITERROR',
                }
                category_code = category_map.get(category_raw, 'OTHER')

                # Пытаемся найти сопоставление в вашей новой таблице
                # ProgramNameMapping
                mapping = ProgramNameMapping.objects.filter(
                    variant_name__iexact=program_name_in_doc,
                    is_active=True
                ).first()

                if mapping and mapping.standard_program:
                    # Если нашли в справочнике — берем эталонную программу
                    # (группу)
                    training_program = mapping.standard_program
                else:
                    # Если в справочнике нет, ищем программу с точно таким же
                    # названием
                    training_program = TrainingProgram.objects.filter(
                        name__iexact=program_name_in_doc
                    ).first()

                # Если вообще ничего не нашли — создадим предупреждение,
                # но запись создадим (хотя сроки могут считаться неверно без
                # группы)
                if not training_program:
                    self.stdout.write(self.style.ERROR(
                        f'❌ Не удалось подобрать группу для: "{program_name_in_doc}". '
                        f'Добавьте это название в ProgramNameMapping в админке!'
                    ))

                # --- 7.4. Сохранение записи ---

                # Маппинг типа документа (проверьте, что в модели Training поле называется document_type)
                doc_type_map = {
                    'протокол': 'PROTOCOL',
                    'удостоверение': 'CERT_QUAL',
                    'сертификат': 'CERT_COMPL',
                    'диплом': 'DIPLOMA'
                }

                # Используем update_or_create, чтобы не дублировать записи
                training, created = Training.objects.update_or_create(
                    employee=emp,
                    training_date=train_date,
                    program=training_program,  # Ссылка на TrainingProgram
                    defaults={
                        # ВАЖНО: используем raw_program_name, как в вашей модели
                        'raw_program_name': program_name_in_doc,
                        'document_type': doc_type_map.get(doc_type_raw, 'OTHER'),
                        'document_number': doc_number,
                        # Поле training_category убираем, так как его нет в модели Training
                    }
                )

                # --- 7.5. Загрузка скана (если есть) ---
                if scans_dir and len(row) > 6 and row[6]:
                    scan_file = str(row[6]).strip()
                    file_path = os.path.join(scans_dir, scan_file)
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            training.document_scan.save(
                                scan_file, File(f), save=True)

                if created:
                    train_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Обучение: загружено {train_created} записей'))

        except KeyError:
            self.stdout.write(self.style.WARNING(
                'ℹ️ Лист "6. Обучение" не найден'))
