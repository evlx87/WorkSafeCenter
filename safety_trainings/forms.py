from django import forms

from .models import SafetyTraining


class SafetyTrainingForm(forms.ModelForm):
    class Meta:
        model = SafetyTraining
        fields = [
            'category',
            'training_type',
            'training_date',
            'instructor',
            'local_act_details',
            'basis_document'
        ]
        widgets = {
            'training_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['basis_document'].empty_label = "Выберите документ (необязательно)"
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
