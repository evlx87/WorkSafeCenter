from dateutil.relativedelta import relativedelta
from django.utils import timezone

from employees.models import Employee
from .models import Training, Instruction, TrainingProgram, InstructionType


def get_next_training_date(training_date, frequency_months):
    """Вычисляет дату следующего обучения."""
    if frequency_months > 0:
        return training_date + relativedelta(months=frequency_months)
    return None


def check_employee_compliance(employee: Employee):
    """
    Проверяет сотрудника на соответствие требованиям по обязательному обучению (курсы и инструктажи).

    Возвращает словарь со списком недостающих и просроченных обязательств.
    """
    status = {
        'missing_programs': [],  # Не пройденные обязательные курсы
        # Не пройденные обязательные инструктажи (включая вводные)
        'missing_instructions': [],
        'expired_programs': [],  # Просроченные курсы
        'expired_instructions': [],  # Просроченные инструктажи (повторные)
    }

    # Если сотрудник уволен, не проверяем
    if employee.termination_date:
        return status

    today = timezone.now().date()

    # ==========================================
    # 1. ПРОВЕРКА ПРОГРАММ ОБУЧЕНИЯ (КУРСЫ)
    # ==========================================

    # Получаем все программы из базы данных для одного запроса
    programs = TrainingProgram.objects.all()

    # 1.1 Определяем, какие программы нужны этому сотруднику
    required_programs_names = set()

    # А. Электробезопасность (Нужна ВСЕМ)
    required_programs_names.add('Электробезопасность')

    # Б. Охрана труда (Руководители, Замы, Члены комиссии)
    # Используем 'Специалист по охране труда' как часть логики
    # руководства/комиссии
    if employee.is_executive or employee.is_safety_committee_member:
        # Используем часть названия, чтобы найти нужную программу
        required_programs_names.add('Охрана труда для руководителей')

    # В. Первая помощь (Руководители, Замы, Педагоги)
    if employee.is_executive or employee.is_pedagogical:
        # Используем часть названия
        required_programs_names.add('Первая помощь')

    # Г. Пожарная безопасность (Руководители, Замы)
    if employee.is_executive:
        required_programs_names.add('Пожарная безопасность')

    # 1.2 Проверяем наличие и сроки

    for prog_name in required_programs_names:
        # Ищем программу по части названия
        program = programs.filter(name__icontains=prog_name).first()

        if program:
            # Ищем последнее обучение по этой программе
            last_training = Training.objects.filter(
                employee=employee,
                program=program
            ).order_by('-training_date').first()

            if not last_training:
                status['missing_programs'].append(program)
            else:
                # Проверка сроков (если периодичность > 0)
                if program.frequency_months > 0:
                    expire_date = get_next_training_date(
                        last_training.training_date, program.frequency_months)
                    if expire_date < today:
                        status['expired_programs'].append(program)

    # ==========================================
    # 2. ПРОВЕРКА ИНСТРУКТАЖЕЙ
    # ==========================================

    instruction_types = InstructionType.objects.all()

    # А. Вводные инструктажи (ОТ и Пожарный) - нужны ВСЕМ (frequency_months=0)
    intro_types = instruction_types.filter(type_name__icontains='Вводный')
    for i_type in intro_types:
        exists = Instruction.objects.filter(
            employee=employee, instruction_type=i_type).exists()
        if not exists:
            status['missing_instructions'].append(i_type)

    # Б. Первичный/Повторный на рабочем месте (периодические, frequency_months > 0)
    # Нужен всем, КРОМЕ освобожденных
    if not employee.exempt_from_safety_instruction:
        repeat_types = instruction_types.filter(
            category__in=['SAFETY', 'FIRE'],
            frequency_months__gt=0
        )

        for i_type in repeat_types:
            # Ищем самый последний инструктаж (первичный или повторный)
            last_instr = Instruction.objects.filter(
                employee=employee,
                # Группируем по категории (ОТ, Пож)
                instruction_type__category=i_type.category
            ).order_by('-training_date').first()

            if not last_instr:
                status['missing_instructions'].append(i_type)
            else:
                # Проверка сроков
                frequency = i_type.frequency_months
                expire_date = get_next_training_date(
                    last_instr.training_date, frequency)

                if expire_date and expire_date < today:
                    status['expired_instructions'].append(i_type)

    # В. Инструктаж по электробезопасности (1 группа)
    prog_electro_instr = instruction_types.filter(
        type_name__icontains='Ежегодный',
        category='ELECTRICAL').first()
    if prog_electro_instr:
        last_instr = Instruction.objects.filter(
            employee=employee,
            instruction_type=prog_electro_instr
        ).order_by('-training_date').first()

        if not last_instr:
            status['missing_instructions'].append(prog_electro_instr)
        else:
            frequency = prog_electro_instr.frequency_months
            expire_date = get_next_training_date(
                last_instr.training_date, frequency)

            if expire_date and expire_date < today:
                status['expired_instructions'].append(prog_electro_instr)

    return status
