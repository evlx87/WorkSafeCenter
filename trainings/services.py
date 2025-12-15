from dateutil.relativedelta import relativedelta
from django.utils import timezone

from .models import Training, Instruction, TrainingProgram, InstructionType


def check_employee_compliance(employee):
    """
    Проверяет сотрудника на соответствие требованиям по обучению.
    Возвращает словарь с недостающими обучениями.
    """
    status = {
        'missing_programs': [],  # Не пройденные программы
        'missing_instructions': [],  # Не пройденные инструктажи
        'expired_programs': [],  # Просроченные программы
        'expired_instructions': [],  # Просроченные инструктажи
    }

    today = timezone.now().date()

    # ==========================================
    # 1. ПРОВЕРКА ПРОГРАММ ОБУЧЕНИЯ (КУРСЫ)
    # ==========================================

    # Определяем, какие программы нужны этому сотруднику
    required_programs_ids = []

    # А. Электробезопасность (Нужна всем - фильтруем по названию или типу)
    # Предполагаем, что в БД есть программа с training_type='OTHER' или
    # названием 'Электробезопасность'
    prog_electro = TrainingProgram.objects.filter(
        name__icontains="Электробезопасность").first()
    if prog_electro:
        required_programs_ids.append(prog_electro.id)

    # Б. Охрана труда (Руководители, Замы, Члены комиссии)
    # Логика: если is_executive=True или is_safety_committee_member=True
    if employee.is_executive or employee.is_safety_committee_member:
        prog_ot = TrainingProgram.objects.filter(
            training_type='SAFETY', name__icontains="руководител").first()
        if prog_ot:
            required_programs_ids.append(prog_ot.id)

    # В. Первая помощь (Руководители, Замы, Педагоги)
    if employee.is_executive or employee.is_pedagogical_staff:
        prog_first_aid = TrainingProgram.objects.filter(
            training_type='FIRST_AID').first()
        if prog_first_aid:
            required_programs_ids.append(prog_first_aid.id)

    # Г. Пожарная безопасность (Руководители, Замы)
    if employee.is_executive:
        prog_fire = TrainingProgram.objects.filter(
            training_type='FIRE').first()
        if prog_fire:
            required_programs_ids.append(prog_fire.id)

    # Проверяем наличие обучений
    for prog_id in required_programs_ids:
        program = TrainingProgram.objects.get(id=prog_id)
        # Ищем последнее обучение по этой программе
        last_training = Training.objects.filter(
            employee=employee,
            program=program
        ).order_by('-training_date').first()

        if not last_training:
            status['missing_programs'].append(program)
        else:
            # Проверка сроков
            if program.frequency_months > 0:
                expire_date = last_training.training_date + \
                    relativedelta(months=program.frequency_months)
                if expire_date < today:
                    status['expired_programs'].append(program)

    # ==========================================
    # 2. ПРОВЕРКА ИНСТРУКТАЖЕЙ
    # ==========================================

    # А. Вводные инструктажи (ОТ и Пожарный) - нужны ВСЕМ
    intro_types = InstructionType.objects.filter(
        type_name__icontains='Вводный')
    for i_type in intro_types:
        exists = Instruction.objects.filter(
            employee=employee, instruction_type=i_type).exists()
        if not exists:
            status['missing_instructions'].append(i_type)

    # Б. Первичный/Повторный на рабочем месте
    # Нужен всем, КРОМЕ освобожденных (exempt_from_safety_instruction)
    if not employee.exempt_from_safety_instruction:
        repeat_types = InstructionType.objects.filter(
            category='SAFETY',
            frequency_months__gt=0
        )  # Ищем периодические

        for i_type in repeat_types:
            last_instr = Instruction.objects.filter(
                employee=employee,
                instruction_type=i_type
            ).order_by('-training_date').first()

            if not last_instr:
                status['missing_instructions'].append(i_type)
            elif last_instr.next_training_date and last_instr.next_training_date < today:
                status['expired_instructions'].append(i_type)

    return status
