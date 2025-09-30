from django import forms
from .models import MedicalCheck


class MedicalCheckForm(forms.ModelForm):
    class Meta:
        model = MedicalCheck
        fields = [
            'employee',
            'check_date',
            'next_check_date',
            'result',
            'is_valid'
        ]
        widgets = {
            'check_date': forms.DateInput(attrs={'type': 'date'}),
            'next_check_date': forms.DateInput(attrs={'type': 'date'}),
            'result': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].empty_label = "Выберите сотрудника"
        for field_name, field in self.fields.items():
            # Для чекбокса is_valid не будем добавлять класс form-control
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
