from django import forms
from .models import Department, Position, OrganizationSafetyInfo, Site
from employees.models import Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'head']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ищем должность руководителя в модели Position
        try:
            # Заменяем 'EmployeePosition' на 'Position'
            head_positions = Position.objects.filter(
                name__icontains='руководитель')

            if head_positions.exists():
                # Находим всех сотрудников, у которых одна из этих должностей
                self.fields['head'].queryset = Employee.objects.filter(
                    position__in=head_positions,
                    is_active=True
                )
            else:
                # Если такая должность не найдена, показываем всех активных
                # сотрудников
                self.fields['head'].queryset = Employee.objects.filter(
                    is_active=True)
        except Position.DoesNotExist:  # И здесь тоже заменяем
            # Этот блок может сработать, если модель Position еще не создана
            self.fields['head'].queryset = Employee.objects.none()


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'description', 'department']


class OrganizationSafetyInfoForm(forms.ModelForm):
    class Meta:
        model = OrganizationSafetyInfo
        fields = [
            'school_name',
            'director_name',
            'ot_specialist_name']


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            'name',
            'address',
            'ot_responsible_name']
