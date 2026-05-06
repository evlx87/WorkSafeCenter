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
        elif program.frequency_months > 0:
            expiry = last_training.training_date + relativedelta(months=program.frequency_months)
            if expiry < today:
                status['expired_programs'].append(
                    _make_program_item(program, f'Срок истёк {expiry.strftime("%d.%m.%Y")}')
                )

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

    Требования:
    - Все сотрудники: I группа (ежегодно)
    - Ответственные за электрохозяйство: IV группа (ежегодно)
    - Электротехнический персонал: II-V группа по должности
    - Группы присваиваются последовательно
    """
    result = {'missing': [], 'expired': []}

    # Определяем требуемую группу
    required_group, min_group = _get_required_electrical_group(employee)

    if not required_group:
        return result

    program = programs.filter(
        category__code='ELECTRICAL',
        name__icontains='электробезопасность'
    ).first()

    if not program:
        return result

    # Получаем все обучения по электробезопасности сотрудника
    electrical_trainings = Training.objects.filter(
        employee=employee,
        program__category__code='ELECTRICAL'
    ).order_by('-training_date')

    # Находим действующее обучение с максимальной группой
    current_training = None
    current_group = None
    current_group_level = 0

    for training in electrical_trainings:
        if training.electrical_safety_group:
            group_level = _get_group_level(training.electrical_safety_group)
            expiry = training.training_date + relativedelta(months=12)

            # Проверяем, действует ли ещё это обучение
            if expiry >= today:
                if group_level > current_group_level:
                    current_training = training
                    current_group = training.electrical_safety_group
                    current_group_level = group_level

    required_group_level = _get_group_level(required_group)
    min_group_level = _get_group_level(min_group) if min_group else 0

    # Проверка 1: Есть ли вообще обучение по электробезопасности
    if not current_training:
        result['missing'].append({
            'program': program,
            'reason': f'Отсутствует обучение по электробезопасности (требуется {required_group} группа)',
            'deadline': employee.hire_date + relativedelta(days=30) if employee.hire_date else today,
            'legal_basis': 'Приказ Минэнерго № 811',
            'required_group': required_group,
            'min_group': min_group
        })
        return result

    # Проверка 2: Не истёк ли срок действия
    expiry_date = current_training.training_date + relativedelta(months=12)
    if expiry_date < today:
        result['expired'].append({
            'program': program,
            'reason': f'Истек срок обучения по электробезопасности (истек {expiry_date.strftime("%d.%m.%Y")})',
            'expired_date': expiry_date,
            'legal_basis': 'Приказ Минэнерго № 811',
            'current_group': current_group,
            'required_group': required_group
        })
        return result

    # Проверка 3: Соответствует ли группа требованиям
    if current_group_level < min_group_level:
        result['missing'].append({
            'program': program,
            'reason': f'Недостаточная группа по электробезопасности (имеется {current_group}, требуется мин. {min_group})',
            'deadline': expiry_date - relativedelta(days=30),
            'legal_basis': 'Приказ Минэнерго № 811',
            'current_group': current_group,
            'required_group': required_group,
            'min_group': min_group
        })

    # Проверка 4: Предупреждение об истечении срока (за 30 дней)
    if expiry_date < today + relativedelta(days=30):
        result['expired'].append({
            'program': program,
            'reason': f'Срок обучения истекает {expiry_date.strftime("%d.%m.%Y")}',
            'expired_date': expiry_date,
            'legal_basis': 'Приказ Минэнерго № 811',
            'current_group': current_group,
            'warning': True
        })

    return result


def _get_required_electrical_group(employee):
    """
    Определяет требуемую и минимальную группу по электробезопасности

    Returns:
        tuple: (required_group, min_group) или (None, None) если не требуется
    """
    # Ответственный за электрохозяйство - IV группа (обязательно)
    if employee.is_electrical_responsible:
        return ('IV', 'IV')

    # Электротехнический персонал - по должности (II-V группа)
    if employee.is_electrical_personnel:
        # Можно расширить логику для определения конкретной группы по должности
        return ('III', 'II')  # По умолчанию III, мин. II

    # Все остальные сотрудники - I группа
    return ('I', 'I')


def _get_group_level(group):
    """
    Возвращает числовой уровень группы для сравнения
    I=1, II=2, III=3, IV=4, V=5
    """
    level_map = {
        'I': 1,
        'II': 2,
        'III': 3,
        'IV': 4,
        'V': 5
    }
    return level_map.get(group, 0)


def _requires_electrical_safety(employee: Employee) -> bool:
    """
    Определяет, требуется ли сотруднику обучение по электробезопасности
    """
    # Всегда требуется хотя бы I группа
    return True


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
