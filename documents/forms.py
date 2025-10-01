from django import forms

from .models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'document_type', 'file', 'employee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Поле сотрудника не является обязательным
        self.fields['employee'].required = False
        self.fields['employee'].empty_label = "Без привязки к сотруднику"
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
