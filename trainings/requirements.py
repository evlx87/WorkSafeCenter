from employees.models import Employee
from trainings.models import TrainingProgram


def is_program_required_for_employee(
        employee: Employee,
        program: TrainingProgram) -> bool:
    """Определяет, требуется ли сотруднику данная программа обучения."""
    category_code = program.category.code if program.category else None

    # 1. Если программа обязательна для всех
    if program.is_mandatory:
        return True

    # 2. Проверка по целевым должностям
    if program.target_positions.exists():
        if employee.position and program.target_positions.filter(
                id=employee.position.id).exists():
            return True

    # 3. Проверка по категории и статусу сотрудника
    if category_code == 'SAFETY':
        if (employee.is_executive or employee.is_safety_committee_member or
                employee.is_safety_specialist):
            return True
        if not employee.exempt_from_safety_instruction:
            return True

    elif category_code == 'FIRE':
        if employee.is_executive or not employee.exempt_from_safety_instruction:
            return True

    elif category_code == 'FIRST_AID':
        if (employee.is_executive or employee.is_pedagogical or
                employee.is_safety_committee_member):
            return True

    elif category_code == 'ELECTRICAL':
        return True  # требуется всем

    # Для остальных категорий – если должность содержит ключевые слова
    # (можно расширить, но пока оставим общую логику)
    return False
