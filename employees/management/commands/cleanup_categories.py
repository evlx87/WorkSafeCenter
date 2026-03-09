from django.core.management.base import BaseCommand

from trainings.models import Training
from trainings.models import TrainingCategory, TrainingProgram, InstructionType


class Command(BaseCommand):
    help = 'Очищает базу данных от лишних категорий обучения'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Режим проверки без удаления данных'
        )
        parser.add_argument(
            '--reassign-training',
            action='store_true',
            help='Переназначить записи об обучении на новые категории вместо удаления')
        parser.add_argument(
            '--show-remaining',
            action='store_true',
            help='Показать оставшиеся категории после очистки'
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Удалить ВСЕ категории кроме 4 основных (игнорируя коды)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        reassign = options['reassign_training']
        show_remaining = options['show_remaining']
        force_all = options['force_all']

        # Категории, которые нужно СОХРАНИТЬ (только 4 основных)
        categories_to_keep = ['SAFETY', 'FIRE', 'FIRST_AID', 'ELECTRICAL']

        # ✅ НОВОЕ: Находим ВСЕ категории, которые нужно удалить
        # (все, кроме 4 основных, независимо от кода)
        if force_all:
            categories_to_remove = TrainingCategory.objects.exclude(
                code__in=categories_to_keep
            )
            self.stdout.write(self.style.WARNING(
                '🔥 РЕЖИМ FORCE-ALL: Будут удалены ВСЕ категории кроме 4 основных'
            ))
        else:
            # Старая логика - по списку кодов
            categories_to_remove_codes = [
                'CIVIL_DEFENSE',
                'ROAD_SAFETY',
                'WORKING_HEIGHT',
                'ANTITERROR',
                'ENVIRONMENTAL',
                'OTHER',
                'БДД',  # ✅ Добавили русские коды
                'ГО',  # ✅ Добавили русские коды
                'ЭЛЕКТРОБЕЗОПАСНОСТЬ',  # ✅ Добавили русские коды
            ]
            categories_to_remove = TrainingCategory.objects.filter(
                code__in=categories_to_remove_codes
            )

        self.stdout.write(self.style.WARNING('📋 Категории для удаления:'))
        for cat in categories_to_remove:
            self.stdout.write(f'   - {cat.code} ({cat.name})')

        self.stdout.write(self.style.SUCCESS('\n✅ Категории для сохранения:'))
        for code in categories_to_keep:
            cat = TrainingCategory.objects.filter(code=code).first()
            if cat:
                self.stdout.write(f'   + {code}: {cat.name}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n⚠️ РЕЖИМ ПРОВЕРКИ (dry-run)'))

        if reassign:
            self.stdout.write(self.style.WARNING(
                '🔄 Записи об обучении будут переназначены в SAFETY'))

        # ==========================================
        # 1. ПРОВЕРКА ЗАПИСЕЙ ОБ ОБУЧЕНИИ
        # ==========================================
        programs_to_delete = TrainingProgram.objects.filter(
            category__in=categories_to_remove
        )

        affected_trainings = Training.objects.filter(
            program__in=programs_to_delete
        )

        if affected_trainings.exists():
            self.stdout.write(self.style.WARNING(
                f'\n⚠️ Найдено {affected_trainings.count()} записей об обучении, '
                f'ссылающихся на удаляемые программы:'
            ))

            for training in affected_trainings[:10]:
                self.stdout.write(
                    f'   - {training.employee}: {training.program.name}'
                )

            if affected_trainings.count() > 10:
                self.stdout.write(
                    f'   ... и ещё {affected_trainings.count() - 10}'
                )

            if not reassign and not dry_run:
                self.stdout.write(self.style.ERROR(
                    '\n❌ ОШИБКА: Нельзя удалить программы с активными записями!'
                ))
                self.stdout.write(self.style.WARNING(
                    '   Используйте --reassign-training для переназначения записей'
                ))
                self.stdout.write(self.style.WARNING(
                    '   Или используйте --force-all для принудительного удаления'
                ))
                return

        # ==========================================
        # 2. ПЕРЕНАЗНАЧЕНИЕ ЗАПИСЕЙ (если указано)
        # ==========================================
        if reassign and not dry_run:
            self.stdout.write(self.style.SUCCESS(
                '\n🔄 Переназначение записей об обучении...'))

            # Кэшируем программы назначения
            target_programs = {}
            for code in categories_to_keep:
                prog = TrainingProgram.objects.filter(
                    category__code=code
                ).first()
                if prog:
                    target_programs[code] = prog

            reassigned_count = 0
            for training in affected_trainings:
                old_category = training.program.category.code
                new_category_code = 'SAFETY'  # Все в SAFETY

                new_program = target_programs.get(new_category_code)

                if new_program:
                    training.program = new_program
                    training.save()
                    reassigned_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'   ✗ {
                                training.employee}: Нет программы для переназначения'))

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Переназначено записей: {reassigned_count}'
                )
            )

        # ==========================================
        # 3. УДАЛЕНИЕ ПРОГРАММ
        # ==========================================
        for category in categories_to_remove:
            programs_count = TrainingProgram.objects.filter(
                category=category).count()
            if programs_count > 0:
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️ Категория {
                                category.code}: {programs_count} программ будет удалено'))
                else:
                    TrainingProgram.objects.filter(category=category).delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Категория {
                                category.code}: {programs_count} программ удалено'))

            # Удаляем категорию
            if not dry_run:
                category.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Категория {category.code} удалена')
                )

        # ==========================================
        # 4. УДАЛЕНИЕ ТИПОВ ИНСТРУКТАЖЕЙ
        # ==========================================
        instruction_types_to_remove = InstructionType.objects.exclude(
            category__in=categories_to_keep
        )
        if instruction_types_to_remove.exists():
            count = instruction_types_to_remove.count()
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Типы инструктажей: {count} будет удалено'
                    )
                )
            else:
                instruction_types_to_remove.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Типы инструктажей: {count} удалено'
                    )
                )

        # ==========================================
        # 5. ПРОВЕРКА ОСТАТКОВ В БД
        # ==========================================
        if show_remaining or not dry_run:
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            self.stdout.write(self.style.SUCCESS(
                '📊 ПРОВЕРКА ОСТАТКОВ В БАЗЕ ДАННЫХ'))
            self.stdout.write(self.style.SUCCESS('=' * 60))

            # Категории
            self.stdout.write(self.style.SUCCESS('\n📁 КАТЕГОРИИ ОБУЧЕНИЯ:'))
            remaining_categories = TrainingCategory.objects.all().order_by('code')
            for cat in remaining_categories:
                prog_count = TrainingProgram.objects.filter(
                    category=cat).count()
                status = '✅' if cat.code in categories_to_keep else '⚠️'
                self.stdout.write(
                    f'   {status} {
                        cat.code}: {
                        cat.name} ({prog_count} программ)')

            # Проверка на лишние категории
            unexpected_categories = remaining_categories.exclude(
                code__in=categories_to_keep
            )
            if unexpected_categories.exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠️ ОБНАРУЖЕНО {
                            unexpected_categories.count()} лишних категорий!'))
                for cat in unexpected_categories:
                    self.stdout.write(f'   - {cat.code}: {cat.name}')
                self.stdout.write(self.style.WARNING(
                    '\n💡 Запустите с --force-all для удаления всех лишних категорий'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    '\n✅ Все категории соответствуют требованиям (только 4 основных)'
                ))

            # Программы
            self.stdout.write(self.style.SUCCESS('\n📋 ПРОГРАММЫ ОБУЧЕНИЯ:'))
            total_programs = TrainingProgram.objects.count()
            self.stdout.write(f'   Всего программ: {total_programs}')

            for code in categories_to_keep:
                cat = TrainingCategory.objects.filter(code=code).first()
                if cat:
                    prog_count = TrainingProgram.objects.filter(
                        category=cat).count()
                    self.stdout.write(f'   • {code}: {prog_count} программ')

            # Типы инструктажей
            self.stdout.write(self.style.SUCCESS('\n📝 ТИПЫ ИНСТРУКТАЖЕЙ:'))
            total_types = InstructionType.objects.count()
            self.stdout.write(f'   Всего типов: {total_types}')

            for code in categories_to_keep:
                type_count = InstructionType.objects.filter(
                    category=code).count()
                self.stdout.write(f'   • {code}: {type_count} типов')

            # Записи об обучении
            self.stdout.write(self.style.SUCCESS('\n🎓 ЗАПИСИ ОБ ОБУЧЕНИИ:'))
            total_trainings = Training.objects.count()
            self.stdout.write(f'   Всего записей: {total_trainings}')

            for code in categories_to_keep:
                cat = TrainingCategory.objects.filter(code=code).first()
                if cat:
                    training_count = Training.objects.filter(
                        program__category=cat
                    ).count()
                    self.stdout.write(f'   • {code}: {training_count} записей')

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))

        self.stdout.write(self.style.SUCCESS('🎉 Очистка завершена!'))

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠️ Запустите без --dry-run для реального удаления'))
