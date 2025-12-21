import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

from organization.models import OrganizationSafetyInfo, Department, Position

load_dotenv()


class Command(BaseCommand):
    help = 'Загружает данные об организации, отделах и должностях из .env файла.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(
            'Начинаем загрузку данных организации...'))

        # ==========================================
        # 1. Загрузка основных реквизитов организации
        # ==========================================
        name_full = os.getenv('ORG_NAME_FULL')
        inn = os.getenv('ORG_INN', '')
        kpp = os.getenv('ORG_KPP', '')  # Новое поле
        ogrn = os.getenv('ORG_OGRN', '')
        address_legal = os.getenv('ORG_ADDRESS_LEGAL', '')
        contact_phone = os.getenv('ORG_CONTACT_PHONE', '')

        if not name_full:
            self.stdout.write(self.style.ERROR(
                'Ошибка: Переменная ORG_NAME_FULL не найдена в .env'))
            return

        # Используем update_or_create для синглтона (pk=1)
        info, created = OrganizationSafetyInfo.objects.update_or_create(
            pk=1,
            defaults={
                'name_full': name_full,
                'inn': inn,
                'kpp': kpp,
                'ogrn': ogrn,
                'address_legal': address_legal,
                'contact_phone': contact_phone,
            }
        )

        action = "Создана" if created else "Обновлена"
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Информация об организации {action}: {
                    info.name_full} (ИНН: {
                    info.inn}, КПП: {
                    info.kpp})'))

        # ==========================================
        # 2. Загрузка Структуры (Отделы и Должности)
        # ==========================================
        structure_json = os.getenv('ORG_STRUCTURE_JSON')

        if not structure_json:
            self.stdout.write(self.style.WARNING(
                '⚠️ Переменная ORG_STRUCTURE_JSON не найдена. Отделы и должности не обновлены.'))
            return

        try:
            structure_data = json.loads(structure_json)
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка чтения JSON структуры из .env: {e}'))
            return

        self.stdout.write('Загрузка структуры подразделений...')

        counters = {'deps_created': 0, 'pos_created': 0}

        for dept_name, positions_list in structure_data.items():
            # 2.1 Создаем или получаем Отдел
            department, dept_created = Department.objects.get_or_create(
                name=dept_name.strip()
            )
            if dept_created:
                counters['deps_created'] += 1
                self.stdout.write(f'  + Отдел: {department.name}')

            # 2.2 Создаем должности внутри этого отдела
            if isinstance(positions_list, list):
                for pos_name in positions_list:
                    position, pos_created = Position.objects.get_or_create(
                        name=pos_name.strip(),
                        defaults={'department': department}
                    )

                    # Если должность существовала, но была в другом отделе или
                    # без отдела - обновляем
                    if not pos_created and position.department != department:
                        position.department = department
                        position.save()
                        self.stdout.write(
                            f'    > Должность "{
                                position.name}" перемещена в {
                                department.name}')

                    if pos_created:
                        counters['pos_created'] += 1
                        self.stdout.write(f'    + Должность: {position.name}')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'    ⚠️ Неверный формат списка должностей для {dept_name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Структура загружена.\n'
            f'   Новых отделов: {counters["deps_created"]}\n'
            f'   Новых должностей: {counters["pos_created"]}'
        ))
