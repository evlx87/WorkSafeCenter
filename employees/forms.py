from django import forms

from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'last_name',
            'first_name',
            'middle_name',
            'position',
            'department',
            'workplace',
            'birth_date',
            'hire_date',
            'email',
            'phone',
            'is_executive',
            'on_parental_leave',
            'is_safety_committee_member',
            'termination_date',
            'termination_order_number']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'termination_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].empty_label = "Должность не выбрана"
        self.fields['department'].empty_label = "Отдел не выбран"
