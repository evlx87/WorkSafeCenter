from django import forms

from .models import Document


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
        self.fields['document_type'].widget.attrs.update(
            {'id': 'id_document_type'})
        self.fields['file'].widget.attrs.update({'id': 'id_file_field'})
        self.fields['external_link'].widget.attrs.update(
            {'id': 'id_external_link_field'})
        self.fields['employee'].widget.attrs.update(
            {'id': 'id_employee_field'})

    def clean(self):
        cleaned_data = super().clean()
        doc_type = cleaned_data.get('document_type')
        employee = cleaned_data.get('employee')

        if doc_type == 'DIPLOMA' and not employee:
            self.add_error(
                'employee',
                'Для диплома необходимо указать сотрудника')

        return cleaned_data
