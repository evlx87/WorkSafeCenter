from django import forms

from .models import SafetyTraining


class SafetyTrainingForm(forms.ModelForm):
    class Meta:
        model = SafetyTraining
        fields = [
            'training_type',
            'training_date',
            'next_training_date',
            'instructor'
        ]
        widgets = {
            'training_date': forms.DateInput(attrs={'type': 'date'}),
            'next_training_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS-классы для стилизации, если потребуется
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
