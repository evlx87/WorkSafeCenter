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
    # Настройка queryset для ForeignKey и ManyToMany полей
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Получаем всех активных сотрудников для выбора
        employee_queryset = Employee.objects.all().order_by('last_name', 'first_name')

        # Настройка queryset для ForeignKey и ManyToMany полей
        if 'director' in self.fields:
            self.fields['director'].queryset = employee_queryset
        if 'safety_specialist' in self.fields:
            self.fields['safety_specialist'].queryset = employee_queryset
        if 'safety_committee_members' in self.fields:
            self.fields['safety_committee_members'].queryset = employee_queryset

        # Добавляем класс для стилизации
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = OrganizationSafetyInfo
        fields = [
            'name_full',
            'inn',
            'ogrn',
            'address_legal',
            'director',
            'director_position',
            'safety_specialist',
            'safety_committee_members',
            'contact_phone',
        ]

        widgets = {
            'safety_committee_members': forms.SelectMultiple(
                attrs={'size': 8, 'class': 'form-control'}
            ),
            'director_position': forms.TextInput(
                attrs={'placeholder': 'Например: Директор, И.О. Директора'}
            ),
        }


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            'name',
            'address',
            'ot_responsible_name']
