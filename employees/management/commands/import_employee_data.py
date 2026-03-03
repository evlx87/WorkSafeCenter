import os
from datetime import datetime

import openpyxl
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.dateparse import parse_date

from employees.models import Employee
from organization.models import OrganizationSafetyInfo, Site, Department, Position
from trainings.models import TrainingProgram, Training, TrainingCategory


class Command(BaseCommand):
    help = 'Импорт данных организации и сотрудников из Excel файла (с интерактивным режимом)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к Excel файлу')
        parser.add_argument(
            '--scans-dir',
            type=str,
            help='Папка с PDF-файлами удостоверений и сканов'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Режим проверки без сохранения изменений'
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Интерактивный режим: спрашивать что делать при ошибках'
        )
        parser.add_argument(
            '--auto-create-employees',
            action='store_true',
            help='Автоматически создавать отсутствующих сотрудников (без вопросов)')

    def _parse_date(self, value):
        """Безопасный парсинг даты из разных форматов Excel"""
        if not value:
            return None
        try:
            if isinstance(value, datetime):
                return value.date()
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
                date_formats = [
                    '%Y-%m-%d',
                    '%d.%m.%Y',
                    '%d-%m-%Y',
                    '%Y/%m/%d',
                    '%d/%m/%Y']
                for fmt in date_formats:
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue
                return parse_date(value)
            if isinstance(value, (int, float)):
                from datetime import timedelta
                excel_epoch = datetime(1899, 12, 30)
                return (excel_epoch + timedelta(days=value)).date()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ Не удалось распарсить дату: {value} ({e})'))
            return None
        return None

    def _parse_boolean(self, value):
        """Безопасный парсинг булевых значений"""
        if not value:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return str(value).strip().lower() in (
                'да', 'yes', 'true', '1', '+')
        return bool(value)

    def _get_cell_value(self, row, index, default=None):
        """Безопасное получение значения ячейки"""
        try:
            if len(row) > index and row[index] is not None:
                value = row[index]
                if isinstance(value, str):
                    return value.strip() if value.strip() else default
                return value
            return default
        except Exception:
            return default

    def _find_or_create_program(
            self,
            program_name_raw,
            category_code,
            dry_run=False):
        """
        Умный поиск программы с ОБЯЗАТЕЛЬНЫМ ограничением длины имени
        """
        if not program_name_raw:
            return None

        program_name_raw = str(program_name_raw).strip()
        program_name_safe = program_name_raw[:255] if len(
            program_name_raw) > 255 else program_name_raw

        # 1. Точный поиск
        program = TrainingProgram.objects.filter(
            name__iexact=program_name_safe).first()
        if program:
            return program

        # 2. Поиск по ключевым словам
        keywords_map = {
            'SAFETY': ['охрана труда', 'сут', 'безопасность труда'],
            'FIRE': ['пожарная безопасность', 'пожарно-технический', 'пб'],
            'FIRST_AID': ['первая помощь', 'мед. помощь'],
            'ELECTRICAL': ['электробезопасность', 'пуэ', 'потэу', 'птээп', 'группа'],
            'ANTITERROR': ['антитеррор', 'терроризм'],
            'CIVIL_DEFENSE': ['гражданская оборона', 'го и чс', 'чрезвычайных ситуациях'],
            'ROAD_SAFETY': ['безопасность дорожного движения', 'бдд'],
            'CORRUPTION': ['коррупция', 'закупок'],
            'PEDAGOGICAL': ['педагогических работников', 'педагог'],
        }

        target_category = TrainingCategory.objects.filter(
            code=category_code).first()
        if not target_category:
            target_category, _ = TrainingCategory.objects.get_or_create(
                code=category_code,
                defaults={'name': category_code}
            )

        name_lower = program_name_raw.lower()

        if category_code in keywords_map:
            for keyword in keywords_map[category_code]:
                if keyword in name_lower:
                    std_prog = TrainingProgram.objects.filter(
                        category=target_category,
                        name__icontains=keyword
                    ).first()
                    if std_prog:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'   ↳ Найдено совпадение по ключу "{keyword}": {
                                    std_prog.name}'))
                        return std_prog

        # 3. Создаем новую программу
        if not dry_run:
            self.stdout.write(self.style.WARNING(
                f'   ↳ Программа не найдена. Создаем новую: "{program_name_safe[:50]}..."'))
            program, _ = TrainingProgram.objects.get_or_create(
                name=program_name_safe,
                defaults={
                    'category': target_category,
                    'hours': 16,
                    'frequency_months': 12,
                    'is_mandatory': False
                }
            )
            return program
        return None

    def _find_employee(self, fio_string):
        """
        Усовершенствованный поиск сотрудника.
        """
        if not fio_string:
            return None

        fio_parts = str(fio_string).strip().split()
        if len(fio_parts) < 2:
            return None

        # Вариант 1: Полное совпадение
        if len(fio_parts) >= 3:
            ln, fn, mn = fio_parts[0], fio_parts[1], " ".join(fio_parts[2:])
            emp = Employee.objects.filter(
                (Q(last_name__iexact=ln) | Q(previous_last_name__iexact=ln)),
                first_name__iexact=fn,
                middle_name__iexact=mn
            ).first()
            if emp:
                return emp

        # Вариант 2: Только Фамилия + Имя
        ln, fn = fio_parts[0], fio_parts[1]
        emp = Employee.objects.filter(
            (Q(last_name__iexact=ln) | Q(previous_last_name__iexact=ln)),
            first_name__iexact=fn
        ).first()

        if emp:
            self.stdout.write(
                self.style.SUCCESS(
                    f'   ↳ Сотрудник найден по Фамилии+Имени: {emp}'))
            return emp

        return None

    def _search_employee_similar(self, fio_string):
        """
        Поиск похожих сотрудников (частичное совпадение).
        """
        if not fio_string:
            return []

        fio_parts = str(fio_string).strip().split()
        if len(fio_parts) < 1:
            return []

        ln = fio_parts[0].strip()

        # Ищем по фамилии (частичное совпадение)
        similar = Employee.objects.filter(
            Q(last_name__icontains=ln) | Q(previous_last_name__icontains=ln),
            is_active=True
        ).order_by('last_name', 'first_name')[:10]

        return list(similar)

    def _interactive_employee_choice(
            self, fio_string, row_idx, auto_create=False):
        """
        Интерактивный выбор действия при ненайденном сотруднике.
        Возвращает сотрудника или None.
        """
        self.stdout.write(
            self.style.ERROR(
                f'❌ Строка {row_idx}: Сотрудник "{fio_string}" не найден в базе'))

        # Показываем похожих сотрудников
        similar = self._search_employee_similar(fio_string)

        while True:
            self.stdout.write(self.style.WARNING(
                '\n🤔 Что делать с этой записью об обучении?'))
            self.stdout.write('   1. ⏭️  Пропустить эту запись')
            self.stdout.write(
                '   2. ⏭️⏭️  Пропустить ВСЕ записи для этого сотрудника')
            self.stdout.write(
                '   3. 🔍 Показать похожих сотрудников для выбора')
            self.stdout.write('   4. ✏️  Ввести правильное ФИО вручную')
            self.stdout.write('   5. ➕ Создать нового сотрудника (только ФИО)')
            self.stdout.write('   6. 🛑 Остановить импорт')

            if auto_create:
                self.stdout.write(self.style.SUCCESS(
                    '   [АВТО] Будет создан новый сотрудник (режим --auto-create-employees)'))

            choice = input('\nВаш выбор (1-6): ').strip()

            # Авто-создание если включен флаг
            if auto_create and choice not in ['1', '2', '6']:
                choice = '5'

            if choice == '1':
                return None, False  # Пропустить, не блокировать

            elif choice == '2':
                return None, True  # Пропустить и блокировать дальнейшие записи этого сотрудника

            elif choice == '3':
                if similar:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n📋 Найдено {
                                len(similar)} похожих сотрудников:'))
                    for i, emp in enumerate(similar, 1):
                        self.stdout.write(f'   {i}. {emp.last_name} {emp.first_name} {emp.middle_name} '
                                          f'({emp.position.name if emp.position else "Без должности"})')

                    select = input(
                        '\nВыберите номер сотрудника (или 0 для отмены): ').strip()
                    try:
                        idx = int(select) - 1
                        if 0 <= idx < len(similar):
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✅ Выбран: {
                                        similar[idx]}'))
                            return similar[idx], False
                    except (ValueError, IndexError):
                        pass
                    self.stdout.write(self.style.WARNING('Отмена выбора'))
                else:
                    self.stdout.write(
                        self.style.WARNING('Похожих сотрудников не найдено'))

            elif choice == '4':
                new_fio = input(
                    'Введите правильное ФИО (Фамилия Имя Отчество): ').strip()
                if new_fio:
                    emp = self._find_employee(new_fio)
                    if emp:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Сотрудник найден: {emp}'))
                        return emp, False
                    else:
                        self.stdout.write(
                            self.style.ERROR('Сотрудник с таким ФИО не найден'))
                else:
                    self.stdout.write(self.style.WARNING('Ввод отменён'))

            elif choice == '5':
                # Создание нового сотрудника
                fio_parts = fio_string.strip().split()
                if len(fio_parts) >= 2:
                    ln = fio_parts[0]
                    fn = fio_parts[1]
                    mn = fio_parts[2] if len(fio_parts) > 2 else ''

                    confirm = input(
                        f'Создать сотрудника: {ln} {fn} {mn}? (y/n): ').strip().lower()
                    if confirm == 'y':
                        emp = Employee.objects.create(
                            last_name=ln[:100],
                            first_name=fn[:100],
                            middle_name=mn[:100] if mn else '',
                            is_active=True
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Сотрудник создан: {emp}'))
                        return emp, False
                    else:
                        self.stdout.write(
                            self.style.WARNING('Создание отменено'))
                else:
                    self.stdout.write(
                        self.style.ERROR('Некорректный формат ФИО'))

            elif choice == '6':
                raise CommandError('Импорт остановлен пользователем')

            else:
                self.stdout.write(
                    self.style.ERROR('Неверный выбор, попробуйте снова'))

        return None, False

    def handle(self, *args, **options):
        path = options['file_path']
        scans_dir = options.get('scans-dir')
        dry_run = options.get('dry-run', False)
        interactive = options.get('interactive', False)
        auto_create = options.get('auto_create_employees', False)

        if not os.path.exists(path):
            raise CommandError(f'❌ Файл не найден: {path}')

        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except Exception as e:
            raise CommandError(f'❌ Ошибка открытия Excel файла: {e}')

        self.stdout.write(self.style.SUCCESS(f'✅ Файл загружен: {path}'))
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠️ РЕЖИМ ПРОВЕРКИ (dry-run) - изменения не сохраняются'))
        if interactive:
            self.stdout.write(self.style.WARNING(
                '🎮 ИНТЕРАКТИВНЫЙ РЕЖИМ - будут задаваться вопросы'))
        if auto_create:
            self.stdout.write(self.style.WARNING(
                '🤖 АВТО-СОЗДАНИЕ - отсутствующие сотрудники будут созданы'))

        # Статистика для отчёта
        stats = {
            'emp_created': 0,
            'emp_updated': 0,
            'train_created': 0,
            'train_updated': 0,
            'train_skipped': 0,
            'train_errors': 0,
            'employees_auto_created': 0,
            'interactive_choices': 0,
        }

        # ==========================================
        # 0. Организация
        # ==========================================
        org = None
        try:
            if "0. Организация" in wb.sheetnames:
                ws_org = wb["0. Организация"]
                for row in ws_org.iter_rows(min_row=2, values_only=True):
                    if self._get_cell_value(row, 0):
                        defaults = {
                            'name_full': str(self._get_cell_value(row, 0, '')).strip()[:255],
                            'inn': str(self._get_cell_value(row, 1, '')).strip()[:12],
                            'kpp': str(self._get_cell_value(row, 2, '')).strip()[:9],
                            'ogrn': str(self._get_cell_value(row, 3, '')).strip()[:15],
                            'address_legal': str(self._get_cell_value(row, 4, '')).strip()[:255],
                            'contact_phone': str(self._get_cell_value(row, 5, '')).strip()[:20],
                        }
                        if not dry_run:
                            org = OrganizationSafetyInfo.load_organization()
                            for key, value in defaults.items():
                                setattr(org, key, value)
                            org.save()
                        else:
                            org = type('Org', (), defaults)()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Организация: {
                                    defaults["name_full"]}'))
                        break
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка при импорте организации: {e}'))

        # ==========================================
        # 1. Площадки
        # ==========================================
        sites_created = 0
        try:
            if "1. Площадки" in wb.sheetnames:
                ws_sites = wb["1. Площадки"]
                for row in ws_sites.iter_rows(min_row=2, values_only=True):
                    if self._get_cell_value(row, 0):
                        if not dry_run:
                            Site.objects.get_or_create(
                                name=str(
                                    self._get_cell_value(
                                        row, 0, '')).strip(), organization=org, defaults={
                                    'address': str(
                                        self._get_cell_value(
                                            row, 1, '')).strip()[
                                        :255], 'ot_responsible_name': str(
                                        self._get_cell_value(
                                            row, 2, '')).strip()[
                                        :200], })
                        sites_created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Площадки: {sites_created} шт.'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка при импорте площадок: {e}'))

        # ==========================================
        # 2. Подразделения
        # ==========================================
        deps_created = 0
        try:
            if "2. Подразделения" in wb.sheetnames:
                ws_deps = wb["2. Подразделения"]
                for row in ws_deps.iter_rows(min_row=2, values_only=True):
                    if self._get_cell_value(row, 0):
                        parent = None
                        if self._get_cell_value(row, 2):
                            parent = Department.objects.filter(
                                name=str(self._get_cell_value(row, 2)).strip()).first()
                        if not dry_run:
                            dept, created = Department.objects.get_or_create(
                                name=str(
                                    self._get_cell_value(
                                        row, 0, '')).strip(), defaults={
                                    'description': str(
                                        self._get_cell_value(
                                            row, 1, '')).strip(), 'parent': parent})
                            if created:
                                deps_created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Подразделения: {deps_created} шт.'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка при импорте подразделений: {e}'))

        # ==========================================
        # 3. Должности
        # ==========================================
        pos_created = 0
        try:
            if "3. Должности" in wb.sheetnames:
                ws_pos = wb["3. Должности"]
                for row in ws_pos.iter_rows(min_row=2, values_only=True):
                    if self._get_cell_value(row, 0):
                        dept = None
                        if self._get_cell_value(row, 1):
                            dept = Department.objects.filter(
                                name=str(self._get_cell_value(row, 1)).strip()).first()
                        if not dry_run:
                            pos, created = Position.objects.get_or_create(
                                name=str(
                                    self._get_cell_value(
                                        row, 0, '')).strip(), defaults={
                                    'department': dept, 'description': str(
                                        self._get_cell_value(
                                            row, 2, '')).strip()})
                            if created:
                                pos_created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Должности: {pos_created} шт.'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка при импорте должностей: {e}'))

        # ==========================================
        # 4. Сотрудники
        # ==========================================
        try:
            if "4. Сотрудники" not in wb.sheetnames:
                raise CommandError(
                    '❌ Критическая ошибка: Лист "4. Сотрудники" не найден!')

            ws_emp = wb["4. Сотрудники"]
            for row_idx, row in enumerate(
                ws_emp.iter_rows(
                    min_row=2, values_only=True), start=2):
                if not self._get_cell_value(
                        row,
                        0) or not self._get_cell_value(
                        row,
                        2):
                    continue
                try:
                    birth_date = self._parse_date(self._get_cell_value(row, 6))
                    hire_date = self._parse_date(self._get_cell_value(row, 7))
                    termination_date = self._parse_date(
                        self._get_cell_value(row, 18))

                    position = None
                    if self._get_cell_value(row, 4):
                        position = Position.objects.filter(
                            name=str(self._get_cell_value(row, 4)).strip()).first()

                    department = None
                    if self._get_cell_value(row, 5):
                        department = Department.objects.filter(
                            name=str(self._get_cell_value(row, 5)).strip()).first()

                    defaults = {
                        'middle_name': str(self._get_cell_value(row, 3, '')).strip()[:100],
                        'previous_last_name': str(self._get_cell_value(row, 1, '')).strip()[:100],
                        'position': position,
                        'department': department,
                        'birth_date': birth_date,
                        'hire_date': hire_date,
                        'phone': str(self._get_cell_value(row, 8, '')).strip()[:20],
                        'email': str(self._get_cell_value(row, 9, '')).strip()[:254],
                        'is_executive': self._parse_boolean(self._get_cell_value(row, 10)),
                        'is_pedagogical': self._parse_boolean(self._get_cell_value(row, 11)),
                        'is_safety_specialist': self._parse_boolean(self._get_cell_value(row, 12)),
                        'is_safety_committee_member': self._parse_boolean(self._get_cell_value(row, 13)),
                        'is_safety_committee_chair': self._parse_boolean(self._get_cell_value(row, 14)),
                        'is_acting_director': self._parse_boolean(self._get_cell_value(row, 15)),
                        'exempt_from_safety_instruction': self._parse_boolean(self._get_cell_value(row, 16)),
                        'on_parental_leave': self._parse_boolean(self._get_cell_value(row, 17)),
                        'termination_date': termination_date,
                        'termination_order_number': str(self._get_cell_value(row, 19, '')).strip()[:50],
                        'is_active': termination_date is None,
                    }

                    if not dry_run:
                        emp, created = Employee.objects.update_or_create(
                            last_name=str(
                                self._get_cell_value(
                                    row, 0, '')).strip()[
                                :100], first_name=str(
                                self._get_cell_value(
                                    row, 2, '')).strip()[
                                :100], defaults=defaults)
                        if created:
                            stats['emp_created'] += 1
                        else:
                            stats['emp_updated'] += 1
                    else:
                        stats['emp_created'] += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Ошибка в строке {row_idx}: {e}'))
                    continue

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Сотрудники: {
                        stats["emp_created"]} новых, {
                        stats["emp_updated"]} обновлено'))
        except Exception as e:
            raise CommandError(
                f'❌ Критическая ошибка при импорте сотрудников: {e}')

        # ==========================================
        # 5. Программы обучения
        # ==========================================
        prog_created = 0
        try:
            if "5. Программы" in wb.sheetnames:
                ws_prog = wb["5. Программы"]
                category_names = {
                    'SAFETY': 'Охрана труда',
                    'FIRE': 'Пожарная безопасность',
                    'FIRST_AID': 'Первая помощь',
                    'ELECTRICAL': 'Электробезопасность',
                    'ANTITERROR': 'Антитеррористическая защищенность',
                    'OTHER': 'Прочее'}
                for row in ws_prog.iter_rows(min_row=2, values_only=True):
                    if not self._get_cell_value(row, 0):
                        continue
                    try:
                        raw_category = str(
                            self._get_cell_value(
                                row, 1, 'OTHER')).strip().upper()
                        if not dry_run:
                            category_obj, _ = TrainingCategory.objects.get_or_create(
                                code=raw_category, defaults={
                                    'name': category_names.get(
                                        raw_category, raw_category)})
                            prog, created = TrainingProgram.objects.get_or_create(
                                name=str(
                                    self._get_cell_value(
                                        row, 0, '')).strip()[
                                    :255], defaults={
                                    'category': category_obj, 'hours': int(
                                        self._get_cell_value(
                                            row, 2, 8)), 'frequency_months': int(
                                        self._get_cell_value(
                                            row, 3, 12)), 'is_mandatory': self._parse_boolean(
                                        self._get_cell_value(
                                            row, 4)), })
                            if created:
                                prog_created += 1
                        else:
                            prog_created += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️ Пропущена программа: {e}'))
                        continue
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Программы обучения: {prog_created} шт.'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка при импорте программ: {e}'))

        # ==========================================
        # 6. Автоматическое назначение директора и спец. по ОТ
        # ==========================================
        if org and not dry_run:
            try:
                director = None
                director_position = Position.objects.filter(
                    name__iexact='Директор').first()
                if director_position:
                    director = Employee.objects.filter(
                        is_active=True, position=director_position).order_by('hire_date').first()
                if not director:
                    director = Employee.objects.filter(
                        is_active=True, is_acting_director=True).order_by('hire_date').first()
                if director:
                    org.director = director
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Назначен директор: {director}'))

                specialist = Employee.objects.filter(
                    is_active=True, is_safety_specialist=True).first()
                if specialist:
                    org.safety_specialist = specialist
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Назначен спец. по ОТ: {specialist}'))
                org.save()
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Ошибка при назначении ответственных: {e}'))

        # ==========================================
        # 7. Обучение (С ИНТЕРАКТИВНЫМ РЕЖИМОМ)
        # ==========================================
        try:
            if "6. Обучение" in wb.sheetnames:
                ws_train = wb["6. Обучение"]

                category_map = {
                    'от': 'SAFETY',
                    'охрана труда': 'SAFETY',
                    'пб': 'FIRE',
                    'пожарная безопасность': 'FIRE',
                    'эб': 'ELECTRICAL',
                    'электробезопасность': 'ELECTRICAL',
                    'первая помощь': 'FIRST_AID',
                    'оказание первой помощи': 'FIRST_AID',
                    'антитерроризм': 'ANTITERROR',
                    'го': 'CIVIL_DEFENSE',
                    'бдд': 'ROAD_SAFETY',
                    'дорожное движение': 'ROAD_SAFETY',
                    'коррупция': 'OTHER',
                    'педагог': 'FIRST_AID'}

                doc_type_map = {
                    'протокол': 'PROTOCOL', 'удостоверение': 'CERT_QUAL',
                    'сертификат': 'CERT_COMPL', 'диплом': 'DIPLOMA'
                }

                # Отслеживаем сотрудников, которых пользователь решил
                # пропустить
                skip_employees = set()

                for row_idx, row in enumerate(
                    ws_train.iter_rows(
                        min_row=2, values_only=True), start=2):
                    if not self._get_cell_value(
                            row,
                            0) or not self._get_cell_value(
                            row,
                            3):
                        continue

                    try:
                        fio_string = str(self._get_cell_value(row, 0)).strip()

                        # Проверяем, не в списке ли пропущенных
                        if fio_string in skip_employees:
                            stats['train_skipped'] += 1
                            continue

                        # Поиск сотрудника
                        emp = self._find_employee(fio_string)

                        # Если не найден - интерактивный режим или
                        # авто-создание
                        if not emp:
                            if interactive or auto_create:
                                emp, block_future = self._interactive_employee_choice(
                                    fio_string, row_idx, auto_create=auto_create)
                                stats['interactive_choices'] += 1

                                if block_future and fio_string:
                                    skip_employees.add(fio_string)

                                if not emp:
                                    stats['train_skipped'] += 1
                                    continue

                                if emp and auto_create:
                                    stats['employees_auto_created'] += 1
                            else:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'⚠️ Строка {row_idx}: Сотрудник "{fio_string}" не найден (используйте --interactive)'))
                                stats['train_skipped'] += 1
                                continue

                        # Данные из строки
                        category_raw = str(
                            self._get_cell_value(
                                row, 1, 'другое')).strip().lower()
                        doc_type_raw = str(
                            self._get_cell_value(
                                row, 2, '')).strip().lower()
                        program_name_in_doc = str(
                            self._get_cell_value(row, 3, '')).strip()
                        train_date = self._parse_date(
                            self._get_cell_value(row, 4))
                        doc_number = str(
                            self._get_cell_value(
                                row, 5, '')).strip()

                        if not train_date:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'⚠️ Строка {row_idx}: Неверная дата обучения'))
                            stats['train_skipped'] += 1
                            continue

                        # Определение категории
                        category_code = 'OTHER'
                        for key, code in category_map.items():
                            if key in category_raw:
                                category_code = code
                                break

                        # Поиск или создание программы
                        training_program = self._find_or_create_program(
                            program_name_in_doc, category_code, dry_run=dry_run
                        )

                        if not training_program:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'❌ Строка {row_idx}: Не удалось создать программу'))
                            stats['train_errors'] += 1
                            continue

                        # Сохранение записи
                        if not dry_run:
                            training, created = Training.objects.update_or_create(
                                employee=emp,
                                training_date=train_date,
                                program=training_program,
                                defaults={
                                    'raw_program_name': program_name_in_doc[:500],
                                    'document_type': doc_type_map.get(doc_type_raw, 'OTHER'),
                                    'document_number': doc_number[:100] if doc_number else '',
                                }
                            )

                            if created:
                                stats['train_created'] += 1
                            else:
                                stats['train_updated'] += 1

                            # Загрузка скана
                            if scans_dir and self._get_cell_value(row, 6):
                                scan_file = str(
                                    self._get_cell_value(
                                        row, 6)).strip()
                                file_path = os.path.join(scans_dir, scan_file)
                                if os.path.exists(file_path):
                                    with open(file_path, 'rb') as f:
                                        training.document_scan.save(
                                            scan_file, File(f), save=True)
                        else:
                            stats['train_created'] += 1

                    except CommandError:
                        raise
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'❌ Ошибка в строке {row_idx} (Обучение): {e}'))
                        stats['train_errors'] += 1
                        continue

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Обучение: {
                            stats["train_created"]} новых, {
                            stats["train_updated"]} обновлено'))
                if stats['train_skipped'] > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️ Пропущено записей: {
                                stats["train_skipped"]}'))
                if stats['train_errors'] > 0:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Ошибок: {
                                stats["train_errors"]}'))
            else:
                self.stdout.write(self.style.WARNING(
                    'ℹ️ Лист "6. Обучение" не найден'))
        except CommandError:
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка при импорте обучения: {e}'))

        # ==========================================
        # Итоговый отчёт
        # ==========================================
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('📊 ИТОГОВЫЙ ОТЧЁТ'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'✅ Организация: обновлена')
        self.stdout.write(
            f'✅ Сотрудники: {
                stats["emp_created"]} новых, {
                stats["emp_updated"]} обновлено')
        self.stdout.write(f'✅ Программы: {prog_created} шт.')
        self.stdout.write(
            f'✅ Обучение: {
                stats["train_created"]} новых, {
                stats["train_updated"]} обновлено')

        if stats['train_skipped'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ Пропущено записей об обучении: {
                        stats["train_skipped"]}'))
        if stats['train_errors'] > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибок при импорте: {
                        stats["train_errors"]}'))
        if stats['interactive_choices'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'🎮 Интерактивных выборов: {
                        stats["interactive_choices"]}'))
        if stats['employees_auto_created'] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'🤖 Сотрудников создано автоматически: {
                        stats["employees_auto_created"]}'))

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ИМПОРТ ЗАВЕРШЁН'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠️ РЕЖИМ ПРОВЕРКИ - данные не сохранены'))
