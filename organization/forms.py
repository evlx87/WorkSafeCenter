from django import forms
from .models import Department, Position, OrganizationSafetyInfo, Site
from employees.models import Employee


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'head']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            head_positions = Position.objects.filter(
                name__icontains='руководитель')

            if head_positions.exists():
                self.fields['head'].queryset = Employee.objects.filter(
                    position__in=head_positions,
                    is_active=True
                )
            else:
                self.fields['head'].queryset = Employee.objects.filter(
                    is_active=True)
        except Exception:
            self.fields['head'].queryset = Employee.objects.none()


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'description', 'department']


class OrganizationSafetyInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        employee_queryset = Employee.objects.all().order_by('last_name', 'first_name')

        if 'director' in self.fields:
            self.fields['director'].queryset = employee_queryset
        if 'safety_specialist' in self.fields:
            self.fields['safety_specialist'].queryset = employee_queryset
        if 'safety_committee_members' in self.fields:
            self.fields['safety_committee_members'].queryset = employee_queryset

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
