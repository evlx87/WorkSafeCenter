from django.core.management.base import BaseCommand
from documents.models import Category


class Command(BaseCommand):
    help = 'Заполняет базу данных начальными категориями документов'

    def handle(self, *args, **kwargs):
        categories = [
            'Пожарная безопасность', 'Электробезопасность',
            'Гигиена и санитария', 'Работы на высоте',
            'Офисная работа', 'Прочее'
        ]
        for name in categories:
            Category.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS('Категории успешно обновлены!'))
