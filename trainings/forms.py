from django import forms

from .models import Training, TrainingProgram


class TrainingProgramForm(forms.ModelForm):
    class Meta:
        model = TrainingProgram
        fields = ['name', 'hours', 'frequency_months']


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = [
            'program',
            'training_date',
            'document_scan'
        ]
        widgets = {
            'training_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['program'].empty_label = "Выберите программу обучения"
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
