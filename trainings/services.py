from dateutil.relativedelta import relativedelta
from django.utils import timezone

from employees.models import Employee
from .models import Training, Instruction, TrainingProgram, InstructionType, Internship


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
    programs = TrainingProgram.objects.all().select_related('category')

    # Проверка ТОЛЬКО по 4 основным категориям
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

    return status


def _is_worker_profession(employee: Employee) -> bool:
    """Проверяет, является ли профессия рабочей"""
    if not employee.position:
        return False

    worker_keywords = ['рабоч', 'рабочий', 'рабочая', 'оператор', 'водитель',
                       'машинист', 'слесар', 'электр', 'монт', 'строитель']

    position_name = employee.position.name.lower()
    return any(keyword in position_name for keyword in worker_keywords)


def _check_safety_training(employee, programs, today):
    """
    Проверка обучения по охране труда
    Постановление № 2464: не реже 1 раза в 3 года
    """
    result = {'missing': [], 'expired': []}

    if employee.exempt_from_safety_instruction:
        return result

    # Для руководителей и специалистов - 3 года
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
        result['missing'].append({
            'program': program,
            'reason': 'Отсутствует обучение по охране труда',
            'deadline': employee.hire_date + relativedelta(days=60) if employee.hire_date else today
        })
    elif program.frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=program.frequency_months)
        if expiry < today:
            result['expired'].append({
                'program': program,
                'reason': f'Истек срок обучения по охране труда (истек {expiry.strftime("%d.%m.%Y")})',
                'expired_date': expiry
            })
        elif expiry < today + relativedelta(days=90):
            # Предупреждение за 90 дней
            pass  # Можно добавить в warnings

    return result


def _check_fire_training(employee, programs, today):
    """
    Проверка обучения по пожарной безопасности
    Законы о ПБ (69-ФЗ, 123-ФЗ): противопожарный инструктаж и обучение
    """
    result = {'missing': [], 'expired': []}

    # ПБ требуется всем сотрудникам
    program = programs.filter(
        category__code='FIRE',
        name__icontains='пожарн'
    ).first()

    if not program:
        return result

    last_training = Training.objects.filter(
        employee=employee,
        program=program
    ).order_by('-training_date').first()

    if not last_training:
        result['missing'].append({
            'program': program,
            'reason': 'Отсутствует обучение по пожарной безопасности',
            'deadline': employee.hire_date + relativedelta(days=30) if employee.hire_date else today,
            'legal_basis': '69-ФЗ, 123-ФЗ'
        })
    elif program.frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=program.frequency_months)
        if expiry < today:
            result['expired'].append({
                'program': program,
                'reason': f'Истек срок обучения по пожарной безопасности (истек {expiry.strftime("%d.%m.%Y")})',
                'expired_date': expiry,
                'legal_basis': '69-ФЗ, 123-ФЗ'
            })

    return result


def _check_first_aid_training(employee, programs, today):
    """
    Проверка обучения по первой помощи
    Федеральный закон № 273-ФЗ: для педагогических работников - ежегодно
    Постановление № 2464: для руководителей и членов комиссии - 1 год
    """
    result = {'missing': [], 'expired': []}

    # Определяем, кому требуется первая помощь
    requires_first_aid = (
        employee.is_pedagogical or  # 273-ФЗ - педагоги
        employee.is_executive or  # 2464 - руководители
        employee.is_safety_committee_member  # 2464 - члены комиссии
    )

    if not requires_first_aid:
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

    # Для педагогов - 1 год (273-ФЗ)
    # Для остальных по программе (обычно 1-3 года)
    frequency_months = 12 if employee.is_pedagogical else program.frequency_months

    if not last_training:
        result['missing'].append({
            'program': program,
            'reason': 'Отсутствует обучение по первой помощи',
            'deadline': employee.hire_date + relativedelta(days=30) if employee.hire_date else today,
            'legal_basis': '273-ФЗ' if employee.is_pedagogical else 'Постановление № 2464'
        })
    elif frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=frequency_months)
        if expiry < today:
            result['expired'].append({
                'program': program,
                'reason': f'Истек срок обучения по первой помощи (истек {expiry.strftime("%d.%m.%Y")})',
                'expired_date': expiry,
                'legal_basis': '273-ФЗ' if employee.is_pedagogical else 'Постановление № 2464'
            })

    return result


def _check_electrical_training(employee, programs, today):
    """
    Проверка обучения по электробезопасности
    Приказ Минэнерго РФ от 12.08.2022 № 811
    """
    result = {'missing': [], 'expired': []}

    # Проверяем, требуется ли электробезопасность
    requires_electrical = _requires_electrical_safety(employee)

    if not requires_electrical:
        return result

    program = programs.filter(
        category__code='ELECTRICAL',
        name__icontains='электробезопасност'
    ).first()

    if not program:
        return result

    last_training = Training.objects.filter(
        employee=employee,
        program=program
    ).order_by('-training_date').first()

    # По Приказу 811:
    # - I группа - ежегодно
    # - II-V группа - ежегодно (проверка знаний)
    frequency_months = 12  # По умолчанию ежегодно

    if not last_training:
        result['missing'].append({
            'program': program,
            'reason': 'Отсутствует обучение по электробезопасности',
            'deadline': employee.hire_date + relativedelta(days=30) if employee.hire_date else today,
            'legal_basis': 'Приказ Минэнерго № 811'
        })
    elif frequency_months > 0:
        expiry = last_training.training_date + \
            relativedelta(months=frequency_months)
        if expiry < today:
            result['expired'].append({
                'program': program,
                'reason': f'Истек срок обучения по электробезопасности (истек {expiry.strftime("%d.%m.%Y")})',
                'expired_date': expiry,
                'legal_basis': 'Приказ Минэнерго № 811'
            })

    return result


def _requires_electrical_safety(employee: Employee) -> bool:
    """
    Определяет, требуется ли сотруднику обучение по электробезопасности
    согласно Приказу № 811
    """
    if not employee.position:
        return False

    # Ключевые слова для определения необходимости
    electrical_keywords = [
        'электр', 'энерг', 'напряж', 'установк', 'щит', 'кабель',
        'провод', 'освещ', 'оборудовани', 'монтаж', 'ремонт'
    ]

    position_name = employee.position.name.lower()

    # Проверяем должность
    if any(keyword in position_name for keyword in electrical_keywords):
        return True

    # Проверяем категорию сотрудника
    # По Приказу 811 - все работающие с электроустановками
    if employee.is_executive or employee.is_safety_specialist:
        return True

    return False


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
