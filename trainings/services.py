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
    Улучшенная проверка сотрудника на соответствие требованиям по обучению
    """
    status = {
        'missing_programs': [],
        'missing_instructions': [],
        'expired_programs': [],
        'expired_instructions': [],
        'recommendations': [],
    }

    if employee.termination_date:
        return status

    today = timezone.now().date()
    programs = TrainingProgram.objects.all().select_related('category')

    # Проверка по каждой категории обучения
    category_checks = [
        ('SAFETY', 'Охрана труда', _check_safety_training),
        ('FIRE', 'Пожарная безопасность', _check_fire_training),
        ('FIRST_AID', 'Первая помощь', _check_first_aid_training),
        ('ELECTRICAL', 'Электробезопасность', _check_electrical_training),
    ]

    for category_code, category_name, check_func in category_checks:
        result = check_func(employee, programs, today)
        if result['missing']:
            status['missing_programs'].extend(result['missing'])
        if result['expired']:
            status['expired_programs'].extend(result['expired'])

    # Проверка инструктажей
    instruction_result = _check_instructions(employee, today)
    status['missing_instructions'] = instruction_result['missing']
    status['expired_instructions'] = instruction_result['expired']

    # Формирование рекомендаций
    if status['missing_programs'] or status['expired_programs']:
        status['recommendations'].append(
            f"Требуется обучение: {len(status['missing_programs']) + len(status['expired_programs'])} программ"
        )
    if status['missing_instructions'] or status['expired_instructions']:
        status['recommendations'].append(
            f"Требуется инструктаж: {len(status['missing_instructions']) + len(status['expired_instructions'])} видов"
        )

    return status


def _check_safety_training(employee, programs, today):
    """Проверка обучения по охране труда"""
    result = {'missing': [], 'expired': []}

    if employee.exempt_from_safety_instruction:
        return result

    program = programs.filter(
        category__code='SAFETY',
        name__icontains='охрана труда'
    ).first()

    if not program:
        return result

    last_training = Training.objects.filter(
        employee=employee,
        program=program
    ).order_by('-training_date').first()

    if not last_training:
        result['missing'].append(program)
    elif program.frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=program.frequency_months)
        if expiry < today:
            result['expired'].append(program)

    return result


def _check_fire_training(employee, programs, today):
    """Проверка обучения по пожарной безопасности"""
    result = {'missing': [], 'expired': []}

    program = programs.filter(
        category__code='FIRE',
        name__icontains='пожарная'
    ).first()

    if not program:
        return result

    # ПБ нужна руководителям и всем сотрудникам
    if not (employee.is_executive or not employee.exempt_from_safety_instruction):
        return result

    last_training = Training.objects.filter(
        employee=employee,
        program=program
    ).order_by('-training_date').first()

    if not last_training:
        result['missing'].append(program)
    elif program.frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=program.frequency_months)
        if expiry < today:
            result['expired'].append(program)

    return result


def _check_first_aid_training(employee, programs, today):
    """Проверка обучения по первой помощи"""
    result = {'missing': [], 'expired': []}

    # Первая помощь нужна руководителям, педагогам, членам комиссии
    if not (employee.is_executive or employee.is_pedagogical or employee.is_safety_committee_member):
        return result

    program = programs.filter(
        category__code='FIRST_AID',
        name__icontains='первая помощь'
    ).first()

    if not program:
        return result

    last_training = Training.objects.filter(
        employee=employee,
        program=program
    ).order_by('-training_date').first()

    if not last_training:
        result['missing'].append(program)
    elif program.frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=program.frequency_months)
        if expiry < today:
            result['expired'].append(program)

    return result


def _check_electrical_training(employee, programs, today):
    """Проверка обучения по электробезопасности"""
    result = {'missing': [], 'expired': []}

    # Электробезопасность нужна всем
    program = programs.filter(
        category__code='ELECTRICAL',
        name__icontains='электробезопасность'
    ).first()

    if not program:
        return result

    last_training = Training.objects.filter(
        employee=employee,
        program=program
    ).order_by('-training_date').first()

    if not last_training:
        result['missing'].append(program)
    elif program.frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=program.frequency_months)
        if expiry < today:
            result['expired'].append(program)

    return result


def _check_instructions(employee, today):
    """Проверка инструктажей"""
    result = {'missing': [], 'expired': []}

    # Вводные инструктажи
    intro_types = InstructionType.objects.filter(
        type_name__icontains='Вводный')
    for i_type in intro_types:
        exists = Instruction.objects.filter(
            employee=employee,
            instruction_type=i_type
        ).exists()
        if not exists:
            result['missing'].append(i_type)

    # Повторные инструктажи
    if not employee.exempt_from_safety_instruction:
        repeat_types = InstructionType.objects.filter(
            category__in=['SAFETY', 'FIRE'],
            frequency_months__gt=0
        )
        for i_type in repeat_types:
            last_instr = Instruction.objects.filter(
                employee=employee,
                instruction_type__category=i_type.category
            ).order_by('-training_date').first()

            if not last_instr:
                result['missing'].append(i_type)
            elif i_type.frequency_months > 0:
                expiry = last_instr.training_date + \
                    relativedelta(months=i_type.frequency_months)
                if expiry < today:
                    result['expired'].append(i_type)

    return result
