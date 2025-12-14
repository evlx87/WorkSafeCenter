from django import forms

from .models import SafetyTraining
from .models import Training, TrainingProgram


class TrainingProgramForm(forms.ModelForm):
    class Meta:
        model = TrainingProgram
        fields = ['name', 'training_type', 'is_mandatory', 'hours', 'frequency_months']


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

