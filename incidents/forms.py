from django import forms
from .models import Incident


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'employee',
            'incident_type',
            'incident_date',
            'description',
            'actions_taken'
        ]
        widgets = {
            'incident_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'incident_type': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].empty_label = "Выберите сотрудника"
        self.fields['employee'].widget.attrs.update({'class': 'form-control'})
        self.fields['incident_date'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['actions_taken'].widget.attrs.update({'class': 'form-control'})
