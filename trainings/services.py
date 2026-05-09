from dateutil.relativedelta import relativedelta
from django.utils import timezone

from employees.models import Employee
from .models import Training, Instruction, TrainingProgram, InstructionType, Internship
from .requirements import is_program_required_for_employee


def _get_required_programs(employee):
    """
    Возвращает список программ обучения, обязательных для данного сотрудника.
    Использует логику, аналогичную reports/views.py
    """
    all_programs = TrainingProgram.objects.filter(
        category__is_active=True
    ).select_related('category')
    required = []
    for program in all_programs:
        if is_program_required_for_employee(employee, program):
            required.append(program)
    return required


def _make_program_item(program, reason, deadline=None, expired_date=None):
    """
    Формирует словарь с информацией о проблеме обучающей программы для шаблона
    """
    return {
        'program': program,
        'reason': reason,
        'deadline': deadline,
        'expired_date': expired_date,
    }


def get_next_training_date(training_date, frequency_months):
    """Вычисляет дату следующего обучения."""
    if frequency_months > 0:
        return training_date + relativedelta(months=frequency_months)
    return None


def check_employee_compliance(employee: Employee):
    """
    Проверка сотрудника на соответствие требованиям по обучению
    Учитываются ТОЛЬКО 4 основные категории:
    - Охрана труда (Постановление № 2464)
    - Пожарная безопасность (69-ФЗ, 123-ФЗ)
    - Первая помощь (273-ФЗ, Постановление № 2464)
    - Электробезопасность (Приказ № 811)
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

    # 1. Проверка обязательных программ обучения
    required_programs = _get_required_programs(employee)
    for program in required_programs:
        last_training = Training.objects.filter(
            employee=employee, program=program
        ).order_by('-training_date').first()

        if not last_training:
            status['missing_programs'].append(
                _make_program_item(program, 'Обучение не пройдено')
            )
        elif last_training.next_training_date and last_training.next_training_date < today:
            status['expired_programs'].append(
                _make_program_item(
                    program, f'Срок истёк {
                        last_training.next_training_date.strftime("%d.%m.%Y")}'))

    # 2. Проверка инструктажей (оставляем старую реализацию, она работает)
    instruction_result = _check_instructions(employee, today)
    status['missing_instructions'] = instruction_result['missing']
    status['expired_instructions'] = instruction_result['expired']

    return status


def _is_worker_profession(employee: Employee) -> bool:
    """Проверяет, является ли профессия рабочей"""
    if not employee.position:
        return False

    worker_keywords = ['рабоч', 'рабочий', 'рабочая', 'оператор', 'водитель',
                       'машинист', 'слесар', 'электр', 'монт', 'строитель']

    position_name = employee.position.name.lower()
    return any(keyword in position_name for keyword in worker_keywords)


def _check_instructions(employee, today):
    """Проверка инструктажей"""
    result = {'missing': [], 'expired': []}

    # Вводный инструктаж (обязателен для всех в течение 60 дней)
    if employee.hire_date:
        days_since_hire = (today - employee.hire_date).days
        if days_since_hire <= 60:
            intro_types = InstructionType.objects.filter(
                type_name__icontains='Вводный'
            )
            for i_type in intro_types:
                exists = Instruction.objects.filter(
                    employee=employee,
                    instruction_type=i_type
                ).exists()
                if not exists:
                    result['missing'].append({
                        'type': i_type,
                        'reason': 'Не проведен вводный инструктаж',
                        'deadline': employee.hire_date + relativedelta(days=60),
                        'legal_basis': 'Постановление № 2464'
                    })

    # Повторные инструктажи
    if not employee.exempt_from_safety_instruction:
        repeat_types = InstructionType.objects.filter(
            category__in=['SAFETY', 'FIRE'],
            frequency_months__gt=0
        )
        for i_type in repeat_types:
            last_instr = Instruction.objects.filter(
                employee=employee,
                instruction_type=i_type
            ).order_by('-training_date').first()

            if not last_instr:
                result['missing'].append({
                    'type': i_type,
                    'reason': f'Не проведен {i_type.type_name} инструктаж',
                    'deadline': employee.hire_date + relativedelta(days=30) if employee.hire_date else today
                })
            elif i_type.frequency_months > 0:
                expiry = last_instr.training_date + \
                    relativedelta(months=i_type.frequency_months)
                if expiry < today:
                    result['expired'].append({
                        'type': i_type,
                        'reason': f'Просрочен {i_type.type_name} инструктаж',
                        'expired_date': expiry
                    })

    return result


def _check_internship(employee, today):
    """Проверка необходимости стажировки"""
    result = {'required': False, 'message': ''}

    if not employee.hire_date:
        return result

    days_since_hire = (today - employee.hire_date).days

    # Стажировка требуется для рабочих профессий в течение 90 дней
    if days_since_hire <= 90 and _is_worker_profession(employee):
        internship = Internship.objects.filter(
            employee=employee,
            is_completed=True
        ).exists()

        if not internship:
            result['required'] = True
            result['message'] = 'Требуется стажировка на рабочем месте'

    return result
