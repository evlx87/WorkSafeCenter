import os

from django.core.management.base import BaseCommand, CommandError
from dotenv import load_dotenv

from employees.models import Employee
from organization.models import OrganizationSafetyInfo

load_dotenv()


class Command(BaseCommand):
    help = 'Loads or updates OrganizationSafetyInfo model instance from .env file settings.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE(
            'Starting organization info load/update...'))

        try:
            # 1. Загрузка данных из .env
            name_full = os.getenv('ORG_NAME_FULL')
            inn = os.getenv('ORG_INN', '')  # С пустым значением по умолчанию
            ogrn = os.getenv('ORG_OGRN', '')
            address_legal = os.getenv('ORG_ADDRESS_LEGAL', '')
            contact_phone = os.getenv('ORG_CONTACT_PHONE', '')

            # Связанные объекты
            director_id = os.getenv('ORG_DIRECTOR_ID')
            director_position = os.getenv('ORG_DIRECTOR_POSITION', 'Директор')
            safety_specialist_id = os.getenv('ORG_SAFETY_SPECIALIST_ID')
            committee_ids_str = os.getenv(
                'ORG_SAFETY_COMMITTEE_MEMBER_IDS', '')

            if not name_full:
                raise CommandError(
                    "Переменная ORG_NAME_FULL не найдена в .env.")

            # 2. Получение или создание единственной записи
            # OrganizationSafetyInfo
            info, created = OrganizationSafetyInfo.objects.get_or_create(
                pk=1,  # Использование PK=1 гарантирует синглтон
                defaults={'name_full': name_full}
            )

            # 3. Обновление простых полей
            info.name_full = name_full
            info.inn = inn
            info.ogrn = ogrn
            info.address_legal = address_legal
            info.contact_phone = contact_phone
            info.director_position = director_position

            # 4. Обновление полей ForeignKey (Director и Specialist)
            info.director = self._get_employee_or_none(
                director_id, 'директора')
            info.safety_specialist = self._get_employee_or_none(
                safety_specialist_id, 'специалиста по ОТ')

            info.save()

            # 5. Обновление ManyToMany (Комиссия)
            committee_members = self._get_committee_members(committee_ids_str)
            info.safety_committee_members.set(committee_members)

            action = "Создана" if created else "Обновлена"
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Информация об организации успешно {action}.'))

        except CommandError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Ошибка при выполнении: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Неизвестная ошибка: {e}'))

    def _get_employee_or_none(self, employee_id, role_name):
        """Получает объект Employee по ID или возвращает None, если ID пуст или не найден."""
        if not employee_id:
            return None

        try:
            return Employee.objects.get(pk=int(employee_id))
        except (ValueError, Employee.DoesNotExist):
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Внимание: Сотрудник для роли '{role_name}' (ID={employee_id}) не найден. Поле оставлено пустым."))
            return None

    def _get_committee_members(self, ids_str):
        """Получает список объектов Employee для комиссии."""
        if not ids_str:
            return []

        try:
            id_list = [int(i.strip()) for i in ids_str.split(',') if i.strip()]
        except ValueError:
            self.stdout.write(self.style.WARNING(
                "⚠️ Внимание: ID членов комиссии должны быть целыми числами, разделенными запятыми. Поле оставлено пустым."
            ))
            return []

        members = Employee.objects.filter(pk__in=id_list)

        # Проверка на пропущенные ID
        found_ids = set(member.pk for member in members)
        missing_ids = set(id_list) - found_ids

        if missing_ids:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Внимание: Некоторые ID членов комиссии не найдены в базе данных: {missing_ids}. Игнорируются."))

        return list(members)
