from django import forms
from .models import Training


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = [
            'program_name', 'hours', 'training_date',
            'frequency_months', 'document_scan'
        ]
        widgets = {
            'training_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
