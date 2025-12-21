from django import forms
from .models import Document, Category

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'title',
            'document_type',
            'category',
            'file',
            'external_link',
            'end_date',
            'employee'
        ]
        widgets = {
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].widget.attrs.update({'id': 'id_document_type'})
        self.fields['file'].widget.attrs.update({'id': 'id_file_field'})
        self.fields['external_link'].widget.attrs.update({'id': 'id_external_link_field'})
        self.fields['employee'].widget.attrs.update({'id': 'id_employee_field'})